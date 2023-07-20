from typing import List, Optional
from cartrige import Cartridge


class Memory:
    def __init__(self):
        self.memory: List[int] = [0] * 0xFFFF
        self.cartridge: Cartridge = None
        self.program_rom: List[int] = None
        self.character_rom: List[int] = None

    def load_bytes(self, program_rom: bytearray, character_rom: Optional[bytearray] = None):
        self.program_rom = program_rom
        self.character_rom = character_rom

    def load_cartridge(self, cartridge: Cartridge):
        self.cartridge = cartridge
        self.load_bytes(program_rom=cartridge.program_rom, character_rom=cartridge.character_rom)
