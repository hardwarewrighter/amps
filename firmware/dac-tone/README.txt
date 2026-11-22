XIAO SAMD21 DAC sine tone

Adapted from the Rust example appended to docs/research2.txt. This version
uses direct peripheral registers, a small Cortex-M0+ startup routine, and
a precomputed 32-sample sine table, so Cargo needs no external crates.
The processor and DAC use the calibrated internal 8 MHz oscillator.
It writes 10-bit samples with 70 us SysTick delays. Ideal delay-only pitch
is 446.4 Hz; loop overhead and oscillator tolerance lower/change it.
This is a tone test, not a calibrated 440 Hz reference.

Output: D0/A0 (PA02), approximately 0-3.3 V, 1.65 V DC offset, unloaded.
Connect through a 1-10 uF nonpolar coupling capacitor and a volume control
to the PAM8403 L/R line inputs; connect grounds. Start at low volume.
Do not connect a speaker directly to A0. Keep PAM8403 speaker outputs
separate from signal ground (they are bridge outputs).

Build on a normal host:
  rustup target add thumbv6m-none-eabi
  sudo pacman -S --needed arm-none-eabi-binutils
  bash build.sh

The already-built dist/dac-tone.bin can be flashed without Rust installed.
The linker reserves the first 8 KiB of flash for the existing bootloader
and the top 8 bytes of SRAM for the bootloader's reset marker.

Flash using the included tools/bossac (BOSSA 1.9.1, built for this Linux x86_64 host):
1. Connect USB. Briefly short the board's RESET and GND pads twice in
   quick succession to enter the bootloader. Do not short power pins.
2. Identify its bootloader port:
     ls -l /dev/serial/by-id/
3. Set PORT to that XIAO bootloader device (port can change after reset):
     PORT=/dev/ttyACM0
4. Flash, verify, and restart:
     ./tools/bossac --port="$PORT" --offset=0x2000 --write --verify --reset dist/dac-tone.bin
   If access is denied, run the same bossac command with sudo.
   This replaces the application; keep the offset exactly as shown.

If the bootloader exposes an XIAO removable drive, an alternative is to
copy dist/dac-tone.uf2 onto that mounted drive. Copy the UF2, not the BIN.

The application does not implement USB serial. The serial port disappears
while the tone runs; double-reset again to return to the USB bootloader.

Validation: release build, ELF sections, Cortex-M0+ disassembly, reset/stack
vectors, application offset and UF2 block layout checked. Not flashed or
measured on the board in this session because hardware access is restricted.

References:
https://wiki.seeedstudio.com/Seeeduino-XIAO/
https://docs.zephyrproject.org/latest/boards/seeed/seeeduino_xiao/doc/index.html
https://learn.adafruit.com/adafruit-qt-py/uf2-bootloader-details

BOSSA tool provenance:
  Source: https://github.com/shumatech/BOSSA/tree/1.9.1
  Built with: make -j4 VERSION=1.9.1 bin/bossac
  License: tools/BOSSA-LICENSE
  The CLI binary was built locally and its --help output checked.
  No pacman bossa package is required.
