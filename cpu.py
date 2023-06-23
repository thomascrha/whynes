import enum
from instructions import AddressingMode, Instructions
from logger import get_logger
from memory import Memory

logger = get_logger(__name__)


class Flags(enum.Enum):
    CARRY = 0
    ZERO = 1
    INTERRUPT_DISABLE = 2
    DECIMAL = 3
    BREAK = 4
    UNUSED = 5
    OVERFLOW = 6
    NEGATIVE = 7


class CPU:
    def __init__(self, memory: Memory):
        # registers
        # accumulator is 8 bits
        self.a = 0x00
        # x and y registers are 8 bits
        self.x = 0x00
        self.y = 0x00
        # program counter is 16 bits but the memory is 64K
        self.program_counter = 0x0000
        # stack pointer is 8 bits but the stack is 256 bytes
        self.stack_pointer = 0xFF
        # stats register is 8 bits where is bit is repersented by the Flags enum
        # 0x00 = 0b00100000
        # 0x01 = 0b00100001
        # 0x02 = 0b00100010
        # 0x03 = 0b00100011
        # 0x04 = 0b00100100
        # 0x05 = 0b00100101
        # 0x06 = 0b00100110
        # 0x07 = 0b00100111
        self.status = 0x00

        self.memory = memory

    # Flag operations
    def set_flag(self, flag: Flags):
        self.status |= 1 << flag.value

    def clear_flag(self, flag: Flags):
        self.status &= ~(1 << flag.value)

    def get_flag(self, flag: Flags) -> bool:
        return bool(self.status & (1 << flag.value))

    def push_stack(self, value):
        # Push a value onto the stack
        self.memory.write(0x0100 + self.stack_pointer, value)
        self.stack_pointer -= 1

    def pull_stack(self):
        # Read the value from the stack
        value = self.memory.read(0x0100 + self.stack_pointer)

        # Increment the stack pointer
        self.stack_pointer += 1

        return value

    def pull_stack_word(self):
        # Read the value from the stack
        value = self.memory.read_word(0x0100 + self.stack_pointer)

        # Increment the stack pointer
        self.stack_pointer += 2

        return value

    def push_stack_word(self):
        # Push a value onto the stack
        self.memory.write_word(0x0100 + self.stack_pointer, value)
        self.stack_pointer -= 2

    def get_operand_value(self, addressing_mode):
        if addressing_mode == AddressingMode.IMMEDIATE:
            return self.memory.read(self.program_counter)
        elif addressing_mode == AddressingMode.ACCUMULATOR:
            return self.a
        else:
            address = self.get_operand_address(addressing_mode)
            return self.memory.read(address)

    def get_addressing_mode(self, opcode):
        return opcode.value.addressing_mode

    def get_operand_address(self, addressing_mode):
        if addressing_mode == AddressingMode.IMPLIED or addressing_mode == AddressingMode.ACCUMULATOR:
            return None
        elif addressing_mode == AddressingMode.IMMEDIATE:
            return self.program_counter + 1
        elif addressing_mode == AddressingMode.ZERO_PAGE:
            return self.memory.read(self.program_counter + 1)
        elif addressing_mode == AddressingMode.ZERO_PAGE_X:
            zero_page_address = self.memory.read(self.program_counter + 1)
            return (zero_page_address + self.x) & 0xFF
        elif addressing_mode == AddressingMode.ZERO_PAGE_Y:
            zero_page_address = self.memory.read(self.program_counter + 1)
            return (zero_page_address + self.y) & 0xFF
        elif addressing_mode == AddressingMode.ABSOLUTE:
            low_byte = self.memory.read(self.program_counter + 1)
            high_byte = self.memory.read(self.program_counter + 2)
            return (high_byte << 8) | low_byte
        elif addressing_mode == AddressingMode.ABSOLUTE_X:
            low_byte = self.memory.read(self.program_counter + 1)
            high_byte = self.memory.read(self.program_counter + 2)
            return ((high_byte << 8) | low_byte) + self.x
        elif addressing_mode == AddressingMode.ABSOLUTE_Y:
            low_byte = self.memory.read(self.program_counter + 1)
            high_byte = self.memory.read(self.program_counter + 2)
            return ((high_byte << 8) | low_byte) + self.y
        elif addressing_mode == AddressingMode.INDIRECT:
            low_byte = self.memory.read(self.program_counter + 1)
            high_byte = self.memory.read(self.program_counter + 2)
            address = (high_byte << 8) | low_byte
            # Simulate 6502 bug where indirect jump doesn't cross page boundary correctly
            if low_byte == 0xFF:
                return (self.memory.read(address & 0xFF00) << 8) | self.memory.read(address)
            else:
                return (self.memory.read(address + 1) << 8) | self.memory.read(address)
        elif addressing_mode == AddressingMode.X_INDEXED_INDIRECT:
            zero_page_address = (self.memory.read(self.program_counter + 1) + self.x) & 0xFF
            low_byte = self.memory.read(zero_page_address)
            high_byte = self.memory.read((zero_page_address + 1) & 0xFF)
            return (high_byte << 8) | low_byte
        elif addressing_mode == AddressingMode.INDIRECT_Y_INDEXED:
            zero_page_address = self.memory.read(self.program_counter + 1)
            low_byte = self.memory.read(zero_page_address)
            high_byte = self.memory.read((zero_page_address + 1) & 0xFF)
            return ((high_byte << 8) | low_byte) + self.y
        elif addressing_mode == AddressingMode.RELATIVE:
            offset = self.memory.read(self.program_counter + 1)
            if offset & 0x80:
                return self.program_counter + offset - 0x100
            else:
                return self.program_counter + offset

    def set_operand_address(self, addressing_mode, value):
        if addressing_mode == AddressingMode.ZERO_PAGE:
            self.memory.write(self.program_counter + 1, value)
        elif addressing_mode == AddressingMode.ZERO_PAGE_X:
            zero_page_address = self.memory.read(self.program_counter + 1)
            self.memory.write((zero_page_address + self.x) & 0xFF, value)
        elif addressing_mode == AddressingMode.ZERO_PAGE_Y:
            zero_page_address = self.memory.read(self.program_counter + 1)
            self.memory.write((zero_page_address + self.y) & 0xFF, value)
        elif addressing_mode == AddressingMode.ABSOLUTE:
            low_byte = self.memory.read(self.program_counter + 1)
            high_byte = self.memory.read(self.program_counter + 2)
            address = (high_byte << 8) | low_byte
            self.memory.write(address, value)
        elif addressing_mode == AddressingMode.ABSOLUTE_X:
            low_byte = self.memory.read(self.program_counter + 1)
            high_byte = self.memory.read(self.program_counter + 2)
            address = ((high_byte << 8) | low_byte) + self.x
            self.memory.write(address, value)
        elif addressing_mode == AddressingMode.ABSOLUTE_Y:
            low_byte = self.memory.read(self.program_counter + 1)
            high_byte = self.memory.read(self.program_counter + 2)
            address = ((high_byte << 8) | low_byte) + self.y
            self.memory.write(address, value)
        elif addressing_mode == AddressingMode.INDIRECT:
            low_byte = self.memory.read(self.program_counter + 1)
            high_byte = self.memory.read(self.program_counter + 2)
            address = (high_byte << 8) | low_byte
            # Simulate 6502 bug where indirect jump doesn't cross page boundary correctly
            if low_byte == 0xFF:
                self.memory.write(address & 0xFF00, (value >> 8) & 0xFF)
                self.memory.write(address, value & 0xFF)
            else:
                self.memory.write(address + 1, (value >> 8) & 0xFF)
                self.memory.write(address, value & 0xFF)
        elif addressing_mode == AddressingMode.X_INDEXED_INDIRECT:
            zero_page_address = (self.memory.read(self.program_counter + 1) + self.x) & 0xFF
            low_byte = self.memory.read(zero_page_address)
            high_byte = self.memory.read((zero_page_address + 1) & 0xFF)
            address = (high_byte << 8) | low_byte
            self.memory.write(address, value)
        elif addressing_mode == AddressingMode.INDIRECT_Y_INDEXED:
            zero_page_address = self.memory.read(self.program_counter + 1)
            low_byte = self.memory.read(zero_page_address)
            high_byte = self.memory.read((zero_page_address + 1) & 0xFF)
            address = ((high_byte << 8) | low_byte) + self.y
            self.memory.write(address, value)

    def decompile_program(self):
        while self.program_counter < self.memory.cartridge.program_rom_size:
            logger.debug(
                f"PC: {hex(self.program_counter)}"
                f" SP: {hex(self.stack_pointer)}"
                f" A: {hex(self.a)}"
                f" X: {hex(self.x)}"
                f" Y: {hex(self.y)}"
                f" Status: {hex(self.status)}"
            )
            opcode_hex = self.memory.program_rom[self.program_counter]
            opcode = Instructions.get_opcode(opcode_hex)
            operand = None
            if opcode.value.argument_length > 0:
                operand = self.memory.program_rom[self.program_counter + opcode.value.argument_length]

            if hasattr(self, opcode.name):
                logger.info(f"{opcode.name} ({operand if operand else ''})")
                if operand:
                    getattr(self, opcode.name)(operand)
                else:
                    getattr(self, opcode.name)()
            else:
                logger.error(f"FUCK {opcode}")
                raise SystemError

    def ADC(self, operand):
        # Add Memory to Accumulator with Carry
        # A + M + C -> A, C

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Perform the addition
        sum_value = self.a + value + self.get_flag(Flags.CARRY)

        # Set the Carry flag if necessary
        if sum_value > 0xFF:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Update the Zero flag
        if (sum_value & 0xFF) == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Overflow flag
        if (self.a ^ value) & 0x80 == 0 and (self.a ^ sum_value) & 0x80 != 0:
            self.set_flag(Flags.OVERFLOW)
        else:
            self.clear_flag(Flags.OVERFLOW)

        # Update the Negative flag
        if sum_value & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Store the result in the accumulator
        self.a = sum_value & 0xFF

        # Increment the program counter
        self.program_counter += 1

    def AND(self, operand):
        # AND Memory with Accumulator
        # A AND M -> A

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Perform the AND operation
        self.a &= value

        # Update the Zero flag
        if self.a == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if self.a & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def ASL(self, operand):
        # Arithmetic Shift Left
        # C <- [76543210] <- 0

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Set the Carry flag if necessary
        if value & 0x80 != 0:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Shift the value left
        value = (value << 1) & 0xFF

        # Update the Zero flag
        if value == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if value & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Store the result in memory
        self.memory.write(operand, value)

        # Increment the program counter
        self.program_counter += 1

    def BCC(self, operand):
        # Branch on Carry Clear
        # branch on C = 0

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        if self.get_flag(Flags.CARRY) == 0:
            self.program_counter += value
        else:
            self.program_counter += 1

    def BCS(self, operand):
        # Branch on Carry Set
        # branch on C = 1

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        if self.get_flag(Flags.CARRY) == 1:
            self.program_counter += value
        else:
            self.program_counter += 1

    def BEQ(self, operand):
        # Branch on Result Zero
        # branch on Z = 1

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        if self.get_flag(Flags.ZERO) == 1:
            self.program_counter += value
        else:
            self.program_counter += 1

    def BIT(self, operand):
        # Test Bits in Memory with Accumulator
        # A AND M, M7 -> N, M6 -> V

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Perform the AND operation
        self.a &= value

        # Update the Zero flag
        if self.a == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if value & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Update the Overflow flag
        if value & 0x40 != 0:
            self.set_flag(Flags.OVERFLOW)
        else:
            self.clear_flag(Flags.OVERFLOW)

        # Increment the program counter
        self.program_counter += 1

    def BMI(self, operand):
        # Branch on Result Minus
        # branch on N = 1

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        if self.get_flag(Flags.NEGATIVE) == 1:
            self.program_counter += value
        else:
            self.program_counter += 1

    def BNE(self, operand):
        # Branch on Result not Zero
        # branch on Z = 0

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        if self.get_flag(Flags.ZERO) == 0:
            self.program_counter += value
        else:
            self.program_counter += 1

    def BPL(self, operand):
        # Branch on Result Plus
        # branch on N = 0

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        if self.get_flag(Flags.NEGATIVE) == 0:
            self.program_counter += value
        else:
            self.program_counter += 1

    def BRK(self):
        # Force Break
        # interrupt, push PC+2, push SR

        # Push the program counter + 2 onto the stack
        self.push_stack((self.program_counter + 2) >> 8)
        self.push_stack((self.program_counter + 2) & 0xFF)

        # Push the status register onto the stack
        self.push_stack(self.status)

        # Set the Interrupt Disable flag
        self.set_flag(Flags.INTERRUPT_DISABLE)

        # Fetch the interrupt vector from memory
        self.program_counter = self.memory.read_word(0xFFFE)

    def BVC(self, operand):
        # Branch on Overflow Clear
        # branch on V = 0

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        if self.get_flag(Flags.OVERFLOW) == 0:
            self.program_counter += value
        else:
            self.program_counter += 1

    def BVS(self, operand):
        # Branch on Overflow Set
        # branch on V = 1

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        if self.get_flag(Flags.OVERFLOW) == 1:
            self.program_counter += value
        else:
            self.program_counter += 1

    def CLC(self):
        # Clear Carry Flag
        # 0 -> C

        self.clear_flag(Flags.CARRY)

        # Increment the program counter
        self.program_counter += 1

    def CLD(self):
        # Clear Decimal Mode
        # 0 -> D

        self.clear_flag(Flags.DECIMAL)

        # Increment the program counter
        self.program_counter += 1

    def CLI(self):
        # Clear Interrupt Disable Bit
        # 0 -> I

        self.clear_flag(Flags.INTERRUPT_DISABLE)

        # Increment the program counter
        self.program_counter += 1

    def CLV(self):
        # Clear Overflow Flag
        # 0 -> V

        self.clear_flag(Flags.OVERFLOW)

        # Increment the program counter
        self.program_counter += 1

    def CMP(self, operand):
        # Compare Memory and Accumulator
        # A - M

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Perform the subtraction
        result = self.a - value

        # Update the Carry flag
        if result >= 0:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Update the Zero flag
        if result == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if result & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def CPX(self, operand):
        # Compare Memory and Index X
        # X - M

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Perform the subtraction
        result = self.x - value

        # Update the Carry flag
        if result >= 0:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Update the Zero flag
        if result == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if result & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def CPY(self, operand):
        # Compare Memory and Index Y
        # Y - M

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Perform the subtraction
        result = self.y - value

        # Update the Carry flag
        if result >= 0:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Update the Zero flag
        if result == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if result & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def DEC(self, operand):
        # Decrement Memory by One
        # M - 1 -> M

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Decrement the value
        value -= 1

        # Update the Zero flag
        if value == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if value & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Write the value back to memory
        self.set_operand_value(operand, value)

        # Increment the program counter
        self.program_counter += 1

    def DEX(self):
        # Decrement Index X by One
        # X - 1 -> X

        # Decrement the value
        self.x -= 1

        # Update the Zero flag
        if self.x == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if self.x & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def DEY(self):
        # Decrement Index Y by One
        # Y - 1 -> Y

        # Decrement the value
        self.y -= 1

        # Update the Zero flag
        if self.y == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag by checking the sign bit of the result
        if self.y & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def EOR(self, operand):
        # Exclusive-OR Memory with Accumulator
        # A EOR M -> A

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Perform the XOR operation
        self.a ^= value

        # Update the Zero flag
        if self.a == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag by checking the sign bit of the result
        if self.a & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def INC(self, operand):
        # Increment Memory by One
        # M + 1 -> M

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Increment the value
        value += 1

        # Update the Zero flag
        if value == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if value & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Write the value back to memory
        self.set_operand_value(operand, value)

        # Increment the program counter
        self.program_counter += 1

    def INX(self):
        # Increment Index X by One
        # X + 1 -> X

        # Increment the value
        self.x += 1

        # Update the Zero flag
        if self.x == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if self.x & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def INY(self):
        # Increment Index Y by One
        # Y + 1 -> Y

        # Increment the value
        self.y += 1

        # Update the Zero flag
        if self.y == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if self.y & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def JMP(self, operand):
        # Jump to New Location
        # (PC + 1) -> PCL
        # (PC + 2) -> PCH

        # Fetch the address from memory based on the addressing mode
        address = self.get_operand_address(operand)

        # Set the program counter to the address
        self.program_counter = address

    def JSR(self, operand):
        # Jump to New Location Saving Return Address
        # Push (PC + 2), (PC + 1) on stack
        # (PC + 1) -> PCL
        # (PC + 2) -> PCH

        # Fetch the address from memory based on the addressing mode
        address = self.get_operand_address(operand)

        # Push the return address onto the stack
        self.push_stack(self.program_counter + 2)
        self.push_stack((self.program_counter + 2) >> 8)

        # Set the program counter to the address
        self.program_counter = address

    def LDA(self, operand):
        # Load Accumulator with Memory
        # M -> A

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Load the value into the accumulator
        self.a = value

        # Update the Zero flag
        if self.a == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag by checking the sign bit of the result
        if self.a & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def LDX(self, operand):
        # Load Index X with Memory
        # M -> X

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Load the value into the index register
        self.x = value

        # Update the Zero flag
        if self.x == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag by checking the sign bit of the result
        if self.x & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def LDY(self, operand):
        # Load Index Y with Memory
        # M -> Y

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Load the value into the index register
        self.y = value

        # Update the Zero flag
        if self.y == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag by checking the sign bit of the result
        if self.y & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def LSR(self, operand):
        # Logical Shift Right One Bit (Memory or Accumulator)
        # 0 -> [7][6][5][4][3][2][1][0] -> C
        # M/2 -> [7][6][5][4][3][2][1][0]

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Update the Carry flag by checking the least significant bit of the value
        if value & 0x01 != 0:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Shift the value right by one bit
        value >>= 1

        # Update the Zero flag
        if value == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if value & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Write the value back to memory
        self.set_operand_value(operand, value)

        # Increment the program counter
        self.program_counter += 1

    def NOP(self):
        # No Operation
        # Increment the program counter
        self.program_counter += 1

    def ORA(self, operand):
        # OR Memory with Accumulator
        # A OR M -> A

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Perform the OR operation
        self.a |= value

        # Update the Zero flag
        if self.a == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag by checking the sign bit of the result
        if self.a & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def PHA(self):
        # Push Accumulator on Stack
        # Push A on stack

        # Push the accumulator onto the stack
        self.push_stack(self.a)

        # Increment the program counter
        self.program_counter += 1

    def PHP(self):
        # Push Processor Status on Stack
        # Push P on stack

        # Push the processor status onto the stack
        self.push_stack(self.flags)

        # Increment the program counter
        self.program_counter += 1

    def PLA(self):
        # Pull Accumulator from Stack
        # Pull A from stack

        # Pull the accumulator from the stack
        self.a = self.pull_stack()

        # Update the Zero flag
        if self.a == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag by checking the sign bit of the result
        if self.a & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def PLP(self):
        # Pull Processor Status from Stack
        # Pull P from stack

        # Pull the processor status from the stack
        self.flags = self.pull_stack()

        # Increment the program counter
        self.program_counter += 1

    def ROL(self, operand):
        # Rotate One Bit Left (Memory or Accumulator)
        # C <- [7][6][5][4][3][2][1][0] <- C
        # M <- [6][5][4][3][2][1][0][C]

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Save the current value of the Carry flag
        carry = self.get_flag(Flags.CARRY)

        # Update the Carry flag by checking the most significant bit of the value
        if value & 0x80 != 0:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Shift the value left by one bit
        value <<= 1

        # Set the least significant bit of the value to the previous value of the Carry flag
        if carry:
            value |= 0x01

        # Update the Zero flag
        if value == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if value & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Write the value back to memory
        self.set_operand_value(operand, value)

        # Increment the program counter
        self.program_counter += 1

    def ROR(self, operand):
        # Rotate One Bit Right (Memory or Accumulator)
        # C -> [7][6][5][4][3][2][1][0] -> C
        # M -> [C][7][6][5][4][3][2][1]

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Save the current value of the Carry flag
        carry = self.get_flag(Flags.CARRY)

        # Update the Carry flag by checking the least significant bit of the value
        if value & 0x01 != 0:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Shift the value right by one bit
        value >>= 1

        # Set the most significant bit of the value to the previous value of the Carry flag
        if carry:
            value |= 0x80

        # Update the Zero flag
        if value == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if value & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Write the value back to memory
        self.set_operand_value(operand, value)

        # Increment the program counter
        self.program_counter += 1

    def RTI(self):
        # Return from Interrupt
        # Pull P from stack, PC from stack

        # Pull the processor status from the stack
        self.flags = self.pull_stack()

        # Pull the program counter from the stack
        self.program_counter = self.pull_stack_word()

    def RTS(self):
        # Return from Subroutine
        # Pull PC from stack, PC+1 -> PC

        # Pull the program counter from the stack
        self.program_counter = self.pull_stack_word()

        # Increment the program counter
        self.program_counter += 1

    def SBC(self, operand):
        # Subtract Memory from Accumulator with Borrow
        # A - M - C -> A

        # Fetch the value from memory based on the addressing mode
        value = self.get_operand_value(operand)

        # Perform the subtraction
        result = self.a - value - (1 - self.get_flag(Flags.CARRY))

        # Update the Carry flag
        if result < 0:
            self.clear_flag(Flags.CARRY)
        else:
            self.set_flag(Flags.CARRY)

        # Update the Overflow flag
        if (self.a ^ result) & (value ^ result) & 0x80 != 0:
            self.set_flag(Flags.OVERFLOW)
        else:
            self.clear_flag(Flags.OVERFLOW)

        # Update the Zero flag
        if result == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if result & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Write the result back to the accumulator
        self.a = result & 0xFF

        # Increment the program counter
        self.program_counter += 1

    def SEC(self):
        # Set Carry Flag
        # 1 -> C

        # Set the Carry flag
        self.set_flag(Flags.CARRY)

        # Increment the program counter
        self.program_counter += 1

    def SED(self):
        # Set Decimal Flag
        # 1 -> D

        # Set the Decimal flag
        self.set_flag(Flags.DECIMAL)

        # Increment the program counter
        self.program_counter += 1

    def SEI(self):
        # Set Interrupt Disable Status
        # 1 -> I

        # Set the Interrupt flag
        self.set_flag(Flags.INTERRUPT_DISABLE)

        # Increment the program counter
        self.program_counter += 1

    def STA(self, operand):
        # Store Accumulator in Memory
        # A -> M

        # Write the accumulator to memory based on the addressing mode
        self.set_operand_value(operand, self.a)

        # Increment the program counter
        self.program_counter += 1

    def STX(self, operand):
        # Store Index X in Memory
        # X -> M

        # Write the X register to memory based on the addressing mode
        self.set_operand_value(operand, self.x)

        # Increment the program counter
        self.program_counter += 1

    def STY(self, operand):
        # Store Index Y in Memory
        # Y -> M

        # Write the Y register to memory based on the addressing mode
        self.set_operand_value(operand, self.y)

        # Increment the program counter
        self.program_counter += 1

    def TAX(self):
        # Transfer Accumulator to Index X
        # A -> X

        # Copy the accumulator to the X register
        self.x = self.a

        # Update the Zero flag
        if self.x == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if self.x & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def TAY(self, operand):
        # Transfer Accumulator to Index Y
        # A -> Y

        # Copy the accumulator to the Y register
        self.y = self.a

        # Update the Zero flag
        if self.y == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if self.y & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def TSX(self):
        # Transfer Stack Pointer to Index X
        # SP -> X

        # Copy the stack pointer to the X register
        self.x = self.stack_pointer

        # Update the Zero flag
        if self.x == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if self.x & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def TXA(self):
        # Transfer Index X to Accumulator
        # X -> A

        # Copy the X register to the accumulator
        self.a = self.x

        # Update the Zero flag
        if self.a == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if self.a & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def TXS(self):
        # Transfer Index X to Stack Pointer
        # X -> SP

        # Copy the X register to the stack pointer
        self.stack_pointer = self.x

        # Increment the program counter
        self.program_counter += 1

    def TYA(self):
        # Transfer Index Y to Accumulator
        # Y -> A

        # Copy the Y register to the accumulator
        self.a = self.y

        # Update the Zero flag
        if self.a == 0:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Negative flag
        if self.a & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1
