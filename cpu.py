import enum
import functools
from typing import Optional, Tuple
from instructions import AddressingModes, Instruction, load_opcodes
from logger import get_logger
from memory import Memory
from pydantic import validate_arguments
from utils import get_bytes_ordered

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
        # program counter is 16 bits
        self.program_counter = 0x0000
        # accumulator is 8 bits
        self.a = 0x00
        # x and y registers are 8 bits
        self.x = 0x00
        self.y = 0x00
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

        self._memory: Memory = memory
        self.memory = self._memory.memory
        self.opcodes = load_opcodes()

    def __str__(self):
        return f"CPU: A: {self.a}, X: {self.x}, Y: {self.y}, PC: {self.program_counter}, SP: {self.stack_pointer}, Status: {self.status}"

    # Flag operations
    def set_flag(self, flag: Flags):
        self.status |= 1 << flag.value

    def clear_flag(self, flag: Flags):
        self.status &= ~(1 << flag.value)

    def get_flag(self, flag: Flags) -> bool:
        return bool(self.status & (1 << flag.value))

    def push_stack(self, value):
        # Push a value onto the stack
        self._memory.write(0x0100 + self.stack_pointer, value)
        self.stack_pointer -= 1

    def pull_stack(self):
        # Read the value from the stack
        value, _ = self._memory.read(0x0100 + self.stack_pointer)

        # Increment the stack pointer
        self.stack_pointer += 1

        return value

    def pull_stack_word(self):
        # Read the value from the stack
        value, _ = self._memory.read_word(0x0100 + self.stack_pointer)

        # Increment the stack pointer
        self.stack_pointer += 2

        return value

    def push_stack_word(self, value):
        # Push a value onto the stack
        self._memory.write_word(0x0100 + self.stack_pointer, value)
        self.stack_pointer -= 2

    # TODO move this to Memory
    def get_memory_value(self, instruction: Instruction) -> Tuple[Optional[int], Optional[int]]:
        # -> Value,        Address if fetched from memory
        match (instruction.addressing_mode):
            case AddressingModes.IMPLIED:
                return None, None

            case AddressingModes.ACCUMULATOR:
                return self.a, None

            case AddressingModes.IMMEDIATE:
                argument_bytes = self._memory.program_rom[
                    self.program_counter + 1 : self.program_counter + instruction.no_bytes
                ]
                return get_bytes_ordered(argument_bytes), None

            case AddressingModes.ABSOLUTE:
                """
                In absolute addressing, the second byte of the instruction
                specifies the eight low order bits of the effective address
                while the third byte specifies the eight high order bits. Thus,
                the absolute addressing mode allows access to the entire
                65 K bytes of addressable memory.
                """
                # ADC $4400
                # 0x69 0x00 0x44
                # 0x69 = ADC
                # 0x00 = operand lower byte
                # 0x44 = operand higher byte
                argument_bytes = self._memory.program_rom[
                    self.program_counter + 1 : self.program_counter + instruction.no_bytes
                ]
                memory_address = get_bytes_ordered(argument_bytes)
                return self.memory[memory_address], memory_address

            case AddressingModes.X_INDEXED_ABSOLUTE:
                """
                This form of addressing is used in conjunction with the X index
                register. The effective address is formed by adding the contents
                of X to the address contained in the second and third bytes of
                the instruction. This mode allows the index register to contain
                the index or count value and the instruction to contain the base
                address. This type of indexing allows any location referencing
                and the index to modify multiple fields resulting in reduced
                coding and execution time.
                """
                argument_bytes = self._memory.program_rom[
                    self.program_counter + 1 : self.program_counter + instruction.no_bytes
                ]
                operand = get_bytes_ordered(argument_bytes)

                return self.memory[(operand + self.x)]

            case AddressingModes.Y_INDEXED_ABSOLUTE:
                """
                This form of addressing is used in conjunction with the Y index
                register. The effective address is formed by adding the contents
                of Y to the address contained in the second and third bytes of
                the instruction. This mode allows the index register to contain
                the index or count value and the instruction to contain the base
                address. This type of indexing allows any location referencing
                and the index to modify multiple fields resulting in reduced
                coding and execution time.
                """
                argument_bytes = self._memory.program_rom[
                    self.program_counter + 1 : self.program_counter + instruction.no_bytes
                ]
                operand = get_bytes_ordered(argument_bytes)

                return self.memory[(operand + self.y)]

            case AddressingModes.ABSOLUTE_INDIRECT:
                """
                The second byte of the instruction contains the low order eight
                bits of a memory location. The high order eight bits of that
                memory location is contained in the third byte of the instruction.
                The contents of the fully specified memory location is the low
                order byte of the effective address. The next memory location
                contains the high order byte of the effective address which is
                loaded into the sixteen bits of the program counter.
                """
                argument_bytes = self._memory.program_rom[
                    self.program_counter + 1 : self.program_counter + instruction.no_bytes
                ]
                operand = get_bytes_ordered(argument_bytes)

                return self.memory[self.memory[operand]]

            case AddressingModes.ZERO_PAGE:
                """
                The zero page instructions allow for shorter code and execution
                times by only fetching the second byte of the instruction and
                assuming a zero high address byte. Careful use of the zero page
                can result in significant increase in code efficiency.
                """
                argument_bytes = self._memory.program_rom[
                    self.program_counter + 1 : self.program_counter + instruction.no_bytes
                ]
                operand = get_bytes_ordered(argument_bytes)

                return self.memory[operand]

            case AddressingModes.X_INDEXED_ZERO_PAGE:
                """
                This form of addressing is used in conjunction with the X index
                register. The effective address is calculated by adding the second
                byte to the contents of the index register. Since this is a form
                of "Zero Page" addressing, the content of the second byte references
                a location in page zero. Additionally, due to the “Zero Page"
                addressing nature of this mode, no carry is added to the high order
                8 bits of memory and crossing of page boundaries does not occur.
                """
                argument_bytes = self._memory.program_rom[
                    self.program_counter + 1 : self.program_counter + instruction.no_bytes
                ]
                operand = get_bytes_ordered(argument_bytes)

                return self.memory[operand + self.x]

            case AddressingModes.Y_INDEXED_ZERO_PAGE:
                """
                This form of addressing is used in conjunction with the Y index
                register. The effective address is calculated by adding the second
                byte to the contents of the index register. Since this is a form of
                "Zero Page" addressing, the content of the second byte references a
                location in page zero. Additionally, due to the “Zero Page"
                addressing nature of this mode, no carry is added to the high
                order 8 bits of memory and crossing of page boundaries does not occur.
                """
                argument_bytes = self._memory.program_rom[
                    self.program_counter + 1 : self.program_counter + instruction.no_bytes
                ]
                operand = get_bytes_ordered(argument_bytes)

                return self.memory[operand + self.y]

            case AddressingModes.X_INDEXED_ZERO_PAGE_INDIRECT:
                """
                In indexed indirect addressing, the second byte of the instruction
                is added to the contents of the X index register, discarding the
                carry. The result of this addition points to a memory location on
                page zero whose contents is the low order eight bits of the effective
                address. The next memory location in page zero contains the high
                order eight bits of the effective address. Both memory locations
                specifying the high and low order bytes of the effective address
                must be in page zero.
                """
                argument_bytes = self._memory.program_rom[
                    self.program_counter + 1 : self.program_counter + instruction.no_bytes
                ]
                operand = get_bytes_ordered(argument_bytes)

                return self.memory[self.memory[operand + self.x]]

            case AddressingModes.ZERO_PAGE_INDIRECT_Y_INDEXED:
                """
                In indirect indexed addressing, the second byte of the instruction
                points to a memory location in page zero. The contents of this
                memory location is added to the contents of the Y index register,
                the result being the low order eight bits of the effective address.
                The carry from this addition is added to the contents of the next
                page zero memory location, the result being the high order eight
                bits of the effective address.
                """
                argument_bytes = self._memory.program_rom[
                    self.program_counter + 1 : self.program_counter + instruction.no_bytes
                ]
                operand = get_bytes_ordered(argument_bytes)

                return self.memory[self.memory[operand] + self.y]

            case AddressingModes.RELATIVE:
                argument_bytes = self._memory.program_rom[
                    self.program_counter + 1 : self.program_counter + instruction.no_bytes
                ]
                operand = get_bytes_ordered(argument_bytes)

                return self.memory[operand]

            case _:
                logger.error(f"#FUCK {opcode.addressing_mode}")
                raise SystemError

    def step(self):
        logger.debug(self)
        opcode_hex = self._memory.program_rom[self.program_counter]
        instruction = self.opcodes[opcode_hex]

        self.instruction = instruction
        logger.debug(f"{instruction}")

        if not hasattr(self, instruction.opcode.value.upper()):
            logger.error(f"FUCK {instruction}")
            raise SystemError

        getattr(self, instruction.opcode)(instruction=instruction)
        logger.debug(self)

    def execute(self):
        while self.program_counter < len(self._memory.program_rom):
            self.step()

    def ADC(self, instruction: Instruction):
        # Add Memory to Accumulator with Carry
        # A + M + C -> A, C
        value, _ = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Perform the addition
        sum_value = self.a + value + self.get_flag(Flags.CARRY)

        # Set the Carry flag if necessary
        if sum_value > 0xFF:  #
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Update the Zero flag
        if (sum_value & 0xFF) == 0:  #
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Update the Overflow flag
        # If the 7th bit is set and the 7th bit is not set
        if (self.a ^ value) & 0x80 == 0 and (self.a ^ sum_value) & 0x80 != 0:
            self.set_flag(Flags.OVERFLOW)
        else:
            self.clear_flag(Flags.OVERFLOW)

        # Update the Negative flag
        if sum_value & 0x80 != 0:  # If the 7th bit is set
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Store the result in the accumulator
        self.a = sum_value & 0xFF  # Keep it 8-bit

    def AND(self, instruction: Instruction):
        # AND Memory with Accumulator
        # A AND M -> A
        value, _ = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

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

    def ASL(self, instruction: Instruction):
        # Arithmetic Shift Left
        # C <- [76543210] <- 0
        value, memory_address = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Set the Carry flag if necessary
        if value & 0x80 != 0:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Shift the value left
        value, _ = (value << 1) & 0xFF

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
        self._memory.write(memory_address, value)

    def BCC(self, instruction: Instruction):
        # Branch on Carry Clear
        # branch on C = 0

        value, _ = self.get_memory_value(instruction)

        if self.get_flag(Flags.CARRY) == 0:
            self.program_counter += value
        else:
            self.program_counter += instruction.no_bytes

    def BCS(self, instruction: Instruction):
        # Branch on Carry Set
        # branch on C = 1

        value, _ = self.get_memory_value(instruction)

        if self.get_flag(Flags.CARRY) == 1:
            self.program_counter += value
        else:
            self.program_counter += instruction.no_bytes

    def BEQ(self, instruction: Instruction):
        # Branch on Result Zero
        # branch on Z = 1

        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        if self.get_flag(Flags.ZERO) == 1:
            self.program_counter += value
        else:
            self.program_counter += instruction.no_bytes

    def BIT(self, instruction: Instruction):
        # Test Bits in Memory with Accumulator
        # A AND M, M7 -> N, M6 -> V

        value, _ = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

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

    def BMI(self, instruction: Instruction):
        # Branch on Result Minus
        # branch on N = 1
        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        if self.get_flag(Flags.NEGATIVE) == 1:
            self.program_counter += value
        else:
            self.program_counter += instruction.no_bytes

    def BNE(self, instruction: Instruction):
        # Branch on Result not Zero
        # branch on Z = 0

        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        if self.get_flag(Flags.ZERO) == 0:
            self.program_counter += value
        else:
            self.program_counter += instruction.no_bytes

    def BPL(self, instruction: Instruction):
        # Branch on Result Plus
        # branch on N = 0
        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        if self.get_flag(Flags.NEGATIVE) == 0:
            self.program_counter += value
        else:
            self.program_counter += instruction.no_bytes

    # TODO look into this
    def BRK(self, instruction: Instruction):
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
        self.program_counter = self._memory.read_word(0xFFFE)

    def BVC(self, instruction: Instruction):
        # Branch on Overflow Clear
        # branch on V = 0
        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        if self.get_flag(Flags.OVERFLOW) == 0:
            self.program_counter += value
        else:
            self.program_counter += instruction.no_bytes

    def BVS(self, instruction: Instruction):
        # Branch on Overflow Set
        # branch on V = 1
        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        if self.get_flag(Flags.OVERFLOW) == 1:
            self.program_counter += value
        else:
            self.program_counter += instruction.no_bytes

    def CLC(self, instruction: Optional[Instruction] = None):
        # Clear Carry Flag
        # 0 -> C
        self.clear_flag(Flags.CARRY)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

    def CLD(self, instruction: Optional[Instruction] = None):
        # Clear Decimal Mode
        # 0 -> D

        self.clear_flag(Flags.DECIMAL)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def CLI(self, instruction: Optional[Instruction] = None):
        # Clear Interrupt Disable Bit
        # 0 -> I

        self.clear_flag(Flags.INTERRUPT_DISABLE)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def CLV(self, instruction: Optional[Instruction] = None):
        # Clear Overflow Flag
        # 0 -> V

        self.clear_flag(Flags.OVERFLOW)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def CMP(self, instruction: Instruction):
        # Compare Memory and Accumulator
        # A - M
        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

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

    def CPX(self, instruction: Instruction):
        # Compare Memory and Index X
        # X - M
        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

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

    def CPY(self, instruction: Instruction):
        # Compare Memory and Index Y
        # Y - M
        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes
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

    def DEC(self, instruction: Instruction):
        # Decrement Memory by One
        # M - 1 -> M
        # Fetch the value from memory based on the addressing mode
        value, memory_address = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

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
        self._memory.write(memory_address, value)

    def DEX(self, instruction: Optional[Instruction] = None):
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
        self.program_counter += instruction.no_bytes

    def DEY(self, instruction: Optional[Instruction] = None):
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
        self.program_counter += instruction.no_bytes

    def EOR(self, instruction: Instruction):
        # Exclusive-OR Memory with Accumulator
        # A EOR M -> A
        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes
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

    def INC(self, instruction: Instruction):
        # Increment Memory by One
        # M + 1 -> M
        # Fetch the value from memory based on the addressing mode
        value, memory_address = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

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
        self._memory.write(memory_address, value)

    def INX(self, instruction: Optional[Instruction] = None):
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
        self.program_counter += instruction.no_bytes

    def INY(self, instruction: Optional[Instruction] = None):
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
        self.program_counter += instruction.no_bytes

    def JMP(self, instruction: Instruction):
        # Jump to New Location
        # (PC + 1) -> PCL
        # (PC + 2) -> PCH
        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        # Set the program counter to the address
        self.program_counter = value

    def JSR(self, instruction: Instruction):
        # Jump to New Location Saving Return Address
        # Push (PC + 2), (PC + 1) on stack
        # (PC + 1) -> PCL
        # (PC + 2) -> PCH
        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        # Push the return address onto the stack
        self.push_stack(self.program_counter + 2)
        self.push_stack((self.program_counter + 2) >> 8)

        # Set the program counter to the address
        self.program_counter = value

    def LDA(self, instruction: Instruction):
        # Load Accumulator with Memory
        # M -> A
        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes
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

    def LDX(self, instruction: Instruction):
        # Load Index X with Memory
        # M -> X
        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

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

    def LDY(self, instruction: Instruction):
        # Load Index Y with Memory
        # M -> Y
        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes
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

    def LSR(self, instruction: Instruction):
        # Logical Shift Right One Bit (Memory or Accumulator)
        # 0 -> [7][6][5][4][3][2][1][0] -> C
        # M/2 -> [7][6][5][4][3][2][1][0]
        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes
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
        self._memory.write(memory_address, value)

    def NOP(self, instruction: Optional[Instruction] = None):
        # No Operation
        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def ORA(self, instruction: Instruction):
        # OR Memory with Accumulator
        # A OR M -> A
        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes
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

    def PHA(self, instruction: Optional[Instruction] = None):
        # Push Accumulator on Stack
        # Push A on stack

        # Push the accumulator onto the stack
        self.push_stack(self.a)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def PHP(self, instruction: Optional[Instruction] = None):
        # Push Processor Status on Stack
        # Push P on stack

        # Push the processor status onto the stack
        self.push_stack(self.flags)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def PLA(self, instruction: Optional[Instruction] = None):
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
        self.program_counter += instruction.no_bytes

    def PLP(self, instruction: Optional[Instruction] = None):
        # Pull Processor Status from Stack
        # Pull P from stack

        # Pull the processor status from the stack
        self.flags = self.pull_stack()

        # Increment the program counter
        self.program_counter += 1

    def ROL(self, instruction: Instruction):
        # Rotate One Bit Left (Memory or Accumulator)
        # C <- [7][6][5][4][3][2][1][0] <- C
        # M <- [6][5][4][3][2][1][0][C]
        # Fetch the value from memory based on the addressing mode
        value, memory_address = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

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
        self.memory.write(memory_address, value)

    def ROR(self, instruction: Instruction):
        # Rotate One Bit Right (Memory or Accumulator)
        # C -> [7][6][5][4][3][2][1][0] -> C
        # M -> [C][7][6][5][4][3][2][1]
        # Fetch the value from memory based on the addressing mode
        value, memory_address = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes
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
        self._memory.write(memory_address, value)

    def RTI(self, instruction: Optional[Instruction] = None):
        # Return from Interrupt
        # Pull P from stack, PC from stack

        # Pull the processor status from the stack
        self.flags = self.pull_stack()

        # Pull the program counter from the stack
        self.program_counter = self.pull_stack_word()

    def RTS(self, instruction: Optional[Instruction] = None):
        # Return from Subroutine
        # Pull PC from stack, PC+1 -> PC

        # Pull the program counter from the stack
        self.program_counter = self.pull_stack_word()

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def SBC(self, instruction: Instruction):
        # Subtract Memory from Accumulator with Borrow
        # A - M - C -> A
        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes
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

    def SEC(self, instruction: Optional[Instruction] = None):
        # Set Carry Flag
        # 1 -> C

        # Set the Carry flag
        self.set_flag(Flags.CARRY)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def SED(self, instruction: Optional[Instruction] = None):
        # Set Decimal Flag
        # 1 -> D

        # Set the Decimal flag
        self.set_flag(Flags.DECIMAL)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def SEI(self, instruction: Optional[Instruction] = None):
        # Set Interrupt Disable Status
        # 1 -> I

        # Set the Interrupt flag
        self.set_flag(Flags.INTERRUPT_DISABLE)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def STA(self, instruction: Instruction):
        # Store Accumulator in Memory
        # A -> M

        # Fetch the value from memory based on the addressing mode
        _, memory_address = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Write the accumulator to memory based on the addressing mode
        self._memory.write(memory_address, self.a)

    def STX(self, instruction: Instruction):
        # Store Index X in Memory
        # X -> M
        # Fetch the value from memory based on the addressing mode
        value, memory_address = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes
        # Write the X register to memory based on the addressing mode
        self._memory.write(memory_address, self.x)

    def STY(self, instruction: Instruction):
        # Store Index Y in Memory
        # Y -> M
        # Fetch the value from memory based on the addressing mode
        value, _ = self.get_memory_value(instruction)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Write the Y register to memory based on the addressing mode
        self.set_memory_value(value, self.y)

    def TAX(self, instruction: Optional[Instruction] = None):
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
        self.program_counter += instruction.no_bytes

    def TAY(self, instruction: Optional[Instruction] = None):
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
        self.program_counter += instruction.no_bytes

    def TSX(self, instruction: Optional[Instruction] = None):
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
        self.program_counter += instruction.no_bytes

    def TXA(self, instruction: Optional[Instruction] = None):
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
        self.program_counter += instruction.no_bytes

    def TXS(self, instruction: Optional[Instruction] = None):
        # Transfer Index X to Stack Pointer
        # X -> SP

        # Copy the X register to the stack pointer
        self.stack_pointer = self.x

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def TYA(self, instruction: Optional[Instruction] = None):
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
        self.program_counter += instruction.no_bytes
