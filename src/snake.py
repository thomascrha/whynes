import random
from typing import List
from constants import Flags
from cpu import CPU
from logger import get_logger


class SnakeGame:
    # fmt: off
    CODE: List[int] = [
        0x20, 0x06, 0x06,
        0x20, 0x38, 0x06,
        0x20, 0x0d, 0x06,
        0x20, 0x2a, 0x06,
        0x60,
        0xa9, 0x02,
        0x85, 0x02,
        0xa9, 0x04,
        0x85, 0x03,
        0xa9, 0x11,
        0x85, 0x10,
        0xa9, 0x10, 0x85, 0x12, 0xa9, 0x0f, 0x85,
        0x14, 0xa9, 0x04, 0x85, 0x11, 0x85, 0x13, 0x85, 0x15, 0x60, 0xa5, 0xfe, 0x85, 0x00, 0xa5, 0xfe,
        0x29, 0x03, 0x18, 0x69, 0x02, 0x85, 0x01, 0x60, 0x20, 0x4d, 0x06, 0x20, 0x8d, 0x06, 0x20, 0xc3,
        0x06, 0x20, 0x19, 0x07, 0x20, 0x20, 0x07, 0x20, 0x2d, 0x07, 0x4c, 0x38, 0x06, 0xa5, 0xff, 0xc9,
        0x77, 0xf0, 0x0d, 0xc9, 0x64, 0xf0, 0x14, 0xc9, 0x73, 0xf0, 0x1b, 0xc9, 0x61, 0xf0, 0x22, 0x60,
        0xa9, 0x04, 0x24, 0x02, 0xd0, 0x26, 0xa9, 0x01, 0x85, 0x02, 0x60, 0xa9, 0x08, 0x24, 0x02, 0xd0,
        0x1b, 0xa9, 0x02, 0x85, 0x02, 0x60, 0xa9, 0x01, 0x24, 0x02, 0xd0, 0x10, 0xa9, 0x04, 0x85, 0x02,
        0x60, 0xa9, 0x02, 0x24, 0x02, 0xd0, 0x05, 0xa9, 0x08, 0x85, 0x02, 0x60, 0x60, 0x20, 0x94, 0x06,
        0x20, 0xa8, 0x06, 0x60,
        0xa5, 0x00, # LDA
        0xc5, 0x10, # CMP
        0xd0, 0x0d, # BNE +13
        0xa5, 0x01, # LDA
        0xc5, 0x11, # CMP
        0xd0, 0x07, # BNE
        0xe6, 0x03, # INC
        0xe6, 0x03, # INC
        0x20, 0x2a, 0x06, # JSR
        0x60, # RTS


        0xa2, 0x02,
        0xb5, 0x10, 0xc5, 0x10, 0xd0, 0x06,
        0xb5, 0x11, 0xc5, 0x11, 0xf0, 0x09, 0xe8, 0xe8, 0xe4, 0x03, 0xf0, 0x06, 0x4c, 0xaa, 0x06, 0x4c,
        0x35, 0x07, 0x60, 0xa6, 0x03, 0xca, 0x8a, 0xb5, 0x10, 0x95, 0x12, 0xca,

        0x10, 0xf9, # BPL -7


        0xa5, 0x02,
        0x4a, 0xb0, 0x09, 0x4a, 0xb0, 0x19, 0x4a, 0xb0, 0x1f, 0x4a, 0xb0, 0x2f, 0xa5, 0x10, 0x38, 0xe9,
        0x20, 0x85, 0x10, 0x90, 0x01, 0x60, 0xc6, 0x11, 0xa9, 0x01, 0xc5, 0x11, 0xf0, 0x28, 0x60, 0xe6,
        0x10, 0xa9, 0x1f, 0x24, 0x10, 0xf0, 0x1f, 0x60, 0xa5, 0x10, 0x18, 0x69, 0x20, 0x85, 0x10, 0xb0,
        0x01, 0x60, 0xe6, 0x11, 0xa9, 0x06, 0xc5, 0x11, 0xf0, 0x0c, 0x60, 0xc6, 0x10, 0xa5, 0x10, 0x29,
        0x1f, 0xc9, 0x1f, 0xf0, 0x01, 0x60, 0x4c, 0x35, 0x07, 0xa0, 0x00, 0xa5, 0xfe, 0x91, 0x00, 0x60,
        0xa6, 0x03, 0xa9, 0x00, 0x81, 0x10, 0xa2, 0x00, 0xa9, 0x01, 0x81, 0x10, 0x60, 0xa2, 0x00, 0xea,
        0xea, 0xca, 0xd0, 0xfb, 0x60,
    ]
    # fmt: off

    cpu: CPU

    def __init__(self):
        self.cpu = CPU(callback=self.callback, program_offset=0x0600)
        self.logger = get_logger(self.__class__.__name__)

    def run(self) -> None:
        self.cpu.load_and_run(self.CODE)
        # self.cpu.load_and_deassemble(self.CODE)

    def callback(self) -> None:
        self.logger.info(f"Opcode: {getattr(self.cpu.opcode, 'mnemonic', None)} PC: {self.cpu.program_counter}, A: {self.cpu.register_a}, X: {self.cpu.register_x}, Y: {self.cpu.register_y}, SP: {self.cpu.stack_pointer}, Status: {Flags(int(self.cpu.status))}")

        # TODO:
        # read user input and write it to mem[0xFF]
        # update mem[0xFE] with new Random Number
        # read mem mapped screen state
        # render screen state

        # generate random number between 1-16 and store in memory location 0xfe
        self.cpu.memory.write(0xfe, random.randint(1, 16))


if __name__ == "__main__":
    SnakeGame().run()
