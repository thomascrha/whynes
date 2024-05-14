from typing import Any, Dict, List, Union
from copy import copy
from constants import U16, U8, Flags, AddressingMode, MEMORY_SIZE
from opcodes import Opcode
import sys

from logger import get_logger

logger = get_logger(__name__)

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

        self.memory = [0] * MEMORY_SIZE

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
                deref = (deref_base + self.register_y) & 0xFFFF
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


    def load_and_run(self, program: List[int], **kwargs: Dict[str, Union[int, Flags]]) -> None:
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

    def wrapping_add(self, value: int, increment: int = 1, mask: int = 0xFF):
        return (value + increment) & mask

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

                # ASL
                case 0x0a | 0x06 | 0x16 | 0x0e | 0x1e:
                    self.asl(opcode.mode)

                # BIT
                case 0x24 | 0x2c:
                    self.bit(opcode.mode)

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

                # CLC
                case 0x18:
                    self.clear_flag(Flags.CARRY)

                # SEC
                case 0x38:
                    self.set_flag(Flags.CARRY)

                # CLI
                case 0x58:
                    self.clear_flag(Flags.INTERRUPT_DISABLE)

                # SEI
                case 0x78:
                    self.set_flag(Flags.INTERRUPT_DISABLE)

                # CLV
                case 0xb8:
                    self.clear_flag(Flags.OVERFLOW)

                # CMP
                case 0xc9 | 0xc5 | 0xd5 | 0xcd | 0xdd | 0xd9 | 0xc1 | 0xd1:
                    addr = self.get_operand_address(opcode.mode)
                    value = self.mem_read(addr)
                    self.compare(self.register_a, value)

                # CPX
                case 0xe0 | 0xe4 | 0xec:
                    addr = self.get_operand_address(opcode.mode)
                    value = self.mem_read(addr)
                    self.compare(self.register_x, value)

                # CPY
                case 0xc0 | 0xc4 | 0xcc:
                    addr = self.get_operand_address(opcode.mode)
                    value = self.mem_read(addr)
                    self.compare(self.register_y, value)

                # DEC
                case 0xc6 | 0xd6 | 0xce | 0xde:
                    addr = self.get_operand_address(opcode.mode)
                    value = self.mem_read(addr)
                    value -= 1
                    self.update_zero_and_negative_flags(value)
                    self.mem_write(addr, value)

                # DEX
                case 0xca:
                    self.register_x -= 1
                    self.update_zero_and_negative_flags(self.register_x)

                # DEY
                case 0x88:
                    self.register_y -= 1
                    self.update_zero_and_negative_flags(self.register_y)

                # EOR
                case 0x49 | 0x45 | 0x55 | 0x4d | 0x5d | 0x59 | 0x41 | 0x51:
                    addr = self.get_operand_address(opcode.mode)
                    value = self.mem_read(addr)
                    self.register_a ^= value
                    self.update_zero_and_negative_flags(self.register_a)

                # INC
                case 0xe6 | 0xf6 | 0xee | 0xfe:
                    addr = self.get_operand_address(opcode.mode)
                    value = self.mem_read(addr)
                    value += 1
                    self.update_zero_and_negative_flags(value)
                    self.mem_write(addr, value)

                # INY
                case 0xc8:
                    self.register_y += 1
                    self.update_zero_and_negative_flags(self.register_y)

                # JMP
                case 0x4c | 0x6c:
                    self.jump(opcode.mode)

                # JSR
                case 0x20:
                    self.mem_write_u16(self.program_counter, self.program_counter - 1)
                    self.program_counter = self.mem_read_u16(self.program_counter)

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
                self.program_counter += (opcode.length - 1)

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

    def asl(self, mode: AddressingMode) -> None:
        addr = self.get_operand_address(mode)
        if mode != AddressingMode.ACCUMULATOR:
            value = self.mem_read(addr)
        else:
            value = copy(self.register_a)

        if value >> 7 == 1:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        data = value << 1

        self.update_zero_and_negative_flags(data)

        if mode == AddressingMode.ACCUMULATOR:
            self.register_a = data
        else:
            self.mem_write(addr, data)

    def sbc(self, mode: AddressingMode) -> None:
        addr = self.get_operand_address(mode)
        value = self.mem_read(addr)
        # After ADC is implemented, implementing SBC becomes trivial as A - B = A + (-B). And -B = !B + 1
        self.add_to_register_a(((value ^ 0xFF) + 1) & 0xFF)

    def unsigned_to_signed(self, unsigned_int: int, bits: int):
        shift = 1 << (bits - 1)
        return (unsigned_int & shift - 1) - (unsigned_int & shift)

    def branch(self):
        # 8-bit signed integer
        value = self.mem_read(self.program_counter)
        offset = self.unsigned_to_signed(value, 8)

        self.program_counter += offset

    def bit(self, mode: AddressingMode) -> None:
        addr = self.get_operand_address(mode)
        value = self.mem_read(addr)

        result = self.register_a & value

        if result == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        if value & 0b10000000 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        if value & 0b01000000 != 0:
            self.set_flag(Flags.OVERFLOW)
        else:
            self.clear_flag(Flags.OVERFLOW)

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

        self.register_a = result

    def compare(self, register: int, value: int) -> None:
        if register >= value:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        self.update_zero_and_negative_flags(register - value)

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

