from typing import List
from constants import MEMORY_SIZE


class Memory:
    memory: List[int]

    def __init__(self, size: int = MEMORY_SIZE):
        self.memory = [0] * size

    def read(self, addr: int) -> int:
        return self.memory[addr]

    def write(self, addr: int, data: int) -> None:
        self.memory[addr] = data

    def read_u16(self, pos: int) -> int:
        low = self.read(pos)
        hi = self.read(pos + 1)

        return hi << 8 | low

    def write_u16(self, pos: int, data: int) -> None:
        hi = data >> 8
        low = data & 0xFF
        self.write(pos, low)
        self.write(pos + 1, hi)
