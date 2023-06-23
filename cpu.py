import curses
import enum
from instructions import Instructions
from logger import get_logger
from memory import Memory

logger = get_logger(__name__)


class Flags(enum.Enum):
    CARRY = 0
    ZERO = 1
    INTERRUPT = 2
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

        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)

    # Flag operations
    def set_flag(self, flag: Flags):
        self.status |= 1 << flag.value

    def clear_flag(self, flag: Flags):
        self.status &= ~(1 << flag.value)

    def get_flag(self, flag: Flags) -> bool:
        return bool(self.status & (1 << flag.value))

    def push(self, value):
        # Decrement the stack pointer
        self.stack_pointer -= 1

        # Write the value to the stack
        self.memory.write(0x0100 + self.stack_pointer, value & 0xFF)

    def pull(self):
        # Read the value from the stack
        value = self.memory.read(0x0100 + self.stack_pointer)

        # Increment the stack pointer
        self.stack_pointer += 1

        return value

    def pull_word(self):
        # Pull a word from the stack
        # (SP + 1) -> PCL
        # (SP + 2) -> PCH

        # Pull the low byte from the stack
        low_byte = self.pull()

        # Pull the high byte from the stack
        high_byte = self.pull()

        # Return the word
        return (high_byte << 8) | low_byte

    def display_cpu_state(self):
        self.stdscr.addstr(0, 0, "CPU State:")
        self.stdscr.addstr(2, 0, f"PC: {hex(self.program_counter)}")
        self.stdscr.addstr(3, 0, f"A: {hex(self.a)}")
        self.stdscr.addstr(4, 0, f"X: {hex(self.x)}")
        self.stdscr.addstr(5, 0, f"Y: {hex(self.y)}")
        self.stdscr.addstr(6, 0, f"Stack Pointer: {hex(self.stack_pointer)}")
        self.stdscr.addstr(7, 0, f"Status: {bin(self.cpu.status)}")

    def display_registers(self):
        self.stdscr.addstr(9, 0, "Registers:")
        # Display additional registers if applicable

    def display_memory(self):
        self.stdscr.addstr(11, 0, "Memory:")
        # Display memory contents

        # Get memory range to display
        start_address = 0x0000
        end_address = 0xFFFF
        memory_rows = []

        for address in range(start_address, end_address + 1):
            value = self.cpu.memory.read(address)
            binary = self.format_binary(value)
            memory_rows.append(f"{hex(address)}: {binary}")

        # Display memory rows
        row = 12
        for memory_row in memory_rows:
            self.stdscr.addstr(row, 0, memory_row)
            row += 1

    def format_binary(self, value):
        binary = bin(value)[2:].zfill(8)
        return f"[{binary}]"

    def close(self):
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    def decompile_program(self):
        while self.program_counter < self.memory.cartridge.program_rom_size:
            self.stdscr.clear()

            self.display_cpu_state()
            self.display_registers()
            self.display_memory()

            self.stdscr.refresh()

            # Get user input
            key = self.stdscr.getch()
            if key == ord("q"):
                break

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
                continue

    def ADC(self, operand):
        # Add Memory to Accumulator with Carry
        # A + M + C -> A, C

        # Fetch the value from memory
        value = self.memory.read(operand)

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

        # Fetch the value from memory AND with the accumulator
        self.a &= self.memory.read(operand)

        # Set the Zero flag if necessary
        if self.a == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if self.a & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def ASL(self, operand):
        # Shift Left One Bit (Memory or Accumulator)
        # C <- [76543210] <- 0

        # Fetch the value from memory or the accumulator
        value = self.memory.read(operand)

        # Move bit 7 to the carry flag
        if value & 0x80 != 0:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Shift left by 1
        value = (value << 1) & 0xFF

        # Store the value in memory or the accumulator
        self.memory.write(operand, value)

        # Set the Zero flag if necessary
        if value == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if value & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def BCC(self, operand):
        # Branch on Carry Clear
        # branch on C = 0

        if self.get_flag(Flags.CARRY) == 0:
            self.program_counter += operand
        else:
            self.program_counter += 1

    def BCS(self, operand):
        # Branch on Carry Set
        # branch on C = 1

        if self.get_flag(Flags.CARRY) == 1:
            self.program_counter += operand
        else:
            self.program_counter += 1

    def BEQ(self, operand):
        # Branch on Result Zero
        # branch on Z = 1

        if self.get_flag(Flags.ZERO) == 1:
            self.program_counter += operand
        else:
            self.program_counter += 1

    def BIT(self, operand):
        # Test Bits in Memory with Accumulator
        # A AND M, M7 -> N, M6 -> V

        # Fetch the value from memory AND with the accumulator
        value = self.memory.read(operand)
        self.a &= value

        # Set the Zero flag if necessary
        if self.a == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if value & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Set the Overflow flag if necessary
        if value & 0x40 != 0:
            self.set_flag(Flags.OVERFLOW)
        else:
            self.clear_flag(Flags.OVERFLOW)

        # Increment the program counter
        self.program_counter += 1

    def BMI(self, operand):
        # Branch on Result Minus
        # branch on N = 1

        if self.get_flag(Flags.NEGATIVE) == 1:
            self.program_counter += operand
        else:
            self.program_counter += 1

    def BNE(self, operand):
        # Branch on Result not Zero
        # branch on Z = 0

        if self.get_flag(Flags.ZERO) == 0:
            self.program_counter += operand
        else:
            self.program_counter += 1

    def BPL(self, operand):
        # Branch on Result Plus
        # branch on N = 0

        if self.get_flag(Flags.NEGATIVE) == 0:
            self.program_counter += operand
        else:
            self.program_counter += 1

    def BRK(self):
        # Force Break
        # interrupt, push PC+2, push SR

        # Increment the program counter
        self.program_counter += 1

        # Push the program counter onto the stack
        self.push(self.program_counter >> 8)
        self.push(self.program_counter & 0xFF)

        # Push the status register onto the stack
        self.push(self.status | 0x10)

        # Set the Interrupt flag
        self.set_flag(Flags.INTERRUPT)

        # Jump to the interrupt vector
        self.program_counter = self.memory.read_word(0xFFFE)

    def BVC(self, operand):
        # Branch on Overflow Clear
        # branch on V = 0

        if self.get_flag(Flags.OVERFLOW) == 0:
            self.program_counter += operand
        else:
            self.program_counter += 1

    def BVS(self, operand):
        # Branch on Overflow Set
        # branch on V = 1

        if self.get_flag(Flags.OVERFLOW) == 1:
            self.program_counter += operand
        else:
            self.program_counter += 1

    def CLC(self):
        # Clear Carry Flag
        # 0 -> C

        self.clear_flag(Flags.CARRY)
        self.program_counter += 1

    def CLD(self):
        # Clear Decimal Mode
        # 0 -> D

        self.clear_flag(Flags.DECIMAL)
        self.program_counter += 1

    def CLI(self):
        # Clear Interrupt Disable Bit
        # 0 -> I

        self.clear_flag(Flags.INTERRUPT)
        self.program_counter += 1

    def CLV(self):
        # Clear Overflow Flag
        # 0 -> V

        self.clear_flag(Flags.OVERFLOW)
        self.program_counter += 1

    def CMP(self, operand):
        # Compare Memory and Accumulator
        # A - M

        # Fetch the value from memory
        value = self.memory.read(operand)

        # Set the Carry flag if necessary
        if self.a >= value:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Set the Zero flag if necessary
        if self.a == value:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if (self.a - value) & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def CPX(self, operand):
        # Compare Memory and Index X
        # X - M

        # Fetch the value from memory
        value = self.memory.read(operand)

        # Set the Carry flag if necessary
        if self.x >= value:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Set the Zero flag if necessary
        if self.x == value:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if (self.x - value) & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def CPY(self, operand):
        # Compare Memory and Index Y
        # Y - M

        # Fetch the value from memory
        value = self.memory.read(operand)

        # Set the Carry flag if necessary
        if self.y >= value:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Set the Zero flag if necessary
        if self.y == value:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if (self.y - value) & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def DEC(self, operand):
        # Decrement Memory by One
        # M - 1 -> M

        # Fetch the value from memory
        value = self.memory.read(operand)

        # Decrement the value
        value -= 1

        # Write the value back to memory
        self.memory.write(operand, value)

        # Set the Zero flag if necessary
        if value == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if value & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def DEX(self):
        # Decrement Index X by One
        # X - 1 -> X

        # Decrement the value
        self.x -= 1

        # Set the Zero flag if necessary
        if self.x == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
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

        # Set the Zero flag if necessary
        if self.y == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if self.y & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def EOR(self, operand):
        # Exclusive-OR Memory with Accumulator
        # A EOR M -> A

        # Fetch the value from memory
        value = self.memory.read(operand)

        # Perform the exclusive-or
        self.a ^= value

        # Set the Zero flag if necessary
        if self.a == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if self.a & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def INC(self, operand):
        # Increment Memory by One
        # M + 1 -> M

        # Fetch the value from memory
        value = self.memory.read(operand)

        # Increment the value
        value += 1

        # Write the value back to memory
        self.memory.write(operand, value)

        # Set the Zero flag if necessary
        if value == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if value & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def INX(self):
        # Increment Index X by One
        # X + 1 -> X

        # Increment the value
        self.x += 1

        # Set the Zero flag if necessary
        if self.x == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
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

        # Set the Zero flag if necessary
        if self.y == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
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

        # Set the program counter
        self.program_counter = operand

    def JSR(self, operand):
        # Jump to New Location Saving Return Address
        # (PC + 1) -> PCL
        # (PC + 2) -> PCH
        # Push (PC + 2) onto stack
        # PCL -> (SP)
        # PCH -> (SP + 1)

        # Push the program counter onto the stack
        self.push(self.program_counter >> 8)
        self.push(self.program_counter & 0xFF)

        # Set the program counter
        self.program_counter = operand

    def LDA(self, operand):
        # Load Accumulator with Memory
        # M -> A

        # Fetch the value from memory
        value = self.memory.read(operand)

        # Load the value into the accumulator
        self.a = value

        # Set the Zero flag if necessary
        if self.a == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if self.a & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def LDX(self, operand):
        # Load Index X with Memory
        # M -> X

        # Fetch the value from memory
        value = self.memory.read(operand)

        # Load the value into the index register
        self.x = value

        # Set the Zero flag if necessary
        if self.x == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if self.x & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def LDY(self, operand):
        # Load Index Y with Memory
        # M -> Y

        # Fetch the value from memory
        value = self.memory.read(operand)

        # Load the value into the index register
        self.y = value

        # Set the Zero flag if necessary
        if self.y == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if self.y & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def LSR(self, operand):
        # Shift One Bit Right (Memory or Accumulator)
        # 0 -> [76543210] -> C

        # Fetch the value from memory
        value = self.memory.read(operand)

        # Shift the value right
        value >>= 1

        # Write the value back to memory
        self.memory.write(operand, value)

        # Set the Carry flag if necessary
        if value & 0x01 != 0:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Set the Zero flag if necessary
        if value == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag to zero
        self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def NOP(self):
        # No Operation
        # --- -> ---

        # Increment the program counter
        self.program_counter += 1

    def ORA(self, operand):
        # OR Memory with Accumulator
        # A V M -> A

        # Fetch the value from memory
        value = self.memory.read(operand)

        # OR the value with the accumulator
        self.a |= value

        # Set the Zero flag if necessary
        if self.a == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if self.a & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def PHA(self):
        # Push Accumulator on Stack
        # A -> (SP)

        # Push the accumulator onto the stack
        self.push(self.a)

        # Increment the program counter
        self.program_counter += 1

    def PHP(self):
        # Push Processor Status on Stack
        # P -> (SP)

        # Push the processor status onto the stack
        self.push(self.status)

        # Increment the program counter
        self.program_counter += 1

    def PLA(self):
        # Pull Accumulator from Stack
        # (SP) -> A

        # Pull the accumulator from the stack
        self.a = self.pull()

        # Set the Zero flag if necessary
        if self.a == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if self.a & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def PLP(self):
        # Pull Processor Status from Stack
        # (SP) -> P

        # Pull the processor status from the stack
        self.status = self.pull()

        # Increment the program counter
        self.program_counter += 1

    def ROL(self, operand):
        # Rotate One Bit Left (Memory or Accumulator)
        # C <- [76543210] <- C

        # Fetch the value from memory
        value = self.memory.read(operand)

        # Rotate the value left
        value <<= 1

        # OR the carry flag into the value
        if self.get_flag(Flags.CARRY):
            value |= 0x01

        # Write the value back to memory
        self.memory.write(operand, value)

        # Set the Carry flag if necessary
        if value & 0x100 != 0:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Set the Zero flag if necessary
        if value == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if value & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def ROR(self, operand):
        # Rotate One Bit Right (Memory or Accumulator)
        # C -> [76543210] -> C

        # Fetch the value from memory
        value = self.memory.read(operand)

        # Rotate the value right
        value >>= 1

        # OR the carry flag into the value
        if self.get_flag(Flags.CARRY):
            value |= 0x80

        # Write the value back to memory
        self.memory.write(operand, value)

        # Set the Carry flag if necessary
        if value & 0x01 != 0:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Set the Zero flag if necessary
        if value == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if value & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def RTI(self):
        # Return from Interrupt
        # from Interrupt

        # Pull the processor status from the stack
        self.status = self.pull()

        # Pull the program counter from the stack
        self.program_counter = self.pull_word()

    def RTS(self):
        # Return from Subroutine
        # from Subroutine

        # Pull the program counter from the stack
        self.program_counter = self.pull_word()

        # Increment the program counter
        self.program_counter += 1

    def SBC(self, operand):
        # Subtract Memory from Accumulator with Borrow
        # A - M - C -> A

        # Fetch the value from memory
        value = self.memory.read(operand)

        # Subtract the value from the accumulator
        result = self.a - value - (1 - self.get_flag(Flags.CARRY))

        # Set the Carry flag if necessary
        if result < 0x00:
            self.set_flag(Flags.CARRY)
        else:
            self.clear_flag(Flags.CARRY)

        # Set the Overflow flag if necessary
        if (self.a ^ result) & (value ^ result) & 0x80 != 0:
            self.set_flag(Flags.OVERFLOW)
        else:
            self.clear_flag(Flags.OVERFLOW)

        # Set the Zero flag if necessary
        if result & 0xFF == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
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
        # Set Decimal Mode
        # 1 -> D

        # Set the Decimal flag
        self.set_flag(Flags.DECIMAL)

        # Increment the program counter
        self.program_counter += 1

    def SEI(self):
        # Set Interrupt Disable Status
        # 1 -> I

        # Set the Interrupt flag
        self.set_flag(Flags.INTERRUPT)

        # Increment the program counter
        self.program_counter += 1

    def STA(self, operand):
        # Store Accumulator in Memory
        # A -> M

        # Store the accumulator in memory
        self.memory.write(operand, self.a)

        # Increment the program counter
        self.program_counter += 1

    def STX(self, operand):
        # Store Index X in Memory
        # X -> M

        # Store the index X in memory
        self.memory.write(operand, self.x)

        # Increment the program counter
        self.program_counter += 1

    def STY(self, operand):
        # Store Index Y in Memory
        # Y -> M

        # Store the index Y in memory
        self.memory.write(operand, self.y)

        # Increment the program counter
        self.program_counter += 1

    def TAX(self):
        # Transfer Accumulator to Index X
        # A -> X

        # Transfer the accumulator to index X
        self.x = self.a

        # Set the Zero flag if necessary
        if self.x == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if self.x & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def TAY(self):
        # Transfer Accumulator to Index Y
        # A -> Y

        # Transfer the accumulator to index Y
        self.y = self.a

        # Set the Zero flag if necessary
        if self.y == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if self.y & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def TSX(self):
        # Transfer Stack Pointer to Index X
        # SP -> X

        # Transfer the stack pointer to index X
        self.x = self.stack_pointer

        # Set the Zero flag if necessary
        if self.x == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if self.x & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def TXA(self):
        # Transfer Index X to Accumulator
        # X -> A

        # Transfer index X to the accumulator
        self.a = self.x

        # Set the Zero flag if necessary
        if self.a == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if self.a & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1

    def TXS(self):
        # Transfer Index X to Stack Register
        # X -> SP

        # Transfer index X to the stack pointer
        self.stack_pointer = self.x

        # Increment the program counter
        self.program_counter += 1

    def TYA(self):
        # Transfer Index Y to Accumulator
        # Y -> A

        # Transfer index Y to the accumulator
        self.a = self.y

        # Set the Zero flag if necessary
        if self.a == 0x00:
            self.set_flag(Flags.ZERO)
        else:
            self.clear_flag(Flags.ZERO)

        # Set the Negative flag if necessary
        if self.a & 0x80 != 0:
            self.set_flag(Flags.NEGATIVE)
        else:
            self.clear_flag(Flags.NEGATIVE)

        # Increment the program counter
        self.program_counter += 1
