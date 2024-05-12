from typing import Any, Dict, List
from copy import copy
import enum
from opcodes import Opcode
import sys

from logger import get_logger

logger = get_logger(__name__)

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
    RELATIVE = "RELATIVE"
    ACCUMULATOR = "ACCUMULATOR"
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
        self.status = Flags(0b0000000) # 8 bits

        self.program_counter = 0x10

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
    def set_flag(self, flag: Flags) -> None:
        self.status |= flag

    def clear_flag(self, flag: Flags) -> None:
        self.status &= ~flag

    def get_flag(self, flag: Flags) -> bool:
        return (self.status & flag != 0)

    def read_with_offset(self, offset: int, u8: bool = True) -> int:
        reader = self.mem_read_u16
        if u8:
            reader = self.mem_read

        base = reader(self.program_counter)
        addr = (base + offset) & 0xFFFF

        return addr

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
                return self.read_with_offset(self.register_x)

            case AddressingMode.Y_INDEXED_ZERO_PAGE:
                return self.read_with_offset(self.register_y)

            case AddressingMode.X_INDEXED_ABSOLUTE:
                return self.read_with_offset(self.register_x, u8=False)

            case AddressingMode.Y_INDEXED_ABSOLUTE:
                return self.read_with_offset(self.register_y, u8=False)

            case AddressingMode.X_INDEXED_ZERO_PAGE_INDIRECT:
                base = self.mem_read(self.program_counter)
                ptr = (base + self.register_x) & 0xFF
                low = self.mem_read(ptr)
                hi = self.mem_read((ptr + 1) & 0xFF )
                return hi << 8 | low

            case AddressingMode.ZERO_PAGE_INDIRECT_Y_INDEXED:
                base = self.mem_read(self.program_counter)
                low = self.mem_read(base)
                hi = self.mem_read((base + 1) & 0xFF)
                deref_base = hi << 8 | low
                deref = (deref_base + 1) & 0xFFFF
                return deref

            # Only used by branch instructions
            case AddressingMode.RELATIVE:
                # handled in the branch function
                return None

            case AddressingMode.ACCUMULATOR:
                return self.register_a

            case AddressingMode.IMPLIED:
                return None

            # Only used by JMP
            case AddressingMode.ABSOLUTE_INDIRECT:
                # handled in the JMP function
                return None


    def load_and_run(self, program: List[int], **kwargs: Dict[str, int]) -> None:
        self.load(program)
        self.reset(**kwargs)
        self.run()

    def load(self, program: List[int]):
        self.memory[0x8000:(0x8000 + len(program))] = program
        self.mem_write_u16(0xFFFC, 0x8000)

    def reset(self, **kwargs: Dict[str, int]) -> None:
        self.register_a = 0
        self.register_y = 0
        self.register_x = 0
        self.status = Flags(0b0000000)
        self.program_counter = self.mem_read_u16(0xFFFC)

        # override the above attributes if they are passed in the kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def run(self) -> Any:
        while True:
            code = self.mem_read(self.program_counter)
            self.program_counter += 1
            program_counter_state = copy(self.program_counter)

            opcode = self.opcodes.get(code)
            if not opcode:
                logger.info("fuck")
                sys.exit(-1)

            match opcode.code:
                # LDA
                case 0xa9 | 0xa5 | 0xb5 | 0xad | 0xbd | 0xb9 | 0xa1 | 0xb1:
                    self.lda(opcode.mode)

                # STA
                case 0x85 | 0x95 | 0x8d | 0x9d | 0x99 | 0x81 | 0x91:
                    self.sta(opcode.mode);

                # ADC
                case 0x69 | 0x65 | 0x75 | 0x6d | 0x7d | 0x79 | 0x61 | 0x71:
                    self.adc(opcode.mode)

                # AND
                case 0x29 | 0x25 | 0x35 | 0x2d | 0x3d | 0x39 | 0x21 | 0x31:
                    self.and_(opcode.mode)

                # SDC
                case 0xE9 | 0xe5 | 0xf5 | 0xed | 0xfd | 0xf9 | 0xe1 | 0xf1:
                    self.sbc(opcode.mode)

                # TAX
                case 0xaa:
                    self.tax()

                # INX
                case 0xe8:
                    self.inx()

                # LDA
                case 0xa9 | 0xa5 | 0xb5 | 0xad | 0xbd | 0xb9 | 0xa1 | 0xb1:
                    self.lda(opcode.mode)

                # LDX
                case 0xa2 | 0xa6 | 0xb6 | 0xae | 0xbe:
                    self.ldx(opcode.mode)

                # BCC
                case 0x90:
                    if not self.get_flag(Flags.CARRY):
                        self.branch()

                # BCS
                case 0xb0:
                    if self.get_flag(Flags.CARRY):
                        self.branch()

                # BEQ
                case 0xf0:
                    if self.get_flag(Flags.ZERO):
                        self.branch()

                # BNE
                case 0xd0:
                    if not self.get_flag(Flags.ZERO):
                        self.branch()

                # BMI
                case 0x30:
                    if self.get_flag(Flags.NEGATIVE):
                        self.branch()

                # BPL
                case 0x10:
                    if not self.get_flag(Flags.NEGATIVE):
                        self.branch()

                # BVC
                case 0x50:
                    if not self.get_flag(Flags.OVERFLOW):
                        self.branch()

                # BVS
                case 0x70:
                    if self.get_flag(Flags.OVERFLOW):
                        self.branch()

                # JMP
                case 0x4c | 0x6c:
                    self.jump(opcode.mode)

                # BREAK
                case 0x00:
                    return False

                case _:
                    logger.info("fuck")
                    sys.exit(-1)

            if program_counter_state == self.program_counter:
                self.program_counter += (opcode.lenght - 1)

    # Opcodes
    def adc(self, mode: AddressingMode) -> None:
        addr = self.get_operand_address(mode)
        value = self.mem_read(addr)
        self.add_to_register_a(value)

    def and_(self, mode: AddressingMode) -> None:
        addr = self.get_operand_address(mode)
        value = self.mem_read(addr)

        self.register_a &= value

        self.update_zero_and_negative_flags(self.register_a)

    def sbc(self, mode: AddressingMode) -> None:
        addr = self.get_operand_address(mode)
        value = self.mem_read(addr)
        # After ADC is implemented, implementing SBC becomes trivial as A - B = A + (-B). And -B = !B + 1
        self.add_to_register_a(((value ^ 0xFF) + 1) & 0xFF)

    def wrapping_add(self, value: int, increment: int = 1, mask: int = 0xFF):
        return (value + increment) & mask


    def branch(self) -> None:
        jump = self.mem_read(self.program_counter)
        jump_addr = self.wrapping_add(self.program_counter, 1, 0xFFFF) + jump
        if self.wrapping_add(self.program_counter, 1, 0xFF00) != jump_addr & 0xFF00:
            # TODO implement bus
            pass

        self.program_counter = jump_addr

    def jump(self, mode: AddressingMode) -> None:
        mem_address = self.mem_read_u16(self.program_counter)

        if mode == AddressingMode.ABSOLUTE_INDIRECT:
            if mem_address & 0x00FF == 0x00FF:
                lo = self.mem_read(mem_address)
                hi = self.mem_read(mem_address & 0xFF00)
                indirect_ref = (hi << 8) | lo
            else:
                indirect_ref = self.mem_read_u16(mem_address)

            mem_address = indirect_ref

        self.program_counter = mem_address

    def add_to_register_a(self, value) -> None:
        sum = self.register_a + value + self.get_flag(Flags.CARRY)
        carry = sum > 0xFF

        if carry:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        result = sum & 0xFF

        if (value ^ result) & (result ^ self.register_a) & 0x80 != 0:
            self.set_flag(Flags.OVERFLOW)
        else:
            self.clear_flag(Flags.OVERFLOW)

        self.update_zero_and_negative_flags(result)

        print(f"result: {result}")
        self.register_a = result

    def lda(self, mode: AddressingMode):
        addr = self.get_operand_address(mode)
        value = self.mem_read(addr)
        self.register_a = value
        self.update_zero_and_negative_flags(self.register_a)

    def ldx(self, mode: AddressingMode):
        addr = self.get_operand_address(mode)
        value = self.mem_read(addr)
        self.register_x = value
        self.update_zero_and_negative_flags(self.register_x)

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
            logger.info("Fuck Yeah")
            self.set_flag(Flags.NEGATIVE)
        else:
            logger.info("Oh fuck")
            self.clear_flag(Flags.NEGATIVE)

# Failing tests
def test_0x61_adc_indirect_x():
    cpu = CPU()

    cpu.mem_write(0x10, 0x20)
    cpu.mem_write(0x20, 0x30)
    cpu.mem_write(0x3020, 0x01)

    # ADC ($0x10,X)
    cpu.load_and_run([0x61, 0x10], **{"register_x": 0x10})
    assert cpu.register_a == 1

def test_0x71_adc_indirect_y():
    cpu = CPU()
    cpu.mem_write(0x10, 0x20)
    cpu.mem_write(0x21, 0x30)
    cpu.mem_write(0x3021, 0x01)
    cpu.load_and_run([0x71, 0x10], **{"register_y": 0x10})
    assert cpu.register_a == 1


