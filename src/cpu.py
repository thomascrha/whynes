from typing import Any, Dict, List
from copy import copy
import enum
from opcodes import Opcode
import sys

class Flags(enum.IntFlag):
    """
    7  bit  0
    ---- ----
    NV1B DIZC
    |||| ||||
    |||| |||+- Carry
    |||| ||+-- Zero
    |||| |+--- Interrupt Disable
    |||| +---- Decimal
    |||+------ (No CPU effect; see: the B flag)
    ||+------- (No CPU effect; always pushed as 1)
    |+-------- Overflow
    +--------- Negative
    """
    CARRY = 1
    ZERO = 2
    INTERRUPT_DISABLE = 4
    DECIMAL = 8
    BREAK = 16
    UNUSED = 32
    OVERFLOW = 64
    NEGATIVE = 128

class AddressingMode(enum.Enum):
    IMMEDIATE = "IMMEDIATE"
    ZERO_PAGE = "ZERO_PAGE"
    X_INDEXED_ZERO_PAGE = "X_INDEXED_ZERO_PAGE"
    Y_INDEXED_ZERO_PAGE = "Y_INDEXED_ZERO_PAGE"
    ABSOLUTE = "ABSOLUTE"
    X_INDEXED_ABSOLUTE = "X_INDEXED_ABSOLUTE"
    Y_INDEXED_ABSOLUTE = "Y_INDEXED_ABSOLUTE"
    X_INDEXED_ZERO_PAGE_INDIRECT = "X_INDEXED_ZERO_PAGE_INDIRECT"
    ZERO_PAGE_INDIRECT_Y_INDEXED = "ZERO_PAGE_INDIRECT_Y_INDEXED"
    ACCUMULATOR = "ACCUMULATOR"
    RELATIVE = "RELATIVE"
    IMPLIED = "IMPLIED"
    ABSOLUTE_INDIRECT = "ABSOLUTE_INDIRECT"


