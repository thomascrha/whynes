from typing import Optional, Tuple
from cartridge import Cartridge
from constants import CHARACTER_ROM_END, CHARACTER_ROM_START, PROGRAM_ROM_END, PROGRAM_ROM_START
from instructions import AddressingModes, Instruction
from utils import get_bytes_ordered


class Memory:
    memory: bytearray
    program_rom: bytearray
    character_rom: bytearray
    cartridge: Optional[Cartridge]

    def __init__(self):
        self.memory = bytearray([0] * 0xFFFF)
        self.cartridge = None

        self.program_rom = self.memory[PROGRAM_ROM_START:PROGRAM_ROM_END]
        self.character_rom = self.memory[CHARACTER_ROM_START:CHARACTER_ROM_END]

    def load_bytes(self, program_rom: bytearray, character_rom: Optional[bytearray] = None):
        self.program_rom = program_rom
        if character_rom is not None:
            self.character_rom = character_rom

    def load_cartridge(self, cartridge: Cartridge):
        self.cartridge = cartridge
        self.load_bytes(program_rom=cartridge.program_rom, character_rom=cartridge.character_rom)

    def set_memory(self, address: int, value: int) -> None:
        self.memory[address] = value

    def get_memory_value(self, instruction: Instruction, cpu: "CPU") -> Tuple[int, int]:
        # -> Value,        Address if fetched from memory
        match (instruction.addressing_mode):
            case AddressingModes.IMPLIED:
                return 0, 0

            case AddressingModes.ACCUMULATOR:
                return cpu.a, 0

            case AddressingModes.IMMEDIATE:
                argument_bytes = self.program_rom[cpu.program_counter + 1 : cpu.program_counter + instruction.no_bytes]
                return get_bytes_ordered(argument_bytes), None

            case AddressingModes.ABSOLUTE:
                argument_bytes = self.program_rom[cpu.program_counter + 1 : cpu.program_counter + instruction.no_bytes]
                memory_address = get_bytes_ordered(argument_bytes)
                return self.memory[memory_address], memory_address

            case AddressingModes.X_INDEXED_ABSOLUTE:
                argument_bytes = self.program_rom[cpu.program_counter + 1 : cpu.program_counter + instruction.no_bytes]
                operand = get_bytes_ordered(argument_bytes)

                return self.memory[(operand + cpu.x)], operand + cpu.x

            case AddressingModes.Y_INDEXED_ABSOLUTE:
                argument_bytes = self.program_rom[cpu.program_counter + 1 : self.program_counter + instruction.no_bytes]
                operand = get_bytes_ordered(argument_bytes)

                return self.memory[(operand + cpu.y)], operand + cpu.y

            case AddressingModes.ABSOLUTE_INDIRECT:
                argument_bytes = self.program_rom[cpu.program_counter + 1 : cpu.program_counter + instruction.no_bytes]
                operand = get_bytes_ordered(argument_bytes)

                return self.memory[self.memory[operand]], self.memory[operand]

            case AddressingModes.ZERO_PAGE:
                argument_bytes = self.program_rom[cpu.program_counter + 1 : cpu.program_counter + instruction.no_bytes]
                operand = get_bytes_ordered(argument_bytes)

                return self.memory[operand], operand

            case AddressingModes.X_INDEXED_ZERO_PAGE:
                argument_bytes = self.program_rom[cpu.program_counter + 1 : cpu.program_counter + instruction.no_bytes]
                operand = get_bytes_ordered(argument_bytes)

                return self.memory[operand + cpu.x], operand + cpu.x

            case AddressingModes.Y_INDEXED_ZERO_PAGE:
                argument_bytes = self.program_rom[cpu.program_counter + 1 : cpu.program_counter + instruction.no_bytes]
                operand = get_bytes_ordered(argument_bytes)

                return self.memory[operand + cpu.y], operand + cpu.y

            case AddressingModes.X_INDEXED_ZERO_PAGE_INDIRECT:
                argument_bytes = self.program_rom[cpu.program_counter + 1 : cpu.program_counter + instruction.no_bytes]
                operand = get_bytes_ordered(argument_bytes)

                return self.memory[self.memory[operand + cpu.x]], self.memory[operand + cpu.x]

            case AddressingModes.ZERO_PAGE_INDIRECT_Y_INDEXED:
                argument_bytes = self.program_rom[cpu.program_counter + 1 : cpu.program_counter + instruction.no_bytes]
                operand = get_bytes_ordered(argument_bytes)

                return self.memory[self.memory[operand] + cpu.y], self.memory[operand] + cpu.y

            case AddressingModes.RELATIVE:
                argument_bytes = self.program_rom[cpu.program_counter + 1 : cpu.program_counter + instruction.no_bytes]
                operand = get_bytes_ordered(argument_bytes)

                return operand, None

            case _:
                logger.error(f"#FUCK {opcode.addressing_mode}")
                raise SystemError
