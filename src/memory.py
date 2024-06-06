from typing import List
import numpy as np

# //  _______________ $10000  _______________
# // | PRG-ROM       |       |               |
# // | Upper Bank    |       |               |
# // |_ _ _ _ _ _ _ _| $C000 | PRG-ROM       |
# // | PRG-ROM       |       |               |
# // | Lower Bank    |       |               |
# // |_______________| $8000 |_______________|
# // | SRAM          |       | SRAM          |
# // |_______________| $6000 |_______________|
# // | Expansion ROM |       | Expansion ROM |
# // |_______________| $4020 |_______________|
# // | I/O Registers |       |               |
# // |_ _ _ _ _ _ _ _| $4000 |               |
# // | Mirrors       |       | I/O Registers |
# // | $2000-$2007   |       |               |
# // |_ _ _ _ _ _ _ _| $2008 |               |
# // | I/O Registers |       |               |
# // |_______________| $2000 |_______________|
# // | Mirrors       |       |               |
# // | $0000-$07FF   |       |               |
# // |_ _ _ _ _ _ _ _| $0800 |               |
# // | RAM           |       | RAM           |
# // |_ _ _ _ _ _ _ _| $0200 |               |
# // | Stack         |       |               |
# // |_ _ _ _ _ _ _ _| $0100 |               |
# // | Zero Page     |       |               |
# // |_______________| $0000 |_______________|

RAM: int = 0x0000
RAM_MIRRORS_END: int = 0x1FFF
PPU_REGISTERS: int = 0x2000
PPU_REGISTERS_MIRRORS_END: int = 0x3FFF
MEMORY_SIZE: int = 0xFFFF


class Memory:
    def __init__(self, has_bus: bool = False, *args, **kwargs):
        super(Memory, self).__init__(*args, **kwargs)

        self.has_bus = has_bus

        if not self.has_bus:
            self.data = np.zeros(MEMORY_SIZE, dtype=np.uint8)
            self.cpu_vram = np.zeros(0x800, dtype=np.uint8)
        else:
            self.data = np.array([], dtype=np.uint8)
            self.cpu_vram = np.zeros(0x800, dtype=np.uint8)

    def read(self, addr: np.uint16) -> np.uint16:
        if not self.has_bus:
            return self.data[addr]

        match addr:
            case _ if addr >= RAM and addr <= RAM_MIRRORS_END:
                return self.cpu_vram[addr & 0b00000111_11111111]
            case _ if addr >= PPU_REGISTERS and addr <= PPU_REGISTERS_MIRRORS_END:
                raise ValueError(f"Not implemented for PPU: address {addr}")
            case _:
                raise ValueError(f"Not implemented for address {addr}")

    def write(self, addr: np.uint16, data: np.uint8) -> None:
        if not self.has_bus:
            self.data[addr] = np.uint8(data)
            return

        match addr:
            case _ if addr >= RAM and addr <= RAM_MIRRORS_END:
                self.cpu_vram[addr & 0b11111111111] = np.uint8(data)
            case _ if addr >= PPU_REGISTERS and addr <= PPU_REGISTERS_MIRRORS_END:
                raise ValueError(f"Not implemented for PPU: address {addr}")
            case _:
                raise ValueError(f"Not implemented for address {addr}")

    def read_u16(self, pos: np.uint16) -> np.uint16:
        low = self.read(pos)
        hi = self.read(pos + 1)

        return hi << 8 | low

    def write_u16(self, pos: int, data: int) -> None:
        hi = data >> 8
        low = data & 0xFF
        self.write(pos, low)
        self.write(pos + 1, hi)

    def slice(self, start: int, end: int) -> list:
        return [self.read(x) for x in range(start, end)]

    def load(self, start: int, end: int, data: List[int]) -> None:
        for i in range(start, end):
            self.write(i, data[i - start])
