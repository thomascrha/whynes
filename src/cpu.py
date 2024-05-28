import sys
from copy import copy
from typing import Any, Callable, Dict, List, Optional, Union
from constants import MEMORY_SIZE, AddressingMode, Flags
from logger import get_logger
from memory import Memory
from opcodes import Opcode

logger = get_logger(__name__)


# https://www.nesdev.org/obelisk-6502-guide/index.html
class CPU:
    register_a: int
    register_x: int
    register_y: int
    status: Flags
    program_counter: int
    memory: Memory
    stack_pointer: int

    opcodes: Dict[int, Opcode]
    opcode: Opcode | None
    program_len: int

    def __init__(
        self,
        callback: Optional[Callable] = None,
        stack: int = 0x0100,
        program_offset: int = 0x8000,
        **kwargs: Dict[str, Union[int, List[Flags]]],
    ):
        self.register_x = 0  # 8 bits
        self.register_a = 0  # 8 bits
        self.status = Flags.UNUSED | Flags.BREAK  # 8 bits

        self.program_counter = 0x10

        self.stack_pointer = 0xFF

        self.memory = Memory()
        self.opcodes = Opcode.load_opcodes()

        self.callback = callback

        self.stack = stack
        self.program_offset = program_offset
        self.load_kwargs(**kwargs)

        self.opcode = None
        self.program_len = 0

    def load_kwargs(self, **kwargs: Dict[str, Union[int, List[Flags]]]) -> None:
        """Load the kwargs into the CPU object - mainly used for testing purposes

        Args:
            **kwargs (Dict[str, Union[int, List[Flags]]]): The kwargs to load into the CPU object

        Returns:
            None
        """
        # override the above attributes if they are passed in the kwargs
        for key, value in kwargs.items():
            if key == "status" and isinstance(value, list):
                for flag in value:
                    self.set_flag(flag)
            else:
                setattr(self, key, value)

    # Flag operations
    def set_flag(self, flag: Flags) -> None:
        self.status |= flag

    def clear_flag(self, flag: Flags) -> None:
        self.status &= ~flag

    def get_flag(self, flag: Flags) -> bool:
        return self.status & flag != 0

    def stack_pop(self) -> int:
        self.stack_pointer = (self.stack_pointer + 1) & 0xFFFF
        return self.memory.read(self.stack + self.stack_pointer)

    def stack_push(self, data: int) -> None:
        self.memory.write(self.stack + self.stack_pointer, data)
        self.stack_pointer = (self.stack_pointer - 1) & 0xFFFF

    def stack_push_u16(self, data: int) -> None:
        # i don't think the wrap is required but im not 100%
        # self.stack_push((data >> 8) & 0xFF)
        self.stack_push(data >> 8)
        self.stack_push(data & 0xFF)

    def stack_pop_u16(self) -> int:
        low = self.stack_pop()
        hi = self.stack_pop()

        return hi << 8 | low

    # Addressing
    def read_with_offset(self, offset: int, u8: bool = True) -> int:
        reader = self.memory.read_u16
        width = 0xFFFF
        if u8:
            reader = self.memory.read
            width = 0xFF

        base = reader(self.program_counter)
        addr = (base + offset) & width

        return addr

    def get_operand_address(self, mode: AddressingMode) -> Any:
        match mode:
            case AddressingMode.IMMEDIATE:
                return self.program_counter

            case AddressingMode.ZERO_PAGE:
                return self.memory.read(self.program_counter)

            case AddressingMode.ABSOLUTE:
                return self.memory.read_u16(self.program_counter)

            case AddressingMode.X_INDEXED_ZERO_PAGE:
                return self.read_with_offset(self.register_x, u8=True)

            case AddressingMode.Y_INDEXED_ZERO_PAGE:
                return self.read_with_offset(self.register_y, u8=True)

            case AddressingMode.X_INDEXED_ABSOLUTE:
                return self.read_with_offset(self.register_x, u8=False)

            case AddressingMode.Y_INDEXED_ABSOLUTE:
                return self.read_with_offset(self.register_y, u8=False)

            case AddressingMode.X_INDEXED_ZERO_PAGE_INDIRECT:
                i = (self.memory.read(self.program_counter) + self.register_x) & 0xFF
                address = ((self.memory.read((i + 1) & 0xFF) << 8) + self.memory.read(i)) & 0xFFFF
                return address

            case AddressingMode.ZERO_PAGE_INDIRECT_Y_INDEXED:
                i = self.memory.read(self.program_counter)
                address = (self.memory.read(i) + (self.memory.read((i + 1) & 0xFF) << 8) + self.register_y) & 0xFFFF

                return address

            case AddressingMode.RELATIVE:
                return self.memory.read(self.program_counter)

            case AddressingMode.ACCUMULATOR:
                return self.register_a

            case AddressingMode.IMPLIED:
                return None

            case AddressingMode.ABSOLUTE_INDIRECT:
                return None

    def pre_load(self, program: List[int], **kwargs: Dict[str, Union[int, List[Flags]]]) -> None:
        self.program_len = len(program)
        self.load(program)
        self.reset(**kwargs)

    def load_and_deassemble(self, program: List[int], **kwargs: Dict[str, Union[int, List[Flags]]]) -> None:
        self.pre_load(program, **kwargs)
        self.deassemble()

    def load_and_run(self, program: List[int], **kwargs: Dict[str, Union[int, List[Flags]]]) -> None:
        self.pre_load(program, **kwargs)
        self.run()

    def load(self, program: List[int]):
        self.memory.memory[self.program_offset : (self.program_offset + len(program))] = program
        self.memory.write_u16(0xFFFC, self.program_offset)

    def reset(self, **kwargs: Dict[str, Union[int, List[Flags]]]) -> None:
        self.register_a = 0
        self.register_y = 0
        self.register_x = 0
        self.status = Flags.UNUSED | Flags.BREAK
        self.stack_pointer = 0xFF
        self.program_counter = self.memory.read_u16(0xFFFC)
        self.opcode = None

        self.load_kwargs(**kwargs)

    def update_negative_flag(self, result: int):
        if result & 0x80:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

    def update_zero_and_negative_flags(self, result: int):
        # Set zero flag if a is 0
        if result == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        self.update_negative_flag(result)

    def deassemble(self) -> None:
        intial_pc = self.program_counter
        tick = 1
        while True:
            code = self.memory.read(self.program_counter)
            self.program_counter += 1
            program_counter_state = copy(self.program_counter)
            self.opcode = self.opcodes.get(code)

            if not self.opcode:
                logger.info("undefined opcode")
                sys.exit(-1)

            self.opcode.opcode_params = self.get_operand_address(self.opcode.addressing_mode)

            # string = self.mnemonic.replace("nn", f"{self.opcode_params:0{2}X}")

            program_mem_string = f"{(self.program_counter - 1):#0{6}X}".replace("X", "x")
            print(f"{program_mem_string}\t{tick}\t{self.opcode.string(self.memory)}")

            if program_counter_state == self.program_counter:
                self.program_counter += self.opcode.length - 1

            # check if we have reached the end of the program
            if (intial_pc + self.program_len) <= self.program_counter:
                break

            tick += 1

    def run(self) -> Any:
        while True:
            code = self.memory.read(self.program_counter)
            self.program_counter += 1

            program_counter_state = copy(self.program_counter)
            self.opcode = self.opcodes.get(code)

            if not self.opcode:
                logger.info("undefined opcode")
                sys.exit(-1)

            if self.callback:
                self.callback()

            # Opcodematch opcode.code:
            match self.opcode.code:
                # ADC
                case 0x69 | 0x65 | 0x75 | 0x6D | 0x7D | 0x79 | 0x61 | 0x71:
                    self.adc(self.opcode.addressing_mode)

                # AND
                case 0x29 | 0x25 | 0x35 | 0x2D | 0x3D | 0x39 | 0x21 | 0x31:
                    self.and_(self.opcode.addressing_mode)

                # ASL
                case 0x0A | 0x06 | 0x16 | 0x0E | 0x1E:
                    self.asl(self.opcode.addressing_mode)

                # BCC
                case 0x90:
                    if not self.get_flag(Flags.CARRY):
                        self.branch()

                # BCS
                case 0xB0:
                    if self.get_flag(Flags.CARRY):
                        self.branch()

                # BEQ
                case 0xF0:
                    if self.get_flag(Flags.ZERO):
                        self.branch()

                # BIT
                case 0x24 | 0x2C:
                    self.bit(self.opcode.addressing_mode)

                # BMI
                case 0x30:
                    if self.get_flag(Flags.NEGATIVE):
                        self.branch()

                # BNE
                case 0xD0:
                    if not self.get_flag(Flags.ZERO):
                        self.branch()

                # BPL
                case 0x10:
                    if not self.get_flag(Flags.NEGATIVE):
                        self.branch()

                # BREAK
                case 0x00:
                    return False

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

                # CLD
                case 0xD8:
                    self.clear_flag(Flags.DECIMAL)

                # CLI
                case 0x58:
                    self.clear_flag(Flags.INTERRUPT_DISABLE)

                # CLV
                case 0xB8:
                    self.clear_flag(Flags.OVERFLOW)

                # CMP
                case 0xC9 | 0xC5 | 0xD5 | 0xCD | 0xDD | 0xD9 | 0xC1 | 0xD1:
                    self.compare(self.opcode.addressing_mode, self.register_a)

                # CPX
                case 0xE0 | 0xE4 | 0xEC:
                    self.compare(self.opcode.addressing_mode, self.register_x)

                # CPY
                case 0xC0 | 0xC4 | 0xCC:
                    self.compare(self.opcode.addressing_mode, self.register_y)

                # DEC
                case 0xC6 | 0xD6 | 0xCE | 0xDE:
                    addr = self.get_operand_address(self.opcode.addressing_mode)
                    value = self.memory.read(addr)
                    value = (value - 1) & 0xFF
                    self.update_zero_and_negative_flags(value)
                    self.memory.write(addr, value)

                # DEX
                case 0xCA:
                    self.register_x = (self.register_x - 1) & 0xFF
                    self.update_zero_and_negative_flags(self.register_x)

                # DEY
                case 0x88:
                    self.register_y = (self.register_y - 1) & 0xFF
                    self.update_zero_and_negative_flags(self.register_y)

                # EOR
                case 0x49 | 0x45 | 0x55 | 0x4D | 0x5D | 0x59 | 0x41 | 0x51:
                    addr = self.get_operand_address(self.opcode.addressing_mode)
                    value = self.memory.read(addr)
                    self.register_a ^= value
                    self.update_zero_and_negative_flags(self.register_a)

                # INC
                case 0xE6 | 0xF6 | 0xEE | 0xFE:
                    addr = self.get_operand_address(self.opcode.addressing_mode)
                    value = self.memory.read(addr)
                    value = (value + 1) & 0xFF
                    self.memory.write(addr, value)
                    self.update_zero_and_negative_flags(value)

                # INX
                case 0xE8:
                    self.inx()

                # INY
                case 0xC8:
                    self.register_y = (self.register_y + 1) & 0xFF
                    self.update_zero_and_negative_flags(self.register_y)

                # JMP ABSOLUTE
                case 0x4C:
                    mem_address = self.memory.read_u16(self.program_counter)
                    self.program_counter = mem_address

                # JMP INDIRECT
                case 0x6C:
                    mem_address = self.memory.read_u16(self.program_counter)

                    if self.opcode.addressing_mode == AddressingMode.ABSOLUTE_INDIRECT:
                        if mem_address & 0x00FF == 0x00FF:
                            lo = self.memory.read(mem_address)
                            hi = self.memory.read(mem_address & 0xFF00)
                            indirect_ref = (hi << 8) | lo
                        else:
                            indirect_ref = self.memory.read_u16(mem_address)

                        mem_address = indirect_ref

                    self.program_counter = mem_address
                # JSR
                case 0x20:
                    self.stack_push_u16(self.program_counter + 2 - 1)
                    target_address = self.memory.read_u16(self.program_counter)
                    self.program_counter = target_address

                # LDA
                case 0xA9 | 0xA5 | 0xB5 | 0xAD | 0xBD | 0xB9 | 0xA1 | 0xB1:
                    addr = self.get_operand_address(self.opcode.addressing_mode)
                    value = self.memory.read(addr)
                    self.register_a = value
                    self.update_zero_and_negative_flags(self.register_a)

                # LDX
                case 0xA2 | 0xA6 | 0xB6 | 0xAE | 0xBE:
                    self.register_x = self.memory.read(self.get_operand_address(self.opcode.addressing_mode))
                    self.update_zero_and_negative_flags(self.register_x)

                # LDY
                case 0xA0 | 0xA4 | 0xB4 | 0xAC | 0xBC:
                    self.register_y = self.memory.read(self.get_operand_address(self.opcode.addressing_mode))
                    self.update_zero_and_negative_flags(self.register_y)

                # LSR
                case 0x4A | 0x46 | 0x56 | 0x4E | 0x5E:
                    self.lsr(self.opcode.addressing_mode)

                # NOP
                case 0xEA:
                    pass

                # ORA
                case 0x09 | 0x05 | 0x15 | 0x0D | 0x1D | 0x19 | 0x01 | 0x11:
                    addr = self.get_operand_address(self.opcode.addressing_mode)
                    value = self.memory.read(addr)
                    self.register_a |= value

                # PHA
                case 0x48:
                    self.stack_push(self.register_a)

                # PHP
                case 0x08:
                    # <//http://wiki.nesdev.com/w/index.php/CPU_status_flag_behavior
                    flags = copy(self.status)
                    flags = flags | Flags.BREAK | Flags.UNUSED
                    self.stack_push(flags)

                # PLA
                case 0x68:
                    self.register_a = self.stack_pop()

                # PLP
                case 0x28:
                    self.status = Flags(self.stack_pop())
                    self.clear_flag(Flags.BREAK)
                    self.set_flag(Flags.UNUSED)

                # ROL
                case 0x2A | 0x26 | 0x36 | 0x2E | 0x3E:
                    self.rol(self.opcode.addressing_mode)

                # ROR
                case 0x6A | 0x66 | 0x76 | 0x6E | 0x7E:
                    self.ror(self.opcode.addressing_mode)

                # RTI
                case 0x40:
                    self.status = self.stack_pop()
                    self.clear_flag(Flags.BREAK)
                    self.set_flag(Flags.UNUSED)

                    self.program_counter = self.stack_pop_u16()

                # RTS
                case 0x60:
                    self.program_counter = self.stack_pop_u16() + 1

                # SBC
                case 0xE9 | 0xE5 | 0xF5 | 0xED | 0xFD | 0xF9 | 0xE1 | 0xF1:
                    addr = self.get_operand_address(self.opcode.addressing_mode)
                    value = self.memory.read(addr)
                    self.add_to_register_a(((value ^ 0xFF) + 1) & 0xFF)

                # SEC
                case 0x38:
                    self.set_flag(Flags.CARRY)

                # SED
                case 0xF8:
                    self.set_flag(Flags.DECIMAL)

                # SEI
                case 0x78:
                    self.set_flag(Flags.INTERRUPT_DISABLE)

                # STA
                case 0x85 | 0x95 | 0x8D | 0x9D | 0x99 | 0x81 | 0x91:
                    self.memory.write(self.get_operand_address(self.opcode.addressing_mode), self.register_a)

                # STX
                case 0x86 | 0x96 | 0x8E:
                    self.memory.write(self.get_operand_address(self.opcode.addressing_mode), self.register_x)

                # STY
                case 0x84 | 0x94 | 0x8C:
                    self.memory.write(self.get_operand_address(self.opcode.addressing_mode), self.register_y)

                # TAX
                case 0xAA:
                    self.tax()

                # TAY
                case 0xA8:
                    self.tay()

                # TSX
                case 0xBA:
                    self.tsx()

                # TXA
                case 0x8A:
                    self.txa()

                # TXS
                case 0x9A:
                    self.txs()

                # TYA
                case 0x98:
                    self.tya()

                case _:
                    logger.info("Not implemented")
                    sys.exit(-1)

            if program_counter_state == self.program_counter:
                self.program_counter += self.opcode.length - 1

    def adc(self, mode: AddressingMode) -> None:
        addr = self.get_operand_address(mode)
        value = self.memory.read(addr)
        self.add_to_register_a(value)

    def and_(self, mode: AddressingMode) -> None:
        addr = self.get_operand_address(mode)
        value = self.memory.read(addr)

        self.register_a &= value

        self.update_zero_and_negative_flags(self.register_a)

    def asl(self, mode: AddressingMode) -> None:
        addr = self.get_operand_address(mode)
        if mode != AddressingMode.ACCUMULATOR:
            value = self.memory.read(addr)
        else:
            value = copy(self.register_a)

        if value >> 7 == 1:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        data = (value << 1) | self.get_flag(Flags.CARRY)

        if mode == AddressingMode.ACCUMULATOR:
            self.register_a = data
        else:
            self.update_negative_flag(data)
            self.memory.write(addr, data)

    def sbc(self, mode: AddressingMode) -> None:
        addr = self.get_operand_address(mode)
        value = self.memory.read(addr)
        # After ADC is implemented, implementing SBC becomes trivial as A - B = A + (-B). And -B = !B + 1
        self.add_to_register_a(((value ^ 0xFF) + 1) & 0xFF)

    def unsigned_to_signed(self, unsigned_value: int, bit_width: int) -> int:
        max_signed_value = 2**bit_width - 1

        if unsigned_value > max_signed_value:
            raise ValueError(f"Value {unsigned_value} is greater than the max signed value of {max_signed_value}")

        if unsigned_value & (1 << (bit_width - 1)):
            return unsigned_value - (1 << bit_width)

        return unsigned_value

    def branch(self):
        jump = self.memory.read(self.program_counter)
        jump_address = self.unsigned_to_signed(jump, 8) + self.program_counter
        self.program_counter = jump_address

        # required to skip the next byte
        self.program_counter += self.opcode.length - 1

    def bit(self, mode: AddressingMode) -> None:
        addr = self.get_operand_address(mode)
        value = self.memory.read(addr)

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
        mem_address = self.memory.read_u16(self.program_counter)

        if mode == AddressingMode.ABSOLUTE_INDIRECT:
            if mem_address & 0x00FF == 0x00FF:
                lo = self.memory.read(mem_address)
                hi = self.memory.read(mem_address & 0xFF00)
                indirect_ref = (hi << 8) | lo
            else:
                indirect_ref = self.memory.read_u16(mem_address)

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

    def compare(self, mode: AddressingMode, compare_with: int) -> None:
        addr = self.get_operand_address(mode)
        value = self.memory.read(addr)
        if value <= compare_with:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        self.update_zero_and_negative_flags(compare_with - value)

    def lsr(self, mode: AddressingMode):
        addr = self.get_operand_address(mode)
        if mode != AddressingMode.ACCUMULATOR:
            value = self.memory.read(addr)
        else:
            value = copy(self.register_a)

        if value & 1 == 1:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        data = value >> 1

        self.update_zero_and_negative_flags(data)

        if mode == AddressingMode.ACCUMULATOR:
            self.register_a = data
        else:
            self.memory.write(addr, data)

    def lda(self, mode: AddressingMode):
        addr = self.get_operand_address(mode)
        self.register_a = self.memory.read(addr)
        self.update_zero_and_negative_flags(self.register_a)

    def sta(self, mode: AddressingMode):
        addr = self.get_operand_address(mode)
        self.memory.write(addr, self.register_a)

    def inx(self):
        self.register_x += 1
        self.register_x &= 0xFF
        self.update_zero_and_negative_flags(self.register_x)

    def tax(self):
        self.register_x = self.register_a
        self.update_zero_and_negative_flags(self.register_x)

    def tay(self):
        self.register_y = self.register_a
        self.update_zero_and_negative_flags(self.register_y)

    def txa(self):
        self.register_a = self.register_x
        self.update_zero_and_negative_flags(self.register_a)

    def tya(self):
        self.register_a = self.register_y
        self.update_zero_and_negative_flags(self.register_a)

    def txs(self):
        self.stack_pointer = self.register_x

    def tsx(self):
        self.register_x = self.stack_pointer
        self.update_zero_and_negative_flags(self.register_x)

    def rol(self, mode: AddressingMode):
        addr = self.get_operand_address(mode)
        if mode != AddressingMode.ACCUMULATOR:
            value = self.memory.read(addr)
        else:
            value = copy(self.register_a)

        carry = self.get_flag(Flags.CARRY)
        self.clear_flag(Flags.CARRY)

        data = (value << 1) | carry

        if value >> 7 == 1:
            self.set_flag(Flags.CARRY)

        if mode == AddressingMode.ACCUMULATOR:
            self.register_a = data
        else:
            self.update_negative_flag(data)
            self.memory.write(addr, data)

    def ror(self, mode: AddressingMode) -> None:
        addr = self.get_operand_address(mode)
        if mode != AddressingMode.ACCUMULATOR:
            value = self.memory.read(addr)
        else:
            value = copy(self.register_a)

        old_carry = self.get_flag(Flags.CARRY)

        if value & 1 == 1:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        data = value >> 1
        if old_carry:
            data |= 0b10000000

        if mode == AddressingMode.ACCUMULATOR:
            self.register_a = data
        else:
            self.memory.write(addr, data)
            self.update_negative_flag(data)
