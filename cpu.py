from cartrige import Cartridge
from instructions import Instructions
from logger import get_logger

logger = get_logger(__name__)


class CPU:
    program_counter: int
    stack_pointer: int
    accumulator: int
    index_x: int
    index_y: int
    status: int

    def __init__(self, cartridge: Cartridge):
        self.cartridge = cartridge
        self.reset()

    def reset(self):
        self.program_counter = 0x0000
        self.stack_pointer = 0x00
        self.accumulator = 0x00
        self.index_x = 0x00
        self.index_y = 0x00
        self.status = 0x00

    def compute_program_counter(self, opcode: Instructions.Opcodes) -> int:
        return self.program_counter + opcode.value.argument_length + 1

    def decompile_program(self):
        while self.program_counter < self.cartridge.prg_rom_size:
            opcode_hex = self.cartridge.prg_rom[self.program_counter]
            opcode = Instructions.get_opcode(opcode_hex)
            operand = None
            if opcode.value.argument_length > 0:
                operand = hex(self.cartridge.prg_rom[self.program_counter + opcode.value.argument_length])

            self.program_counter = self.compute_program_counter(opcode)
            logger.info(f"{opcode.name} ({operand if operand else ''}) :: {opcode.value.argument_length}")
