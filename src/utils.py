from typing import List

HEX_16 = 0xFFFF
HEX_8 = 0xFF

MEMORY_SIZE = 0xFFFF
PROGRAM_ROM_START = 0x8000
PROGRAM_ROM_END = 0xFFFF
CHARACTER_ROM_START = 0x0000
CHARACTER_ROM_END = 0x1FFF


def endianify(bytes_: List[int]) -> int:
    if len(bytes_) == 1:
        return bytes_[0]

    elif len(bytes_) == 2:
        lo = bytes_[0]
        hi = bytes_[1]
        hi = hi << 8
        return hi | lo
    else:
        # no command should have more than 2 bytes for a 6502 processor
        raise ValueError("Unsupported number of bytes")
