import enum
from copy import copy
from typing import List, Optional, Set
from instructions import AddressingModes, Instruction, Opcodes, load_opcodes
from logger import get_logger
from memory import Memory
from numpy import compare_chararrays
from utils import endianify

logger = get_logger(__name__)

"""
Problem operands

     140292356658992 str = 'SBC'
     140292356657904 str = 'INX'
     140292356657136 str = 'CLC'
     140292356658224 str = 'LDY'
     140292356658096 str = 'LDA'
     140292356659312 str = 'STA'
     140292953382768 str = 'NOP'
     140292356656176 str = 'DEC'
     140292356658032 str = 'JSR'
     140292356659056 str = 'SEC'
     140292356655088 str = 'ADC'
     140292356655728 str = 'BCC'
     140292356655920 str = 'BEQ'
     140292356653232 str = 'BPL'
     140292356654000 str = 'CPX'
     140292356653808 str = 'BNE'
     140292356658928 str = 'RTS'
     140292356656240 str = 'BCS'
     140292953100848 str = 'CMP'
     140292356657264 str = 'DEX'
     140292356659760 str = 'TXA'
     140292356658288 str = 'LSR'
     140292356658160 str = 'LDX'
     140292953100720 str = 'AND'
"""
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
    stack_start: int

    instruction: Instruction

    used_instructions: Set[str]

    def __init__(self, memory: Memory) -> None:
        self.a = 0x00
        self.x = 0x00
        self.y = 0x00
        # stack pointer is 8 bits but the stack is 256 bytes
        self.stack_pointer = 0xFD
        self.status = Flag(0b100100)

        self.cycles = 0
        self.memory = memory

        self.program_rom_offset = self.memory.program_rom_offset
        self.program_counter = self.memory.program_rom_offset

        self.opcodes = load_opcodes(self)

        self.instruction = Instruction(
            opcode=Opcodes.NOP,
            run=self.NOP,
            addressing_mode=AddressingModes.IMPLIED,
            no_bytes=2,
            opcode_hex="00",
            cycles=1,
            cycle_flags=[],
        )
        self.stack_start = 0x0100

        self.used_instructions = set()

    @property
    def state(self):
        return {
            "A": self.a,
            "X": self.x,
            "Y": self.y,
            "SP": self.stack_pointer,
            "PC": self.program_counter,
            "S": self.status,
            "MEMORY": self.memory.memory[: self.program_rom_offset],
        }

    def set_state(self, state: dict):
        self.a = state["A"]
        self.x = state["X"]
        self.y = state["Y"]
        self.stack_pointer = state["SP"]
        self.program_counter = state["PC"]
        self.status = state["S"]
        for inx, value in enumerate(state["MEMORY"]):
            self.memory.memory[inx] = value

    def __str__(self):
        return f"{self.program_counter}\t{self.instruction.assembly_hex}\tA:{self.a} X:{self.x} Y:{self.y} P:{self.status} SP:{self.stack_pointer}"

    # Flag operations
    def set_flag(self, flag: Flag):
        self.status |= flag

    def clear_flag(self, flag: Flag):
        self.status &= flag

    def get_flag(self, flag: Flag):
        return bool(self.status & flag)

    def stack_pop(self):
        self.stack_pointer += 1
        return self.memory[self.stack_start + self.stack_pointer]

    def stack_push(self, data):
        self.memory[self.stack_start + self.stack_pointer] = data
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

    def get_operand(self) -> int:
        self.instruction.assembly_hex = f"{self.instruction.opcode_hex}"
        # This is honestly ass - at this point I parse the operand - but i need
        # an easy way to refernece this property later (printing/logging) - so i mutate
        # the instruction object and change assembly hex context each time - this
        # isn't used for functionality but rather giving me better debug messages.
        if self.instruction.addressing_mode not in (AddressingModes.IMPLIED, AddressingModes.ACCUMULATOR):
            argument_bytes = self.memory.get_memory_slice(
                self.program_counter + 1, self.program_counter + self.instruction.no_bytes
            )
            self.instruction.assembly_hex += f" {' '.join([hex(x).split('x')[1:][0].zfill(2) for x in argument_bytes])}"
            return endianify(argument_bytes)
        return 0

    def read_word(self, address: int, *, wrap_at_page: bool = False) -> int:
        lo = self.memory.get_memory(address)
        hi = self.memory.get_memory(address + 1)
        if wrap_at_page and (address & 0xFF) == 0xFF:
            # will wrap at page boundary
            hi = self.memory.get_memory(address & 0xFF00)  # read the second (hi) byte from the start of the page

        return lo + (hi << 8)

    def process_addressing_mode(self) -> Optional[int]:
        operand = self.get_operand()
        match (self.instruction.addressing_mode):
            case AddressingModes.IMPLIED:
                return None

            case AddressingModes.ACCUMULATOR:
                return self.a

            case AddressingModes.IMMEDIATE | AddressingModes.ZERO_PAGE | AddressingModes.ABSOLUTE:
                return operand

            case AddressingModes.RELATIVE:
                return operand if operand < 0x80 else operand - 0x100

            case AddressingModes.X_INDEXED_ZERO_PAGE:
                return (operand + self.x) & 0xFF  # wrap around

            case AddressingModes.Y_INDEXED_ZERO_PAGE:
                return (operand + self.y) & 0xFF  # wrap around

            case AddressingModes.X_INDEXED_ABSOLUTE:
                return (operand + self.x) & 0xFFFF  # wrap around

            case AddressingModes.Y_INDEXED_ABSOLUTE:
                return (operand + self.y) & 0xFFFF  # wrap around

            case AddressingModes.ABSOLUTE_INDIRECT:
                return self.read_word(operand, wrap_at_page=True)

            case AddressingModes.X_INDEXED_ZERO_PAGE_INDIRECT:
                address = (operand + self.x) & 0xFF  # wrap around
                return self.read_word(address, wrap_at_page=True)

            case AddressingModes.ZERO_PAGE_INDIRECT_Y_INDEXED:
                return (self.read_word(operand, wrap_at_page=True) + self.y) & 0xFFFF  # wrap around

            case _:
                raise SystemError

    def step(self) -> None:
        opcode_hex = self.memory[self.program_counter]
        self.instruction = self.opcodes[opcode_hex]

        if not hasattr(self, self.instruction.opcode.value.upper()):
            raise SystemError

        instruction_args = self.process_addressing_mode()

        self.used_instructions.add(self.instruction.opcode.value)
        logger.debug(self.instruction)
        logger.debug(self)

        # Increment program counter by size of operation (opcode + operand)
        self.program_counter += self.instruction.no_bytes
        # run the instruction
        self.instruction.run(instruction_args)

    def run(self):
        logger.info("Starting Execution")
        while self.program_counter < len(self.memory.program_rom):
            self.step()

    def ADC(self, value):
        # Add Memory to Accumulator with Carry
        # A + M + C -> A, C
        if self.instruction.addressing_mode != AddressingModes.IMMEDIATE:
            value = self.memory.get_memory(value)

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

    def AND(self, value):
        # AND Memory with Accumulator
        # A AND M -> A
        value = self.memory.get_memory(value)

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

    def ASL(self, value):
        # Arithmetic Shift Left
        # C <- [76543210] <- 0
        if self.instruction.addressing_mode != AddressingModes.ACCUMULATOR:
            value = self.memory.get_memory(value)

        # Set the Carry flag if necessary
        if value & 0x80 != 0:
            self.set_flag(Flag.CARRY)
        else:
            self.clear_flag(Flag.CARRY)

        # Shift the value left by 1
        value = value << 1

        # Update the Zero Flag
        if value == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative Flags
        if value & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

    def BIT(self, value):
        # Test Bits in Memory with Accumulator
        # A AND M, M7 -> N, M6 -> V
        value = self.memory.get_memory(value)

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

    def branch(self, condition: bool, value: int):
        if condition:
            jump_addr = self.program_counter + value
            self.program_counter = jump_addr

    def BNE(self, value):
        # Branch on Result not ZERO
        self.branch(not self.get_flag(Flag.ZERO), value)

    def BPL(self, value):
        # Branch on Result Plus
        self.branch(not self.get_flag(Flag.NEGATIVE), value)

    def BVC(self, value):
        # Branch on Overflow Clear
        self.branch(not self.get_flag(Flag.OVERFLOW), value)

    def BCC(self, value):
        # Branch on Carry Clear
        self.branch(not self.get_flag(Flag.CARRY), value)

    def BVS(self, value):
        # Branch on Overflow set
        self.branch(self.get_flag(Flag.OVERFLOW), value)

    def BCS(self, value):
        # Branch on Carry set
        self.branch(self.get_flag(Flag.CARRY), value)

    def BEQ(self, value):
        # Branch on Result Zero
        self.branch(self.get_flag(Flag.ZERO), value)

    def BMI(self, value):
        # Branch on Result Minus
        self.branch(self.get_flag(Flag.NEGATIVE), value)

    def BRK(self, value):
        # Push the program counter to the stack
        self.stack_push(self.program_counter >> 8)
        self.stack_push(self.program_counter & 0xFF)

        # Push the status register to the stack
        self.stack_push(self.status.value)

        # Set the program counter to the interrupt vector
        self.program_counter = self.memory.memory[0xFFFE]

    def CLC(self, _):
        # Clear Carry Flag
        self.clear_flag(Flag.CARRY)

    def CLD(self, _):
        # Clear Decimal Mode
        # 0 -> D
        self.clear_flag(Flag.DECIMAL)

    def CLI(self, _):
        # Clear Interrupt Disable Bit
        # 0 -> I
        self.clear_flag(Flag.INTERRUPT_DISABLE)

    def CLV(self, _):
        # Clear Overflow Flag
        # 0 -> V
        self.clear_flag(Flag.OVERFLOW)

    def compare(self, register, value):
        if self.instruction.addressing_mode != AddressingModes.IMMEDIATE:
            value = self.memory.get_memory(value)

        if register == value:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # he N flag is set or reset by the result bit 7
        if value & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

        if value <= register:
            self.set_flag(Flag.CARRY)
        else:
            self.clear_flag(Flag.CARRY)

    def CMP(self, value):
        # Compare Memory and Accumulator
        # A - M
        self.compare(self.a, value)

    def CPX(self, value):
        # Compare Memory and Index X
        # X - M
        self.compare(self.x, value)

    def CPY(self, value):
        # Compare Memory and Index Y
        # Y - M
        self.compare(self.y, value)

    def DEC(self, value):
        # Decrement Memory by One
        # M - 1 -> M
        # Decrement the memory value by One
        value = self.memory.set_memory(value, self.memory.get_memory(value) - 1)

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

    def DEX(self, value):
        # Decrement Index X by One
        # X - 1 -> X
        self.x -= 1

        if self.x == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        if self.x & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)


    def DEY(self, value):
        # Decrement Index Y by One
        # Y - 1 -> Y
        self.y -= 1

        if self.y == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        if self.y & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)


    def EOR(self, value):
        # Exclusive-OR Memory with Accumulator
        # A EOR M -> A
        value = self.memory.get_memory(value)

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

    def INC(self, value):
        # Increment Memory by One
        value = self.memory.set_memory(value, self.memory.get_memory(value) + 1)

        # Update the Zero Flag
        if value == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative Flag
        if value & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

    def INX(self, _):
        # Increment Index X by one
        # X + 1 -> X
        self.x += 1

        if self.x == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        if self.x & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

    def INY(self, _):
        # Increment Index Y by One
        # Y + 1 -> Y
        self.y += 1

        if self.y == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        if self.y & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

    def JMP(self, value):
        # Jump to New Location
        # (PC + 1) -> PCL
        # (PC + 2) -> PCH
        # Set the program counter to the address
        self.program_counter = value

    def JSR(self, value):
        # Jump to New Location Saving Return Address
        # Push (PC + 2), (PC + 1) on stack
        # (PC + 1) -> PCL
        # (PC + 2) -> PCH
        # Push the return address onto the stack
        self.stack_push_word(self.program_counter)

        # Set the program counter to the address
        self.program_counter = value

    def LDA(self, value):
        # Load Accumulator with Memory
        # M -> A
        if self.instruction.addressing_mode != AddressingModes.IMMEDIATE:
            value = self.memory.get_memory(value)

        self.a = copy(value)

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

    def LDX(self, value):
        # Load Index X with Memory
        # M -> X
        if self.instruction.addressing_mode != AddressingModes.IMMEDIATE:
            value = self.memory.get_memory(value)

        self.x = copy(value)

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


    def LDY(self, value):
        # Load Index Y with Memory
        # M -> Y
        if self.instruction.addressing_mode != AddressingModes.IMMEDIATE:
            value = self.memory.get_memory(value)

        self.y = copy(value)

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

    def LSR(self, value):
        # Logical Shift Right One Bit (Memory or Accumulator)
        # 0 -> [7][6][5][4][3][2][1][0] -> C
        # M/2 -> [7][6][5][4][3][2][1][0]
        if self.instruction.addressing_mode != AddressingModes.ACCUMULATOR:
            value = self.memory.get_memory(value)

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

    def NOP(self, value):
        # No Operation
        pass

    def ORA(self, value):
        # OR Memory with Accumulator
        # A OR M -> A
        if self.instruction.addressing_mode != AddressingModes.IMMEDIATE:
            value = self.memory.get_memory(value)

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

    def PHA(self, value):
        # Push the accumulator onto the stack
        self.stack_push(self.a)

    def PHP(self, value):
        # Push the processor status onto the stack
        self.stack_push(self.status.value)

    def PLA(self, value):
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

    def PLP(self, value):
        # Pull the processor status from the stack
        self.status = Flag(self.stack_pop())

    def ROL(self, value):
        # Rotate One Bit Left (Memory or Accumulator)
        # C <- [7][6][5][4][3][2][1][0] <- C
        # M <- [6][5][4][3][2][1][0][C]
        if self.instruction.addressing_mode != AddressingModes.ACCUMULATOR:
            value = self.memory.get_memory(value)

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

    def ROR(self, value):
        # Rotate One Bit Right (Memory or Accumulator)
        # C -> [7][6][5][4][3][2][1][0] -> C
        # M -> [C][7][6][5][4][3][2][1]
        if self.instruction.addressing_mode != AddressingModes.ACCUMULATOR:
            value = self.memory.get_memory(value)

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

    def RTI(self, value):
        # Return from Interrupt
        # Pull P from stack, PC from stack
        self.status = Flag(self.stack_pop())

    def RTS(self, value):
        # Return from Subroutine
        # Pull PC from stack, PC+1 -> PC
        self.program_counter = self.stack_pop_word()

    def SBC(self, value):
        # Subtract Memory from Accumulator with Borrow
        # A - M - C -> A
        if self.instruction.addressing_mode != AddressingModes.IMMEDIATE:
            value = self.memory.get_memory(value)

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

    def SEC(self, value):
        # Set Carry Flag
        # 1 -> C
        self.set_flag(Flag.CARRY)

    def SED(self, value):
        # Set Decimal Flag
        # 1 -> D
        self.set_flag(Flag.DECIMAL)

    def SEI(self, value):
        # Set Interrupt Disable Status
        # 1 -> I
        self.set_flag(Flag.INTERRUPT_DISABLE)

    def STA(self, value):
        # Store Accumulator in Memory
        # A -> M
        self.memory.set_memory(value, self.a)

    def STX(self, value):
        # Store Index X in Memory
        # X -> M
        self.memory.set_memory(value, self.x)

    def STY(self, value):
        # Store Index Y in Memory
        # Y -> M
        self.memory.set_memory(value, self.y)

    def transfer(self, source, destination):
        destination = copy(source)

        # Update the Zero flag
        if destination == 0:
            self.set_flag(Flag.ZERO)
        else:
            self.clear_flag(Flag.ZERO)

        # Update the Negative flag
        if destination & 0x80 != 0:
            self.set_flag(Flag.NEGATIVE)
        else:
            self.clear_flag(Flag.NEGATIVE)

    def TAX(self, value):
        # Transfer Accumulator to Index X
        # A -> X
        self.transfer(self.a, self.x)

    def TAY(self, value):
        # Transfer Accumulator to Index Y
        # A -> Y
        self.transfer(self.a, self.y)

    def TSX(self, value):
        # Transfer Stack Pointer to Index X
        # SP -> X
        self.transfer(self.stack_pointer, self.x)

    def TXA(self, value):
        # Transfer Index X to Accumulator
        # X -> A
        self.transfer(self.x, self.a)

    def TXS(self, value):
        # Transfer Index X to Stack Pointer
        # X -> SP
        self.transfer(self.x, self.stack_pointer)

    def TYA(self, value):
        # Transfer Index Y to Accumulator
        # Y -> A
        self.transfer(self.y, self.a)