class CPU:
    register_a: int
    register_x: int
    register_y: int
    status: Flags
    program_counter: int
    memory: List[int]

    opcodes: Dict[int, Opcode]

    def __init__(self):
        self.register_x = 0 # 8 bits
        self.register_a = 0 # 8 bits
        self.status = Flags(0) # 8 bits

        self.program_counter = -1

        self.memory = [0] * 0xFFFF

        self.opcodes = Opcode.load_opcodes()

    # Memory
    def mem_read(self, addr: int) -> int:
        return self.memory[addr]

    def mem_write(self, addr: int, data: int) -> None:
        self.memory[addr] = data

    def mem_read_u16(self, pos: int) -> int:
        low = self.mem_read(pos)
        hi = self.mem_read(pos + 1)

        return hi << 8 | low

    def mem_write_u16(self, pos: int, data: int) -> None:
        hi = data >> 8
        low = data & 0xFF
        self.mem_write(pos, low)
        self.mem_write(pos + 1, hi)

    # Flag operations
    def set_flag(self, flag: Flags):
        self.status |= flag

    def clear_flag(self, flag: Flags):
        self.status &= ~flag

    def get_flag(self, flag: Flags) -> bool:
        return (self.status & flag != 0)

    # Addressing
    def get_operand_address(self, mode: AddressingMode) -> Any:
        match mode:
            case AddressingMode.IMMEDIATE:
                return self.program_counter

            case AddressingMode.ZERO_PAGE:
                return self.mem_read(self.program_counter)

            case AddressingMode.ABSOLUTE:
                return self.mem_read_u16(self.program_counter)

            case AddressingMode.X_INDEXED_ZERO_PAGE:
                pos = self.mem_read(self.program_counter)
                addr = (pos + self.register_x) & 0xFFFF
                return addr

            case AddressingMode.Y_INDEXED_ZERO_PAGE:
                pos = self.mem_read(self.program_counter)
                addr = (pos + self.register_y) & 0xFFFF
                return addr

            case AddressingMode.X_INDEXED_ABSOLUTE:
                base = self.mem_read_u16(self.program_counter)
                addr = (base + self.register_x) & 0xFFFF
                return addr

            case AddressingMode.Y_INDEXED_ABSOLUTE:
                base = self.mem_read_u16(self.program_counter)
                addr = (base + self.register_y) & 0xFFFF
                return addr

            case AddressingMode.X_INDEXED_ZERO_PAGE_INDIRECT:
                base = self.mem_read(self.program_counter)
                ptr = (base + self.register_x) & 0xFF
                low = self.mem_read(ptr)
                hi = self.mem_read((ptr + 1) & 0xFFFF )
                return hi << 8 | low

            case AddressingMode.ZERO_PAGE_INDIRECT_Y_INDEXED:
                base = self.mem_read(self.program_counter)
                low = self.mem_read(base)
                hi = self.mem_read((base + 1) & 0xFFFF)
                deref_base = hi << 8 | low
                deref = (deref_base + 1) & 0xFFFF
                return deref

            case AddressingMode.ACCUMULATOR:
                pass

            case AddressingMode.RELATIVE:
                pass

            case AddressingMode.IMPLIED:
                pass

            case AddressingMode.ABSOLUTE_INDIRECT:
                pass

            case _:
                print("fuck")
                sys.exit(-1)

    # Runtime
    def load_and_run(self, program: List[int]) -> None:
        self.load(program)
        self.reset()
        self.run()

    def load(self, program: List[int]):
        self.memory[0x8000:(0x8000 + len(program))] = program
        self.mem_write_u16(0xFFFC, 0x8000)

    def reset(self) -> None:
        self.register_a = 0
        self.register_y = 0
        self.register_x = 0
        self.status = Flags(0)
        self.program_counter = self.mem_read_u16(0xFFFC)

    def run(self) -> None:
        while True:
            code = self.mem_read(self.program_counter)
            self.program_counter += 1
            program_counter_state = copy(self.program_counter)

            opcode = self.opcodes.get(code)
            if not opcode:
                print("fuck")
                sys.exit(-1)

            match opcode.code:
                # LDA
                case 0xa9 | 0xa5 | 0xb5 | 0xad | 0xbd | 0xb9 | 0xa1 | 0xb1:
                    self.lda(opcode.mode)

                # STA
                case 0x85 | 0x95 | 0x8d | 0x9d | 0x99 | 0x81 | 0x91:
                    self.sta(opcode.mode);

                # TAX
                case 0xaa:
                    self.tax()

                # INX
                case 0xe8:
                    self.inx()

                # BREAK
                case 0x00:
                    return

                case _:
                    print("fuck")
                    sys.exit(-1)

            if program_counter_state == self.program_counter:
                self.program_counter += (opcode.lenght - 1)

    # Opcodes
    def lda(self, mode: AddressingMode):
        addr = self.get_operand_address(mode)
        value = self.mem_read(addr)

        self.register_a = value
        self.update_zero_and_negative_flags(self.register_a)

    def sta(self, mode: AddressingMode):
        addr = self.get_operand_address(mode)
        self.mem_write(addr, self.register_a)

    def inx(self):
        self.register_x += 1
        self.register_x &= 0xFF
        self.update_zero_and_negative_flags(self.register_x)

    def tax(self):
        self.register_x = self.register_a
        self.update_zero_and_negative_flags(self.register_x)


    def update_zero_and_negative_flags(self, result: int):
        # Set zero flag if a is 0
        if result == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # set Negative flag if a's 7th bit is set
        if result & 0b10000000 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

# Tests
def test_0xa9_lda_immediate_load_data():
    cpu = CPU()
    cpu.load_and_run([0xa9, 0x05, 0x00])
    assert cpu.register_a == 0x05

    # make sure the zero flag isn't set
    assert cpu.get_flag(Flags.ZERO) == False

    # make sure negative flag isn't set
    assert cpu.get_flag(Flags.NEGATIVE) == False

def test_0xa9_lda_zero_flag():
    cpu = CPU()
    cpu.load_and_run([0xa9, 0x00, 0x00])
    assert cpu.get_flag(Flags.ZERO)

def test_0xaa_tax_move_a_to_x():
    cpu = CPU()
    cpu.load_and_run([0xa9, 0x0A,0xaa, 0x00])
    assert cpu.register_x == 10

def test_5_ops_working_together():
    cpu = CPU()
    cpu.load_and_run([0xa9, 0xc0, 0xaa, 0xe8, 0x00])
    assert cpu.register_x == 0xc1

def test_inx_overflow():
    cpu = CPU()
    cpu.load_and_run([0xa9, 0xff, 0xaa,0xe8, 0xe8, 0x00])
    assert cpu.register_x == 1

def test_lda_from_memory():
    cpu = CPU()
    cpu.mem_write(0x10, 0x55)
    cpu.load_and_run([0xa5, 0x10, 0x00])
    assert cpu.register_a == 0x55


