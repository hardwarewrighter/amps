#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec sudo "$repo_root/firmware/dac-tone/tools/bossac" \
  --port=/dev/ttyACM1 --offset=0x2000 --write --verify --reset \
  "$repo_root/firmware/dac-usb/dist/dac-usb.bin"
