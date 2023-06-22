from cartrige import Cartridge


class Memory:
    def __init__(self):
        self.memory = [0] * 0xFFFF
        self.program_rom = self.memory[0x8000:0xFFFF]
        self.character_rom = self.memory[0x0000:0x2000]

    def setup(self, cartridge: Cartridge):
        self.cartridge = cartridge
        self.program_rom = self.cartridge.program_rom
        self.character_rom = self.cartridge.character_rom

    def read(self, address: int) -> int:
        return self.memory[address]

    def write(self, address: int, value: int):
        self.memory[address] = value
