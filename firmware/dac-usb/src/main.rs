#![no_std]
#![no_main]

use atsamd_hal::{
    clock::{ClockGenId, ClockSource, GenericClockController},
    gpio, pac,
    usb::UsbBus,
};
use core::{
    cell::RefCell,
    fmt::{self, Write},
    ptr::{read_volatile, write_volatile},
};
use cortex_m::{
    interrupt::{self, Mutex},
    peripheral::syst::SystClkSource,
};
use cortex_m_rt::{entry, exception};
use panic_halt as _;
use tone_protocol::{Lines, Synth, SAMPLE_RATE};
use usb_device::{bus::UsbBusAllocator, prelude::*};
use usbd_serial::{SerialPort, USB_CLASS_CDC};

static AUDIO: Mutex<RefCell<Synth>> = Mutex::new(RefCell::new(Synth::new()));

struct Reply {
    bytes: [u8; 128],
    len: usize,
    sent: usize,
}
impl Reply {
    fn new() -> Self {
        Self {
            bytes: [0; 128],
            len: 0,
            sent: 0,
        }
    }
    fn clear(&mut self) {
        self.len = 0;
        self.sent = 0;
    }
}
impl Write for Reply {
    fn write_str(&mut self, s: &str) -> fmt::Result {
        if self.len + s.len() > self.bytes.len() {
            return Err(fmt::Error);
        }
        self.bytes[self.len..self.len + s.len()].copy_from_slice(s.as_bytes());
        self.len += s.len();
        Ok(())
    }
}

#[entry]
fn main() -> ! {
    let mut p = pac::Peripherals::take().unwrap();
    let mut core = cortex_m::Peripherals::take().unwrap();
    // HAL uses DFLL48M with USB SOF clock recovery for USB timing.
    let mut clocks = GenericClockController::with_internal_32kosc(
        p.GCLK,
        &mut p.PM,
        &mut p.SYSCTRL,
        &mut p.NVMCTRL,
    );
    let pins = gpio::Pins::new(p.PORT);
    let _dac_pin = pins.pa02.into_alternate::<gpio::B>();
    let dac_gclk = clocks
        .configure_gclk_divider_and_source(ClockGenId::GCLK2, 6, ClockSource::DFLL48M, false)
        .unwrap();
    let _dac_clock = clocks.dac(&dac_gclk).unwrap(); // DAC clock = 8 MHz
    p.PM.apbcmask.modify(|_, w| w.dac_().set_bit());
    let dac = p.DAC;
    dac.ctrla.write(|w| w.swrst().set_bit());
    while dac.ctrla.read().swrst().bit_is_set() || dac.status.read().syncbusy().bit_is_set() {}
    dac.ctrlb.write(|w| w.refsel().avcc().eoen().set_bit());
    dac.ctrla.write(|w| w.enable().set_bit());
    while dac.status.read().syncbusy().bit_is_set() {}
    dac.data.write(|w| unsafe { w.data().bits(512) });
    while dac.status.read().syncbusy().bit_is_set() {}

    let gclk0 = clocks.gclk0();
    let usb_clock = clocks.usb(&gclk0).unwrap();
    let bus = UsbBusAllocator::new(UsbBus::new(
        &usb_clock, &mut p.PM, pins.pa24, pins.pa25, p.USB,
    ));
    let mut serial = SerialPort::new(&bus);
    // pid.codes test VID/PID: local development, not an assigned product ID.
    let mut usb = UsbDeviceBuilder::new(&bus, UsbVidPid(0x1209, 0x0001))
        .manufacturer("hardwarewrighter")
        .product("XIAO DAC Tone")
        .serial_number("XIAO-DAC-001")
        .device_class(USB_CLASS_CDC)
        .build();

    core.SYST.set_clock_source(SystClkSource::Core);
    core.SYST.set_reload(48_000_000 / SAMPLE_RATE - 1);
    core.SYST.clear_current();
    core.SYST.enable_interrupt();
    core.SYST.enable_counter();
    unsafe {
        interrupt::enable();
    }

    let mut lines = Lines::new();
    let mut reply = Reply::new();
    let mut packet = [0u8; 64];
    let mut cursor = 0;
    let mut count = 0;
    let mut was_configured = false;
    loop {
        usb.poll(&mut [&mut serial]);
        let configured = usb.state() == UsbDeviceState::Configured;
        if !configured {
            // Retain tone settings, discard partial protocol data on USB reset.
            if was_configured {
                lines = Lines::new();
                reply.clear();
                cursor = 0;
                count = 0;
            }
            was_configured = false;
            continue;
        }
        was_configured = true;
        let _ = serial.flush();
        if reply.sent < reply.len {
            if let Ok(n) = serial.write(&reply.bytes[reply.sent..reply.len]) {
                reply.sent += n;
            }
            continue;
        }
        if cursor == count {
            match serial.read(&mut packet) {
                Ok(n) if n > 0 => {
                    cursor = 0;
                    count = n;
                }
                _ => continue,
            }
        }
        // Send each reply before parsing the next line, including when several
        // commands arrive in one USB packet. Handle partial writes without loss.
        while cursor < count {
            let byte = packet[cursor];
            cursor += 1;
            if let Some(command) = lines.push(byte) {
                reply.clear();
                match command {
                    Ok(command) => {
                        let (running, hz) = interrupt::free(|cs| {
                            let mut audio = AUDIO.borrow(cs).borrow_mut();
                            audio.apply(command);
                            (audio.running, audio.hz)
                        });
                        let _ = writeln!(
                            reply,
                            "OK running={} freq={} rate={}",
                            u8::from(running),
                            hz,
                            SAMPLE_RATE
                        );
                    }
                    Err(message) => {
                        let _ = reply.write_str(message);
                    }
                }
                break;
            }
        }
    }
}

#[exception]
fn SysTick() {
    // This ISR is the only DAC DATA writer after initialization. No wait loops.
    let sample = interrupt::free(|cs| AUDIO.borrow(cs).borrow_mut().sample());
    unsafe {
        if read_volatile(0x4200_4807 as *const u8) & 0x80 == 0 {
            write_volatile(0x4200_4808 as *mut u16, sample);
        }
    }
}
