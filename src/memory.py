from collections import UserList
from constants import MEMORY_SIZE


class Memory(UserList):
    def __init__(self, *args, **kwargs):
        super(Memory, self).__init__(*args, **kwargs)
        self.data = [0] * MEMORY_SIZE

    def read(self, addr: int) -> int:
        return self.data[addr]

    def write(self, addr: int, data: int) -> None:
        self.data[addr] = data

    def read_u16(self, pos: int) -> int:
        low = self.read(pos)
        hi = self.read(pos + 1)

        return hi << 8 | low

    def write_u16(self, pos: int, data: int) -> None:
        hi = data >> 8
        low = data & 0xFF
        self.write(pos, low)
        self.write(pos + 1, hi)

    def slice(self, start: int, end: int) -> list:
        return self.data[start:end]
