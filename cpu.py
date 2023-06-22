from cartrige import Cartridge
from instructions import Instructions
from logger import get_logger
from memory import Memory

logger = get_logger(__name__)


class CPU:
    program_counter: int
    stack_pointer: int
    accumulator: int
    index_x: int
    index_y: int
    status: int

    def __init__(self, memory: Memory):
        self.memory = memory
        self.reset()

    def reset(self):
        self.program_counter = 0
        self.stack_pointer = 0
        self.accumulator = 0
        self.status = 0
        self.x_register = 0
        self.y_register = 0

    def compute_program_counter(self, opcode: Instructions.Opcodes) -> int:
        return self.program_counter + opcode.value.argument_length + 1

    def decompile_program(self):
        while self.program_counter < self.memory.cartridge.program_rom_size:
            logger.debug(
                f"PC: {hex(self.program_counter)}"
                f" SP: {hex(self.stack_pointer)}"
                f" A: {hex(self.accumulator)}"
                f" X: {hex(self.x_register)}"
                f" Y: {hex(self.y_register)}"
                f" Status: {hex(self.status)}"
            )
            opcode_hex = self.memory.program_rom[self.program_counter]
            opcode = Instructions.get_opcode(opcode_hex)
            operand = None
            if opcode.value.argument_length > 0:
                operand = self.memory.program_rom[self.program_counter + opcode.value.argument_length]

            if hasattr(self, opcode.name.lower()):
                logger.info(f"{opcode.name} ({operand if operand else ''})")
                if operand:
                    getattr(self, opcode.name.lower())(operand)
                else:
                    getattr(self, opcode.name.lower())()

            self.program_counter = self.compute_program_counter(opcode)

    def stack_push(self, value: int) -> None:
        """
        Pushes a value to the stack.
        """
        self.memory.memory[0x0100 + self.stack_pointer] = value
        self.stack_pointer -= 1

    def stack_pop(self) -> int:
        """
        Pops the stack and returns the value.
        """
        self.stack_pointer += 1
        return self.memory.memory[0x0100 + self.stack_pointer]

    def adc(self, operand: int) -> None:
        """
        Adds the immediate value following the ADC opcode from memory to the
        accumulator of the CPU. The program counter (self.pc) is incremented to
        point to the next instruction after the immediate value.
        """
        self.accumulator += operand

    def and_(self, operand: int) -> None:
        """
        Performs a bitwise AND operation on the immediate value following the
        AND opcode and the accumulator of the CPU. The program counter (self.pc)
        is incremented to point to the next instruction after the immediate
        value.
        """
        self.accumulator &= operand

    def asl(self) -> None:
        """
        Shifts the bits in the accumulator of the CPU to the left by one bit.
        """
        self.accumulator <<= 1

    def bcc(self, operand: int) -> None:
        """
        Branches to the relative address following the BCC opcode if the carry
        flag is not set.
        """
        if not self.status & 0b00000001:
            self.program_counter += operand
        else:
            self.program_counter += 1

    def beq(self, operand: int) -> None:
        """
        Branches to the relative address following the BEQ opcode if the zero
        flag is set.
        """
        if self.status & 0b00000010:
            self.program_counter += operand
        else:
            self.program_counter += 1

    def bit(self, operand: int) -> None:
        """
        Performs a bitwise AND operation on the immediate value following the
        BIT opcode and the accumulator of the CPU. The zero flag is set if the
        result of the bitwise AND operation is zero.
        """
        self.accumulator &= operand
        if self.accumulator == 0:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101

    def bmi(self, operand: int) -> None:
        """
        Branches to the relative address following the BMI opcode if the
        negative flag is set.
        """
        if self.status & 0b10000000:
            self.program_counter += operand
        else:
            self.program_counter += 1

    def bne(self, operand: int) -> None:
        """
        Branches to the relative address following the BNE opcode if the zero
        flag is not set.
        """
        if not self.status & 0b00000010:
            self.program_counter += operand
        else:
            self.program_counter += 1

    def bpl(self, operand: int) -> None:
        """
        Branches to the relative address following the BPL opcode if the
        negative flag is not set.
        """
        if not self.status & 0b10000000:
            self.program_counter += operand
        else:
            self.program_counter += 1

    def brk(self) -> None:
        """
        Sets the break flag of the CPU.
        """
        self.status |= 0b00010000

    def bvc(self, operand: int) -> None:
        """
        Branches to the relative address following the BVC opcode if the
        overflow flag is not set.
        """
        if not self.status & 0b01000000:
            self.program_counter += operand
        else:
            self.program_counter += 1

    def bvs(self, operand: int) -> None:
        """
        Branches to the relative address following the BVS opcode if the
        overflow flag is set.
        """
        if self.status & 0b01000000:
            self.program_counter += operand
        else:
            self.program_counter += 1

    def clc(self) -> None:
        """
        Clears the carry flag of the CPU.
        """
        self.status &= 0b11111110

    def cld(self) -> None:
        """
        Clears the decimal flag of the CPU.
        """
        self.status &= 0b11110111

    def cli(self) -> None:
        """
        Clears the interrupt flag of the CPU.
        """
        self.status &= 0b11111011

    def clv(self) -> None:
        """
        Clears the overflow flag of the CPU.
        """
        self.status &= 0b10111111

    def cmp(self, operand: int) -> None:
        """
        Compares the immediate value following the CMP opcode with the
        accumulator of the CPU. The zero flag is set if the values are equal.
        The carry flag is set if the accumulator is greater than the immediate
        value.
        """
        if self.accumulator == operand:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101
        if self.accumulator > operand:
            self.status |= 0b00000001
        else:
            self.status &= 0b11111110

    def cpx(self, operand: int) -> None:
        """
        Compares the immediate value following the CPX opcode with the X
        register of the CPU. The zero flag is set if the values are equal. The
        carry flag is set if the X register is greater than the immediate
        value.
        """
        if self.x_register == operand:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101
        if self.x_register > operand:
            self.status |= 0b00000001
        else:
            self.status &= 0b11111110

    def cpy(self, operand: int) -> None:
        """
        Compares the immediate value following the CPY opcode with the Y
        register of the CPU. The zero flag is set if the values are equal. The
        carry flag is set if the Y register is greater than the immediate
        value.
        """
        if self.y_register == operand:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101
        if self.y_register > operand:
            self.status |= 0b00000001
        else:
            self.status &= 0b11111110

    def dec(self, operand: int) -> None:
        """
        Decrements the value at the address following the DEC opcode by one.
        """
        operand -= 1

    def dex(self) -> None:
        """
        Decrements the X register of the CPU by one.
        """
        self.x_register -= 1

    def dey(self) -> None:
        """
        Decrements the Y register of the CPU by one.
        """
        self.y_register -= 1

    def eor(self, operand: int) -> None:
        """
        Performs a bitwise XOR operation on the immediate value following the
        EOR opcode and the accumulator of the CPU.
        """
        self.accumulator ^= operand

    def inc(self, operand: int) -> None:
        """
        Increments the value at the address following the INC opcode by one.
        """
        operand += 1

    def inx(self) -> None:
        """
        Increments the X register of the CPU by one.
        """
        self.x_register += 1

    def iny(self) -> None:
        """
        Increments the Y register of the CPU by one.
        """
        self.y_register += 1

    def jmp(self, operand: int) -> None:
        """
        Jumps to the address following the JMP opcode.
        """
        self.program_counter = operand

    def jsr(self, operand: int) -> None:
        """
        Pushes the address of the next instruction to the stack and jumps to
        the address following the JSR opcode.
        """
        self.stack_push(self.program_counter)
        self.program_counter = operand

    def lda(self, operand: int) -> None:
        """
        Loads the immediate value following the LDA opcode into the accumulator
        of the CPU. The zero flag is set if the accumulator is zero. The
        negative flag is set if the accumulator is negative.
        """
        self.accumulator = operand
        if self.accumulator == 0:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101
        if self.accumulator & 0b10000000:
            self.status |= 0b10000000
        else:
            self.status &= 0b01111111

    def ldx(self, operand: int) -> None:
        """
        Loads the immediate value following the LDX opcode into the X register
        of the CPU. The zero flag is set if the X register is zero. The
        negative flag is set if the X register is negative.
        """
        self.x_register = operand
        if self.x_register == 0:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101
        if self.x_register & 0b10000000:
            self.status |= 0b10000000
        else:
            self.status &= 0b01111111

    def ldy(self, operand: int) -> None:
        """
        Loads the immediate value following the LDY opcode into the Y register
        of the CPU. The zero flag is set if the Y register is zero. The
        negative flag is set if the Y register is negative.
        """
        self.y_register = operand
        if self.y_register == 0:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101
        if self.y_register & 0b10000000:
            self.status |= 0b10000000
        else:
            self.status &= 0b01111111

    def lsr(self, operand: int) -> None:
        """
        Shifts the immediate value following the LSR opcode one bit to the
        right. The zero flag is set if the value is zero. The carry flag is set
        if the value is odd.
        """
        if operand & 0b00000001:
            self.status |= 0b00000001
        else:
            self.status &= 0b11111110
        operand >>= 1
        if operand == 0:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101

    def nop(self) -> None:
        """
        Does nothing.
        """
        pass

    def ora(self, operand: int) -> None:
        """
        Performs a bitwise OR operation on the immediate value following the
        ORA opcode and the accumulator of the CPU. The zero flag is set if the
        accumulator is zero. The negative flag is set if the accumulator is
        negative.
        """
        self.accumulator |= operand
        if self.accumulator == 0:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101
        if self.accumulator & 0b10000000:
            self.status |= 0b10000000
        else:
            self.status &= 0b01111111

    def pha(self) -> None:
        """
        Pushes the accumulator of the CPU to the stack.
        """
        self.stack_push(self.accumulator)

    def php(self) -> None:
        """
        Pushes the status register of the CPU to the stack.
        """
        self.stack_push(self.status)

    def pla(self) -> None:
        """
        Pops the stack and loads the value into the accumulator of the CPU. The
        zero flag is set if the accumulator is zero. The negative flag is set
        if the accumulator is negative.
        """
        self.accumulator = self.stack_pop()
        if self.accumulator == 0:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101
        if self.accumulator & 0b10000000:
            self.status |= 0b10000000
        else:
            self.status &= 0b01111111

    def plp(self) -> None:
        """
        Pops the stack and loads the value into the status register of the CPU.
        """
        self.status = self.stack_pop()

    def rol(self, operand: int) -> None:
        """
        Shifts the immediate value following the ROL opcode one bit to the left
        and adds the carry flag. The zero flag is set if the value is zero. The
        carry flag is set if the value is odd.
        """
        if self.status & 0b00000001:
            operand |= 0b10000000
        else:
            operand &= 0b01111111
        if operand & 0b10000000:
            self.status |= 0b00000001
        else:
            self.status &= 0b11111110
        operand <<= 1
        if operand == 0:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101

    def ror(self, operand: int) -> None:
        """
        Shifts the immediate value following the ROR opcode one bit to the
        right and adds the carry flag. The zero flag is set if the value is
        zero. The carry flag is set if the value is odd.
        """
        if self.status & 0b00000001:
            operand |= 0b10000000
        else:
            operand &= 0b01111111
        if operand & 0b00000001:
            self.status |= 0b00000001
        else:
            self.status &= 0b11111110
        operand >>= 1
        if operand == 0:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101

    def rti(self) -> None:
        """
        Pops the stack and loads the value into the status register of the CPU.
        Pops the stack and loads the value into the program counter of the CPU.
        """
        self.status = self.stack_pop()
        self.program_counter = self.stack_pop()

    def rts(self) -> None:
        """
        Pops the stack and loads the value into the program counter of the CPU.
        """
        self.program_counter = self.stack_pop()

    def sbc(self, operand: int) -> None:
        """
        Subtracts the immediate value following the SBC opcode from the
        """
        operand = operand ^ 0b11111111
        self.adc(operand)

    def sec(self) -> None:
        """
        Sets the carry flag of the CPU.
        """
        self.status |= 0b00000001

    def sed(self) -> None:
        """
        Sets the decimal flag of the CPU.
        """
        self.status |= 0b00001000

    def sei(self) -> None:
        """
        Sets the interrupt disable flag of the CPU.
        """
        self.status |= 0b00000100

    def sta(self, operand: int) -> None:
        """
        Stores the accumulator of the CPU in the memory location following the
        STA opcode.
        """
        self.memory.memory[operand] = self.accumulator

    def stx(self, operand: int) -> None:
        """
        Stores the X register of the CPU in the memory location following the
        STX opcode.
        """
        self.memory.memory[operand] = self.x_register

    def sty(self, operand: int) -> None:
        """
        Stores the Y register of the CPU in the memory location following the
        STY opcode.
        """
        self.memory.memory[operand] = self.y_register

    def tax(self) -> None:
        """
        Loads the accumulator of the CPU into the X register. The zero flag is
        set if the X register is zero. The negative flag is set if the X
        register is negative.
        """
        self.x_register = self.accumulator
        if self.x_register == 0:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101
        if self.x_register & 0b10000000:
            self.status |= 0b10000000
        else:
            self.status &= 0b01111111

    def tay(self) -> None:
        """
        Loads the accumulator of the CPU into the Y register. The zero flag is
        set if the Y register is zero. The negative flag is set if the Y
        register is negative.
        """
        self.y_register = self.accumulator
        if self.y_register == 0:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101
        if self.y_register & 0b10000000:
            self.status |= 0b10000000
        else:
            self.status &= 0b01111111

    def tsx(self) -> None:
        """
        Loads the stack pointer of the CPU into the X register. The zero flag
        is set if the X register is zero. The negative flag is set if the X
        register is negative.
        """
        self.x_register = self.stack_pointer
        if self.x_register == 0:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101
        if self.x_register & 0b10000000:
            self.status |= 0b10000000
        else:
            self.status &= 0b01111111

    def txa(self) -> None:
        """
        Loads the X register of the CPU into the accumulator. The zero flag is
        set if the accumulator is zero. The negative flag is set if the
        accumulator is negative.
        """
        self.accumulator = self.x_register
        if self.accumulator == 0:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101
        if self.accumulator & 0b10000000:
            self.status |= 0b10000000
        else:
            self.status &= 0b01111111

    def txs(self) -> None:
        """
        Loads the X register of the CPU into the stack pointer.
        """
        self.stack_pointer = self.x_register

    def tya(self) -> None:
        """
        Loads the Y register of the CPU into the accumulator. The zero flag is
        set if the accumulator is zero. The negative flag is set if the
        accumulator is negative.
        """
        self.accumulator = self.y_register
        if self.accumulator == 0:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101
        if self.accumulator & 0b10000000:
            self.status |= 0b10000000
        else:
            self.status &= 0b01111111

    def stack_push(self, value: int) -> None:
        """
        Pushes a value onto the stack of the CPU.
        """
        self.memory.memory[self.stack_pointer + 0x100] = value
        self.stack_pointer -= 1

    def stack_pop(self) -> int:
        """
        Pops a value from the stack of the CPU.
        """
        self.stack_pointer += 1
        return self.memory.memory[self.stack_pointer + 0x100]

    def get_operand(self, addressing_mode: int) -> int:
        """
        Returns the operand for the opcode of the CPU.
        """
        if addressing_mode == 0b000:
            return self.memory.memory[self.program_counter]
        elif addressing_mode == 0b001:
            return self.memory.memory[self.memory.memory[self.program_counter]]
        elif addressing_mode == 0b010:
            return self.memory.memory[self.memory.memory[self.program_counter] + self.x_register]
        elif addressing_mode == 0b011:
            return self.memory.memory[self.memory.memory[self.program_counter] + self.y_register]
        elif addressing_mode == 0b100:
            return self.memory.memory[self.program_counter + self.x_register]
        elif addressing_mode == 0b101:
            return self.memory.memory[self.program_counter + self.y_register]
        elif addressing_mode == 0b110:
            return self.memory.memory[self.program_counter + self.memory.memory[self.program_counter + 1]]
        elif addressing_mode == 0b111:
            return self.memory.memory[
                self.program_counter + self.memory.memory[self.program_counter + 1] + self.x_register
            ]
        else:
            raise RuntimeError("Invalid addressing mode.")
