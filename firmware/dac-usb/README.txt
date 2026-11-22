USB-controlled Rust DAC tone for the Seeed XIAO SAMD21

The new firmware is in dist/dac-usb.bin (also .elf and .uf2).
The Linux x86_64 controller is ../../tools/tone-control/dist/tone-control.
Both are already built; no Rust installation is needed to use them.
The old fixed-tone firmware in ../dac-tone is preserved.

FLASH (from the amps repository root)

1. Keep USB connected and double-bridge the XIAO's two RST pads to enter
   its existing bootloader. Identify the bootloader port:
     ls -l /dev/serial/by-id/
2. Set the correct port, then flash and verify:
     BOOT_PORT=/dev/ttyACM0
     sudo firmware/dac-tone/tools/bossac --port="$BOOT_PORT" --offset=0x2000 \
       --write --verify --reset firmware/dac-usb/dist/dac-usb.bin
   Keep the 0x2000 offset: the first 8 KiB belongs to the USB bootloader.
   This changes the application; the existing bootloader remains available.
3. Wait a few seconds for USB enumeration, then look again:
     ls -l /dev/serial/by-id/
   Choose the application device containing XIAO_DAC_Tone / XIAO-DAC-001,
   not the bootloader device. Its ttyACM number may have changed.

CONTROL (from the amps repository root)

  PORT=/dev/ttyACM0
  tools/tone-control/dist/tone-control --port "$PORT" status
  tools/tone-control/dist/tone-control --port "$PORT" frequency 440
  tools/tone-control/dist/tone-control --port "$PORT" start
  tools/tone-control/dist/tone-control --port "$PORT" frequency 880
  tools/tone-control/dist/tone-control --port "$PORT" stop

Use the application port found above, or its full /dev/serial/by-id/... path.
If access is denied, prepend sudo to the controller command, or use your
host's serial-device group permissions. Close other serial monitors first;
use only one controller process at a time. No baud-rate setup is needed.
The Linux controller uses installed stty to configure the tty in raw mode.
It sends one request, waits up to 5 seconds for an acknowledgment, prints
that acknowledgment, and exits. Device errors/timeouts produce exit code 1.

Firmware boots STOPPED with pitch 440 Hz. Setting frequency preserves the
current running/stopped state. Closing the controller leaves the current
tone playing. Settings remain until reset/power loss; they are not saved
in flash. Acknowledgments include actual logical state, for example:
  OK running=1 freq=880 rate=32000

The serial wire protocol is newline-terminated ASCII:
  START
  STOP
  FREQ 440
  STATUS
Commands are case-insensitive. Frequencies must be integers 20..5000 Hz.
CRLF, fragmented USB packets and multiple commands per packet are supported.
Malformed/oversized requests get ERR responses and leave tone settings alone.

AUDIO

Output stays on D0/A0 (PA02). STOP holds the DAC at code 512 (about 1.65 V);
through an AC-coupling capacitor this is silence. START resets oscillator
phase. Output is a full-range 10-bit sine lookup table, about 3.3 Vpp when
unloaded. Keep the coupling capacitor and volume control before PAM8403
L/R inputs, share signal ground, and start with low amplifier volume.
There is no volume command or fade; abrupt start/stop can produce a click.

SysTick interrupts update the DAC at nominally 32,000 samples/s. A 32-bit
phase accumulator sets pitch independently of the USB polling loop, using
32 sine table positions. USB SOF clock recovery provides the 48 MHz core
clock; a separate 8 MHz generic clock drives the DAC. Main-loop USB work
uses short critical sections; this is a basic tone generator, not a
jitter-free or high-fidelity audio instrument. Scope-check actual output.

USB uses CDC ACM with the pid.codes private-testing VID/PID 1209:0001 and
serial XIAO-DAC-001. This ID is not unique/assigned to this project; do not
ship or redistribute hardware using it. For multiple boards, assign unique
serial numbers in src/main.rs. Firmware keeps polling USB while tone runs;
no bootloader reset is needed to change tone. Double-reset pads to reflash.

REBUILD (optional; ordinary host with network access for initial fetching)

  rustup target add thumbv6m-none-eabi
  sudo pacman -S --needed arm-none-eabi-binutils
  bash firmware/dac-usb/build.sh
  bash tools/tone-control/build.sh

Firmware uses atsamd-hal 0.16.0, cortex-m-rt, usb-device and usbd-serial.
Cargo.lock pins the dependency versions. The host controller and shared
protocol/synth crate need no external dependencies. Source is in:
  src/main.rs                         USB firmware and timer interrupt
  ../tone-protocol/src/lib.rs          parser, framing and oscillator
  ../../tools/tone-control/src/main.rs Linux serial controller

VALIDATION

  cargo test --manifest-path firmware/tone-protocol/Cargo.toml
  python3 tools/tone-control/test-control.py

Release builds completed for thumbv6m-none-eabi and Linux x86_64. Protocol
unit tests cover malformed commands, CRLF/fragmentation, overlong lines,
muting and phase stepping. Controller integration tests use Linux PTYs to
check actual command bytes, fragmented replies, error replies and timeout.
Application vectors, stack reservation, bootloader offset and UF2 packaging
were checked. Physical USB enumeration and DAC output remain unverified:
this agent session cannot access the host USB device nodes.

REFERENCES
https://github.com/atsamd-rs/atsamd/tree/54bed012d535ae3eb7be0e515e55447ef1267fee/boards/xiao_m0
https://wiki.seeedstudio.com/Seeeduino-XIAO/
https://pid.codes/1209/0001/
