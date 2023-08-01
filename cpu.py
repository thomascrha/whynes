import enum
from typing import Optional
from constants import PROGRAM_ROM_START
from instructions import AddressingModes, Instruction, load_opcodes
from logger import get_logger
from memory import Memory

logger = get_logger(__name__)


class Flag(enum.Flag):
    NULL = 0
    CARRY = 1
    ZERO = 2
    INTERRUPT_DISABLE = 4
    DECIMAL = 8
    BREAK = 16
    UNUSED = 32
    OVERFLOW = 64
    NEGATIVE = 128


class CPU:
    program_counter: int
    a: int
    x: int
    y: int
    stack_pointer: int
    status: Flag
    memory: Memory
    opcodes: dict
    cycles: int

    instruction: Optional[Instruction]
    assembly: Optional[str]
    memory_allocation: Optional[str]

    def __init__(self, memory: Memory, program_offset: int) -> None:
        # registers
        # program counter is 16 bits
        self.program_offset = program_offset
        self.program_counter = program_offset
        # accumulator is 8 bits
        self.a = 0x00
        # x and y registers are 8 bits
        self.x = 0x00
        self.y = 0x00
        # stack pointer is 8 bits but the stack is 256 bytes
        self.stack_pointer = 0xFD
        # stats register is 8 bits where is bit is repersented by the Flags enum
        # 0x00 = 0b00100000
        # 0x01 = 0b00100001
        # 0x02 = 0b00100010
        # 0x03 = 0b00100011
        # 0x04 = 0b00100100
        # 0x05 = 0b00100101
        # 0x06 = 0b00100110
        # 0x07 = 0b00100111
        self.status = Flag(0b00100100)

        self.cycles = 0
        self.memory = memory
        self.opcodes = load_opcodes()

        self.instruction = None
        self.assembly = None
        self.memory_allocation = None

    @property
    def state(self):
        return {
            "A": self.a,
            "X": self.x,
            "Y": self.y,
            "SP": self.stack_pointer,
            "PC": self.program_counter,
            "S": self.status,
            "memory": self.memory.memory,
        }

    def set_state(self, state: dict):
        self.a = state["A"]
        self.x = state["X"]
        self.y = state["Y"]
        self.stack_pointer = state["SP"]
        self.program_counter = state["PC"]
        self.status = state["S"]
        if "memory" in state:
            self.memory.memory = state["memory"]

    def __str__(self):
        return f"{self.program_counter}\t{self.instruction.assembly_hex}\tA:{self.a} X:{self.x} Y:{self.y} P:{self.status} SP:{self.stack_pointer}"

    # Flag operations
    def set_flag(self, flag: Flag):
        self.status |= flag

    def clear_flag(self, flag: Flag):
        self.status &= ~flag

    def get_flag(self, flag: Flag):
        return bool(self.status & flag)

    def stack_pop(self):
        self.stack_pointer += 1
        return self.memory[0x0100 + self.stack_pointer]

    def stack_push(self, data):
        self.memory[0x0100 + self.stack_pointer] = data
        self.stack_pointer -= 1

    def stack_push_word(self, data):
        hi = (data >> 8) & 0xFF
        lo = data & 0xFF
        self.stack_push(hi)
        self.stack_push(lo)

    def stack_pop_word(self):
        lo = self.stack_pop()
        hi = self.stack_pop()
        return (hi << 8) | lo

    # def push_stack(self, value):
    #     # Push a value onto the stack
    #     self.memory.memory[0x0100 + self.stack_pointer] = value
    #     self.stack_pointer -= 1
    #
    # def stack_pop(self):
    #     # Read the value from the stack
    #     value = self.memory.memory[0x0100 + self.stack_pointer]
    #
    #     # Increment the stack pointer
    #     self.stack_pointer += 1
    #
    #     return value
    #
    # def stack_pop_word(self):
    #     # Read the value from the stack
    #     value = self.memory.memory[0x0100 + self.stack_pointer]
    #
    #     # Increment the stack pointer
    #     self.stack_pointer += 1
    #
    #     value |= self.memory.memory[0x0100 + self.stack_pointer] << 8
    #
    #     # Increment the stack pointer
    #     self.stack_pointer += 1
    #
    #     return value
    #
    # def push_stack_word(self, value):
    #     # Push a value onto the stack
    #     self.memory.memory[0x0100 + self.stack_pointer] = value >> 8
    #     self.stack_pointer -= 1
    #
    #     self.memory.memory[0x0100 + self.stack_pointer] = value & 0xFF
    #     self.stack_pointer -= 1
    #
    def step(self):
        # if first:
        # logger.debug(self)

        opcode_hex = self.memory[self.program_counter]
        instruction = self.opcodes[opcode_hex]

        self.instruction = instruction
        logger.debug(instruction)
        logger.debug(self)

        if not hasattr(self, instruction.opcode.value.upper()):
            logger.error(f"FUCK {instruction}")
            raise SystemError

        # information = getattr(self, instruction.opcode)(instruction=instruction)
        # self.log_step(information)

        getattr(self, instruction.opcode)(instruction=instruction)

    def run(self):
        logger.info("Starting Execution")
        while self.program_counter < len(self.memory.program_rom):
            self.step()

    def ADC(self, instruction: Instruction):
        # Add Memory to Accumulator with Carry
        # A + M + C -> A, C
        value, _ = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Perform the addition
        sum_value = self.a + value + self.get_flag(Flag.CARRY)

        # Set the Carry flag if necessary
        if sum_value > 0xFF:
            self.set_flag(Flag.CARRY)
        else:
            self.clear_flag(Flag.CARRY)

        # Update the Zero flag
        if (sum_value & 0xFF) == 0:  #
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Overflow flag
        # If the 7th bit is set and the 7th bit is not set
        if (self.a ^ value) & 0x80 == 0 and (self.a ^ sum_value) & 0x80 != 0:
            self.set_flag(Flag.OVERFLOW)
        else:
            self.clear_flag(Flag.OVERFLOW)

        # Update the Negative flag
        if sum_value & 0x80 != 0:  # If the 7th bit is set
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Store the result in the accumulator
        self.a = sum_value & 0xFF  # Keep it 8-bit

    def AND(self, instruction: Instruction):
        # AND Memory with Accumulator
        # A AND M -> A
        value, _ = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Perform the AND operation
        self.a &= value

        # Update the Zero flag
        if self.a == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if self.a & Flag.NEGATIVE.value != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

    def ASL(self, instruction: Instruction):
        # Arithmetic Shift Left
        # C <- [76543210] <- 0
        value, memory_address = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Set the Carry flag if necessary
        if value & 0x80 != 0:
            self.set_flag(Flag.CARRY)
        else:
            self.clear_flag(Flag.CARRY)

        # Shift the value left
        value = (value << 1) & 0xFF

        # Update the Zero flag
        if value == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if value & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        if instruction.addressing_mode == AddressingModes.ACCUMULATOR:
            self.a = value
        else:
            # Store the result in memory
            self.memory.set_memory(memory_address, value)

    def BCC(self, instruction: Instruction):
        # Branch on Carry Clear
        # branch on C = 0

        value, _ = self.memory.get_memory_value(instruction, self)

        if self.get_flag(Flag.CARRY) == 0:
            self.program_counter += value
        else:
            self.program_counter += instruction.no_bytes

    def BCS(self, instruction: Instruction):
        # Branch on Carry Set
        # branch on C = 1

        value, _ = self.memory.get_memory_value(instruction, self)

        if self.get_flag(Flag.CARRY) == 1:
            self.program_counter += value
        else:
            self.program_counter += instruction.no_bytes

    def BEQ(self, instruction: Instruction):
        # Branch on Result Zero
        # branch on Z = 1

        # Fetch the value from memory based on the addressing mode
        value, _ = self.memory.get_memory_value(instruction, self)

        if self.get_flag(Flag.ZERO) == 1:
            self.program_counter += value
        else:
            self.program_counter += instruction.no_bytes

    def BIT(self, instruction: Instruction):
        # Test Bits in Memory with Accumulator
        # A AND M, M7 -> N, M6 -> V

        value, _ = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Perform the AND operation
        self.a &= value

        # Update the Zero flag
        if self.a == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if value & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Update the Overflow flag
        if value & 0x40 != 0:
            self.set_flag(Flag.OVERFLOW)
        else:
            self.clear_flag(Flag.OVERFLOW)

    def BMI(self, instruction: Instruction):
        # Branch on Result Minus
        # branch on N = 1
        # Fetch the value from memory based on the addressing mode
        value, _ = self.memory.get_memory_value(instruction, self)

        if self.get_flag(Flag.NEGATIVE) == 1:
            self.program_counter += value
        else:
            self.program_counter += instruction.no_bytes

    def BNE(self, instruction: Instruction):
        # Branch on Result not Zero
        # branch on Z = 0

        # Fetch the value from memory based on the addressing mode
        value, _ = self.memory.get_memory_value(instruction, self)

        if self.get_flag(Flag.ZERO) == 0:
            self.program_counter = value
        else:
            self.program_counter += instruction.no_bytes

    def BPL(self, instruction: Instruction):
        # Branch on Result Plus
        # branch on N = 0
        # Fetch the value from memory based on the addressing mode
        value, _ = self.memory.get_memory_value(instruction, self)

        if self.get_flag(Flag.NEGATIVE) == 0:
            self.program_counter = value
        else:
            self.program_counter += instruction.no_bytes

    def BRK(self, instruction: Instruction):
        """
        Force Break
        interrupt, PC + 2 toS, B toS, D toS, interrupt vector to $FFFE/$FFFF
        The break command causes the microprocessor to go through an inter rupt sequence under program control.
        This means that the program counter of the second byte after the BRK. is automatically stored on the stack
        along with the processor status at the beginning of the break instruction. The microprocessor then transfers control to the interrupt vector.

        Other than changing the program counter, the break instruction changes no values in either the registers or the flags.

        Note on the MOS 6502:

        If an IRQ happens at the same time as a BRK instruction, the BRK instruction is ignored.
        """
        self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Push the program counter to the stack
        self.stack_push(self.program_counter >> 8)
        self.stack_push(self.program_counter & 0xFF)

        # Push the status register to the stack
        self.stack_push(self.status.value)

        # Set the program counter to the interrupt vector
        self.program_counter = self.memory.memory[0xFFFE]

    def BVC(self, instruction: Instruction):
        # Branch on Overflow Clear
        # branch on V = 0
        # Fetch the value from memory based on the addressing mode
        value, _ = self.memory.get_memory_value(instruction, self)

        if self.get_flag(Flag.OVERFLOW) == 0:
            self.program_counter += value
        else:
            self.program_counter += instruction.no_bytes

    def BVS(self, instruction: Instruction):
        # Branch on Overflow Set
        # branch on V = 1
        # Fetch the value from memory based on the addressing mode
        value, _ = self.memory.get_memory_value(instruction, self)

        if self.get_flag(Flag.OVERFLOW) == 1:
            self.program_counter += value
        else:
            self.program_counter += instruction.no_bytes

    def CLC(self, instruction: Instruction):
        # Clear Carry Flag
        # 0 -> C
        self.memory.get_memory_value(instruction, self)
        self.clear_flag(Flag.CARRY)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

    def CLD(self, instruction: Instruction):
        # Clear Decimal Mode
        # 0 -> D

        self.memory.get_memory_value(instruction, self)
        self.clear_flag(Flag.DECIMAL)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def CLI(self, instruction: Instruction):
        # Clear Interrupt Disable Bit
        # 0 -> I

        self.memory.get_memory_value(instruction, self)
        self.clear_flag(Flag.INTERRUPT_DISABLE)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def CLV(self, instruction: Instruction):
        # Clear Overflow Flag
        # 0 -> V

        self.memory.get_memory_value(instruction, self)
        self.clear_flag(Flag.OVERFLOW)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def CMP(self, instruction: Instruction):
        # Compare Memory and Accumulator
        # A - M
        # Fetch the value from memory based on the addressing mode
        value, _ = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Perform the subtraction
        if self.a >= value:
            self.set_flag(Flag.CARRY)
        else:
            self.clear_flag(Flag.CARRY)

    def CPX(self, instruction: Instruction):
        # Compare Memory and Index X
        # X - M
        # Fetch the value from memory based on the addressing mode
        value, _ = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Perform the subtraction
        if self.x >= value:
            self.set_flag(Flag.CARRY)
        else:
            self.clear_flag(Flag.CARRY)

    def CPY(self, instruction: Instruction):
        # Compare Memory and Index Y
        # Y - M
        # Fetch the value from memory based on the addressing mode
        value, _ = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Perform the subtraction
        if self.y >= value:
            self.set_flag(Flag.CARRY)
        else:
            self.clear_flag(Flag.CARRY)

    def DEC(self, instruction: Instruction):
        # Decrement Memory by One
        # M - 1 -> M
        # Fetch the value from memory based on the addressing mode
        value, memory_address = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Decrement the value
        value -= 1

        # Update the Zero flag
        if value == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if value & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Write the value back to memory
        self.memory.set_memory(memory_address, value)

    def DEX(self, instruction: Instruction):
        # Decrement Index X by One
        # X - 1 -> X

        self.memory.get_memory_value(instruction, self)
        # Decrement the value
        self.x -= 1

        # Update the Zero flag
        if self.x == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if self.x & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def DEY(self, instruction: Instruction):
        # Decrement Index Y by One
        # Y - 1 -> Y

        self.memory.get_memory_value(instruction, self)
        # Decrement the value
        self.y -= 1

        # Update the Zero flag
        if self.y == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag by checking the sign bit of the result
        if self.y & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def EOR(self, instruction: Instruction):
        # Exclusive-OR Memory with Accumulator
        # A EOR M -> A
        # Fetch the value from memory based on the addressing mode
        value, _ = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes
        # Perform the XOR operation
        self.a ^= value

        # Update the Zero flag
        if self.a == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag by checking the sign bit of the result
        if self.a & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

    def INC(self, instruction: Instruction):
        # Increment Memory by One
        # M + 1 -> M
        # Fetch the value from memory based on the addressing mode
        value, memory_address = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Increment the value
        value += 1

        # Update the Zero flag
        if value == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if value & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Write the value back to memory
        self.memory.set_memory(memory_address, value)

    def INX(self, instruction: Instruction):
        # Increment Index X by One
        # X + 1 -> X

        self.memory.get_memory_value(instruction, self)
        # Increment the value
        self.x += 1

        # Update the Zero flag
        if self.x == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if self.x & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def INY(self, instruction: Instruction):
        # Increment Index Y by One
        # Y + 1 -> Y

        self.memory.get_memory_value(instruction, self)
        # Increment the value
        self.y += 1

        # Update the Zero flag
        if self.y == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if self.y & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def JMP(self, instruction: Instruction):
        # Jump to New Location
        # (PC + 1) -> PCL
        # (PC + 2) -> PCH
        # Fetch the value from memory based on the addressing mode
        value, _ = self.memory.get_memory_value(instruction, self)

        # Set the program counter to the address
        self.program_counter = value

    def JSR(self, instruction: Instruction):
        # Jump to New Location Saving Return Address
        # Push (PC + 2), (PC + 1) on stack
        # (PC + 1) -> PCL
        # (PC + 2) -> PCH
        # Fetch the value from memory based on the addressing Mode
        _, memory_address = self.memory.get_memory_value(instruction, self)

        # Push the return address onto the stack
        self.stack_push_word(self.program_counter + instruction.no_bytes)

        # Set the program counter to the address
        self.program_counter = memory_address

    def LDA(self, instruction: Instruction):
        # Load Accumulator with Memory
        # M -> A
        # Fetch the value from memory based on the addressing mode
        value, _ = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes
        # Load the value into the accumulator
        self.a = value

        # Update the Zero flag
        if self.a == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag by checking the sign bit of the result
        if self.a & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

    def LDX(self, instruction: Instruction):
        # Load Index X with Memory
        # M -> X
        # Fetch the value from memory based on the addressing mode
        value, _ = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Load the value into the index register
        self.x = value

        # Update the Zero flag
        if self.x == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag by checking the sign bit of the result
        if self.x & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

    def LDY(self, instruction: Instruction):
        # Load Index Y with Memory
        # M -> Y
        # Fetch the value from memory based on the addressing mode
        value, _ = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes
        # Load the value into the index register
        self.y = value

        # Update the Zero flag
        if self.y == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag by checking the sign bit of the result
        if self.y & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

    def LSR(self, instruction: Instruction):
        # Logical Shift Right One Bit (Memory or Accumulator)
        # 0 -> [7][6][5][4][3][2][1][0] -> C
        # M/2 -> [7][6][5][4][3][2][1][0]
        # Fetch the value from memory based on the addressing mode
        value, memory_address = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes
        # Update the Carry flag by checking the least significant bit of the value
        if value & 0x01 != 0:
            self.set_flag(Flag.CARRY)
        else:
            self.clear_flag(Flag.CARRY)

        # Shift the value right by one bit
        value >>= 1

        # Update the Zero flag
        if value == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if value & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Write the value back to memory
        self.memory.set_memory(memory_address, value)

    def NOP(self, instruction: Instruction):
        # No Operation
        # Increment the program counter
        self.memory.get_memory_value(instruction, self)
        self.program_counter += instruction.no_bytes

    def ORA(self, instruction: Instruction):
        # OR Memory with Accumulator
        # A OR M -> A
        # Fetch the value from memory based on the addressing mode
        value, _ = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes
        # Perform the OR operation
        self.a |= value

        # Update the Zero flag
        if self.a == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag by checking the sign bit of the result
        if self.a & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

    def PHA(self, instruction: Instruction):
        # Push Accumulator on Stack
        # Push A on stack

        self.memory.get_memory_value(instruction, self)
        # Push the accumulator onto the stack
        self.stack_push(self.a)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def PHP(self, instruction: Instruction):
        # Push Processor Status on Stack
        # Push P on stack

        self.memory.get_memory_value(instruction, self)
        # Push the processor status onto the stack
        self.stack_push(self.status.value)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def PLA(self, instruction: Instruction):
        # Pull Accumulator from Stack
        # Pull A from stack

        self.memory.get_memory_value(instruction, self)
        # Pull the accumulator from the stack
        self.a = self.stack_pop()

        # Update the Zero flag
        if self.a == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag by checking the sign bit of the result
        if self.a & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def PLP(self, instruction: Instruction):
        # Pull Processor Status from Stack
        # Pull P from stack

        self.memory.get_memory_value(instruction, self)
        # Pull the processor status from the stack
        self.status = Flag(self.stack_pop())

        # Increment the program counter
        self.program_counter += 1

    def ROL(self, instruction: Instruction):
        # Rotate One Bit Left (Memory or Accumulator)
        # C <- [7][6][5][4][3][2][1][0] <- C
        # M <- [6][5][4][3][2][1][0][C]

        # Fetch the value from memory based on the addressing mode
        value, memory_address = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Save the current value of the Carry flag
        carry = self.get_flag(Flag.CARRY)

        # Update the Carry flag by checking the most significant bit of the value
        if value & 0x80 != 0:
            self.set_flag(Flag.CARRY)
        else:
            self.clear_flag(Flag.CARRY)

        # Shift the value left by one bit
        value <<= 1

        # Set the least significant bit of the value to the previous value of the Carry flag
        if carry:
            value |= 0x01

        # Update the Zero flag
        if value == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if value & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Write the value back to memory
        if instruction.addressing_mode == AddressingModes.ACCUMULATOR:
            self.a = value
        else:
            self.memory.set_memory(memory_address, value)

    def ROR(self, instruction: Instruction):
        # Rotate One Bit Right (Memory or Accumulator)
        # C -> [7][6][5][4][3][2][1][0] -> C
        # M -> [C][7][6][5][4][3][2][1]
        # Fetch the value from memory based on the addressing mode
        value, memory_address = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes
        # Save the current value of the Carry flag
        carry = self.get_flag(Flag.CARRY)

        # Update the Carry flag by checking the least significant bit of the value
        if value & 0x01 != 0:
            self.set_flag(Flag.CARRY)
        else:
            self.clear_flag(Flag.CARRY)

        # Shift the value right by one bit
        value >>= 1

        # Set the most significant bit of the value to the previous value of the Carry flag
        if carry:
            value |= 0x80

        # Update the Zero flag
        if value == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if value & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Write the value back to memory
        if instruction.addressing_mode == AddressingModes.ACCUMULATOR:
            self.a = value
        else:
            self.memory.set_memory(memory_address, value)

    def RTI(self, instruction: Instruction):
        # Return from Interrupt
        # Pull P from stack, PC from stack

        self.memory.get_memory_value(instruction, self)
        # Pull the processor status from the stack
        self.status = Flag(self.stack_pop())

    def RTS(self, instruction: Instruction):
        # Return from Subroutine
        # Pull PC from stack, PC+1 -> PC
        self.memory.get_memory_value(instruction, self)
        # Pull the program counter from the stack
        self.program_counter = self.stack_pop_word()

    def SBC(self, instruction: Instruction):
        # Subtract Memory from Accumulator with Borrow
        # A - M - C -> A
        # Fetch the value from memory based on the addressing mode
        value, _ = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes
        # Perform the subtraction
        result = self.a - value - (1 - self.get_flag(Flag.CARRY))

        # Update the Carry flag
        if result < 0:
            self.clear_flag(Flag.CARRY)
        else:
            self.set_flag(Flag.CARRY)

        # Update the Overflow flag
        if (self.a ^ result) & (value ^ result) & 0x80 != 0:
            self.set_flag(Flag.OVERFLOW)
        else:
            self.clear_flag(Flag.OVERFLOW)

        # Update the Zero flag
        if result == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if result & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Write the result back to the accumulator
        self.a = result & 0xFF

    def SEC(self, instruction: Instruction):
        # Set Carry Flag
        # 1 -> C

        self.memory.get_memory_value(instruction, self)
        # Set the Carry flag
        self.set_flag(Flag.CARRY)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def SED(self, instruction: Instruction):
        # Set Decimal Flag
        # 1 -> D

        self.memory.get_memory_value(instruction, self)
        # Set the Decimal flag
        self.set_flag(Flag.DECIMAL)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def SEI(self, instruction: Instruction):
        # Set Interrupt Disable Status
        # 1 -> I

        self.memory.get_memory_value(instruction, self)
        # Set the Interrupt flag
        self.set_flag(Flag.INTERRUPT_DISABLE)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def STA(self, instruction: Instruction):
        # Store Accumulator in Memory
        # A -> M

        # Fetch the value from memory based on the addressing mode
        _, memory_address = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Write the accumulator to memory based on the addressing mode
        self.memory.set_memory(memory_address, self.a)

    def STX(self, instruction: Instruction):
        # Store Index X in Memory
        # X -> M
        # Fetch the value from memory based on the addressing mode
        value, memory_address = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes
        # Write the X register to memory based on the addressing mode
        self.memory.set_memory(memory_address, value)

    def STY(self, instruction: Instruction):
        # Store Index Y in Memory
        # Y -> M
        # Fetch the value from memory based on the addressing mode
        value, _ = self.memory.get_memory_value(instruction, self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += instruction.no_bytes

        # Write the Y register to memory based on the addressing mode
        self.memory.set_memory(value, self.y)

    def TAX(self, instruction: Instruction):
        # Transfer Accumulator to Index X
        # A -> X

        self.memory.get_memory_value(instruction, self)
        # Copy the accumulator to the X register
        self.x = self.a

        # Update the Zero flag
        if self.x == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if self.x & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def TAY(self, instruction: Instruction):
        # Transfer Accumulator to Index Y
        # A -> Y

        self.memory.get_memory_value(instruction, self)
        # Copy the accumulator to the Y register
        self.y = self.a

        # Update the Zero flag
        if self.y == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if self.y & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def TSX(self, instruction: Instruction):
        # Transfer Stack Pointer to Index X
        # SP -> X

        self.memory.get_memory_value(instruction, self)
        # Copy the stack pointer to the X register
        self.x = self.stack_pointer

        # Update the Zero flag
        if self.x == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if self.x & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def TXA(self, instruction: Instruction):
        # Transfer Index X to Accumulator
        # X -> A

        self.memory.get_memory_value(instruction, self)
        # Copy the X register to the accumulator
        self.a = self.x

        # Update the Zero flag
        if self.a == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if self.a & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def TXS(self, instruction: Instruction):
        # Transfer Index X to Stack Pointer
        # X -> SP

        self.memory.get_memory_value(instruction, self)
        # Copy the X register to the stack pointer
        self.stack_pointer = self.x

        # Increment the program counter
        self.program_counter += instruction.no_bytes

    def TYA(self, instruction: Instruction):
        # Transfer Index Y to Accumulator
        # Y -> A

        self.memory.get_memory_value(instruction, self)
        # Copy the Y register to the accumulator
        self.a = self.y

        # Update the Zero flag
        if self.a == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if self.a & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        # Increment the program counter
        self.program_counter += instruction.no_bytes
