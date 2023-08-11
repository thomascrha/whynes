from typing import List, Optional
from cartridge import Cartridge


class Memory:
    memory: List[int]
    program_rom: List[int]
    cartridge: Optional[Cartridge]

    def __init__(self, address_space: int = 0xFFFF) -> None:
        self.address_space = address_space
        self.memory = [0] * self.address_space
        self.cartridge = None
        self.program_rom_offset = 0x0600

    def __getitem__(self, key: int) -> int:
        return self.memory[key]

    def __setitem__(self, key: int, value: int) -> None:
        self.memory[key] = value

    def load_program_rom(self, program_rom: List[int], program_rom_offset: int = 0x0600):
        for inx, value in enumerate(program_rom):
            self.memory[program_rom_offset + inx] = value

            self.program_rom = self.memory[program_rom_offset : self.address_space]

    # def load_cartridge(self, cartridge: Cartridge) -> None:
    #     self.cartridge = cartridge
    #     self.load_bytes(program_rom=cartridge.program_rom, character_rom=cartridge.character_rom)

    def get_memory(self, address: int) -> int:
        return self.memory[address]

    def set_memory(self, address: int, value: int) -> None:
        self.memory[address] = value

    def get_memory_slice(self, start: int, end: int) -> List[int]:
        return self.memory[start:end]
