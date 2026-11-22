#![no_std]
#![no_main]

// Adapted from docs/research2.txt: 32-point, 10-bit sine, 70 us delay.
// XIAO SAMD21G18A, D0/A0 = PA02, DAC peripheral function B.
use core::{
    arch::{asm, global_asm},
    ptr::{read_volatile, write_volatile},
};

// Cortex-M0+ startup and vector table; no external runtime is needed.
global_asm!(
    r#"
.syntax unified
.cpu cortex-m0plus
.thumb
.section .vector_table,"a",%progbits
.word _stack_top
.word Reset
.rept 46
.word DefaultHandler
.endr
.section .text.Reset,"ax",%progbits
.global Reset
.type Reset,%function
.thumb_func
Reset:
    cpsid i
    ldr r0, =_sidata
    ldr r1, =_sdata
    ldr r2, =_edata
1:
    cmp r1, r2
    bhs 2f
    ldr r3, [r0]
    str r3, [r1]
    adds r0, #4
    adds r1, #4
    b 1b
2:
    ldr r1, =_sbss
    ldr r2, =_ebss
    movs r3, #0
3:
    cmp r1, r2
    bhs 4f
    str r3, [r1]
    adds r1, #4
    b 3b
4:
    bl main
    b .
.global DefaultHandler
.type DefaultHandler,%function
.thumb_func
DefaultHandler:
    b .
"#
);

const PM: usize = 0x40000400;
const SYSCTRL: usize = 0x40000800;
const GCLK: usize = 0x40000c00;
const PORT: usize = 0x41004400;
const DAC: usize = 0x42004800;
const SYST: usize = 0xe000e010;
const SAMPLE_DELAY_US: u32 = 70;
// floor((sin(i * 2*pi/32) + 1) * 511.5), calculated at build preparation.
const WAVE: [u16; 32] = [
    511, 611, 707, 795, 873, 936, 984, 1013, 1023, 1013, 984, 936, 873, 795, 707, 611, 511, 411,
    315, 227, 149, 86, 38, 9, 0, 9, 38, 86, 149, 227, 315, 411,
];

// Safety: all accesses below target documented SAMD21 peripheral registers,
// with their specified access widths. Only this single-threaded firmware uses them.
unsafe fn r8(a: usize) -> u8 {
    read_volatile(a as *const u8)
}
unsafe fn w8(a: usize, v: u8) {
    write_volatile(a as *mut u8, v);
}
unsafe fn w16(a: usize, v: u16) {
    write_volatile(a as *mut u16, v);
}
unsafe fn r32(a: usize) -> u32 {
    read_volatile(a as *const u32)
}
unsafe fn w32(a: usize, v: u32) {
    write_volatile(a as *mut u32, v);
}
unsafe fn clock_sync() {
    while r8(GCLK + 1) & 0x80 != 0 {}
}
unsafe fn dac_sync() {
    while r8(DAC + 7) & 0x80 != 0 {}
}

#[no_mangle]
pub unsafe extern "C" fn main() -> ! {
    // Enable OSC8M, preserve factory calibration, select /1, clear ONDEMAND.
    w32(SYSCTRL + 0x20, (r32(SYSCTRL + 0x20) & !0x380) | 2);
    while r32(SYSCTRL + 0x0c) & (1 << 3) == 0 {}
    w32(PM + 0x18, r32(PM + 0x18) | (1 << 3)); // GCLK bus clock
    w32(GCLK + 8, 1 << 8); // GCLK0 divider = 1
    clock_sync();
    w32(GCLK + 4, (6 << 8) | (1 << 16)); // GCLK0 = OSC8M, enabled
    clock_sync();
    for offset in 8..12 {
        w8(PM + offset, 0);
    } // CPU/APB clocks /1
    w32(0xe000ed08, 0x2000); // application vector table
    asm!("dsb", "isb", options(nostack, preserves_flags));

    // Route the 8 MHz generic clock to the DAC (peripheral ID 33).
    w32(PM + 0x20, r32(PM + 0x20) | (1 << 18));
    w16(GCLK + 2, 33 | (1 << 14));
    clock_sync();
    // PA02 peripheral B, input/pull resistors off, analog output on.
    w8(PORT + 0x31, (r8(PORT + 0x31) & 0xf0) | 1);
    w8(PORT + 0x42, 1);
    w8(DAC, 1); // SWRST
    while r8(DAC) & 1 != 0 || r8(DAC + 7) & 0x80 != 0 {}
    w8(DAC + 1, (1 << 6) | 1); // AVCC reference, external output enable
    w8(DAC, 2); // ENABLE
    dac_sync();

    loop {
        for &sample in &WAVE {
            dac_sync();
            w16(DAC + 8, sample);
            // SysTick at 8 MHz; polling only, no interrupt.
            w32(SYST, 0);
            w32(SYST + 4, SAMPLE_DELAY_US * 8 - 1);
            w32(SYST + 8, 0);
            w32(SYST, 5);
            while r32(SYST) & (1 << 16) == 0 {}
        }
    }
}

#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! {
    loop {
        core::hint::spin_loop();
    }
}
