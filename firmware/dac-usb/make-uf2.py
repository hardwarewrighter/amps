"""Package the application for a SAMD21 UF2 bootloader; validate vectors."""
from pathlib import Path
import struct

image = Path("dist/dac-usb.bin").read_bytes()
base = 0x2000
sp, reset = struct.unpack_from("<II", image)
assert 0x20000000 < sp <= 0x20007FF8 and sp % 8 == 0
assert reset & 1 and base <= (reset & ~1) < base + len(image)
assert len(image) <= 256 * 1024 - base
blocks = (len(image) + 255) // 256
result = bytearray()
for i in range(blocks):
    payload = image[i * 256:(i + 1) * 256].ljust(256, b"\x00")
    result += struct.pack("<8I", 0x0A324655, 0x9E5D5157, 0x2000,
                          base + i * 256, 256, i, blocks, 0x68ED2B88)
    result += payload + bytes(220) + struct.pack("<I", 0x0AB16F30)
assert len(result) == blocks * 512
Path("dist/dac-usb.uf2").write_bytes(result)
print(f"Built {len(image)}-byte application at {base:#x}; "
      f"SP={sp:#x}, reset={reset:#x}; UF2: {blocks} blocks")
