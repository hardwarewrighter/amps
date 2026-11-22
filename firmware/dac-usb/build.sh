#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
cargo build --release --locked
mkdir -p dist
arm-none-eabi-objcopy -O binary target/thumbv6m-none-eabi/release/dac-usb dist/dac-usb.bin
cp target/thumbv6m-none-eabi/release/dac-usb dist/dac-usb.elf
python3 make-uf2.py
