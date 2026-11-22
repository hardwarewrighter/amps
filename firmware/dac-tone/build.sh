#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
cargo build --offline --release
mkdir -p dist
arm-none-eabi-objcopy -O binary target/thumbv6m-none-eabi/release/dac-tone dist/dac-tone.bin
cp target/thumbv6m-none-eabi/release/dac-tone dist/dac-tone.elf
python3 make-uf2.py
