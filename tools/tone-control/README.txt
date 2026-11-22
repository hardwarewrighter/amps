Rust USB serial controller for firmware/dac-usb.

From the repository root:
  PORT=/dev/ttyACM0
  tools/tone-control/dist/tone-control --port "$PORT" status
  tools/tone-control/dist/tone-control --port "$PORT" frequency 440
  tools/tone-control/dist/tone-control --port "$PORT" start
  tools/tone-control/dist/tone-control --port "$PORT" stop

Full flashing, wiring and protocol instructions: ../../firmware/dac-usb/README.txt

Linux only; uses stty and nonblocking tty I/O, no external Rust crates.
Build: bash tools/tone-control/build.sh
Test: python3 tools/tone-control/test-control.py
