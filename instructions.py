import enum
from typing import Optional, Tuple, Union


class Opcode:
    def __init__(self, hex_value: int, mnemonic: str, argument_length: int):
        self.hex_value = hex_value
        self.mnemonic = mnemonic
        self.argument_length = argument_length

    def __str__(self):
        return f"{self.mnemonic} ({hex(self.hex_value)}) * {self.argument_length} bytes"


class Instruction:
    def __init__(self, opcode: Opcode, process, operand: Optional[int] = None):
        self.opcode = opcode
        self.operand = operand
        self.process = process

    def __str__(self):
        return f"{self.opcode} ({hex(self.operand)})"


class Instructions:
    """
    https://www.masswerk.at/6502/6502_instruction_set.html
    """

    class Opcodes(enum.Enum):
        ADC = Opcode(0x69, "ADC", 1)  # Add with Carry
        AND = Opcode(0x29, "AND", 1)  # Logical AND
        ASL = Opcode(0x0A, "ASL", 0)  # Arithmetic Shift Left
        BCC = Opcode(0x90, "BCC", 1)  # Branch if Carry Clear
        BCS = Opcode(0xB0, "BCS", 1)  # Branch if Carry Set
        BEQ = Opcode(0xF0, "BEQ", 1)  # Branch if Equal
        BIT = Opcode(0x24, "BIT", 1)  # Bit Test
        BMI = Opcode(0x30, "BMI", 1)  # Branch if Minus
        BNE = Opcode(0xD0, "BNE", 1)  # Branch if Not Equal
        BPL = Opcode(0x10, "BPL", 1)  # Branch if Positive
        BRK = Opcode(0x00, "BRK", 0)  # Force Interrupt
        BVC = Opcode(0x50, "BVC", 1)  # Branch if Overflow Clear
        BVS = Opcode(0x70, "BVS", 1)  # Branch if Overflow Set
        CLC = Opcode(0x18, "CLC", 0)  # Clear Carry Flag
        CLD = Opcode(0xD8, "CLD", 0)  # Clear Decimal Mode
        CLI = Opcode(0x58, "CLI", 0)  # Clear Interrupt Disable
        CLV = Opcode(0xB8, "CLV", 0)  # Clear Overflow Flag
        CMP = Opcode(0xC9, "CMP", 1)  # Compare
        CPX = Opcode(0xE0, "CPX", 1)  # Compare X Register
        CPY = Opcode(0xC0, "CPY", 1)  # Compare Y Register
        DEC = Opcode(0xC6, "DEC", 1)  # Decrement Memory
        DEX = Opcode(0xCA, "DEX", 0)  # Decrement X Register
        DEY = Opcode(0x88, "DEY", 0)  # Decrement Y Register
        EOR = Opcode(0x49, "EOR", 1)  # Exclusive OR
        INC = Opcode(0xE6, "INC", 1)  # Increment Memory
        INX = Opcode(0xE8, "INX", 0)  # Increment X Register
        INY = Opcode(0xC8, "INY", 0)  # Increment Y Register
        JMP = Opcode(0x4C, "JMP", 1)  # Jump
        JSR = Opcode(0x20, "JSR", 1)  # Jump to Subroutine
        LDA = Opcode(0xA9, "LDA", 1)  # Load Accumulator
        LDX = Opcode(0xA2, "LDX", 1)  # Load X Register
        LDY = Opcode(0xA0, "LDY", 1)  # Load Y Register
        LSR = Opcode(0x4A, "LSR", 0)  # Logical Shift Right
        NOP = Opcode(0xEA, "NOP", 0)  # No Operation
        ORA = Opcode(0x09, "ORA", 1)  # Logical OR
        PHA = Opcode(0x48, "PHA", 0)  # Push Accumulator
        PHP = Opcode(0x08, "PHP", 0)  # Push Processor Status
        PLA = Opcode(0x68, "PLA", 0)  # Pull Accumulator
        PLP = Opcode(0x28, "PLP", 0)  # Pull Processor Status
        ROL = Opcode(0x2A, "ROL", 0)  # Rotate Left
        ROR = Opcode(0x6A, "ROR", 0)  # Rotate Right
        RTI = Opcode(0x40, "RTI", 0)  # Return from Interrupt
        RTS = Opcode(0x60, "RTS", 0)  # Return from Subroutine
        SBC = Opcode(0xE9, "SBC", 1)  # Subtract with Carry
        SEC = Opcode(0x38, "SEC", 0)  # Set Carry Flag
        SED = Opcode(0xF8, "SED", 0)  # Set Decimal Mode
        SEI = Opcode(0x78, "SEI", 0)  # Set Interrupt Disable
        STA = Opcode(0x8D, "STA", 1)  # Store Accumulator
        STX = Opcode(0x8E, "STX", 1)  # Store X Register
        STY = Opcode(0x8C, "STY", 1)  # Store Y Register
        TAX = Opcode(0xAA, "TAX", 0)  # Transfer Accumulator to X
        TAY = Opcode(0xA8, "TAY", 0)  # Transfer Accumulator to Y
        TSX = Opcode(0xBA, "TSX", 0)  # Transfer Stack Pointer to X
        TXA = Opcode(0x8A, "TXA", 0)  # Transfer X to Accumulator
        TXS = Opcode(0x9A, "TXS", 0)  # Transfer X to Stack Pointer
        TYA = Opcode(0x98, "TYA", 0)  # Transfer Y to Accumulator

    @staticmethod
    def get_opcode(opcode_hex) -> Union[Opcodes, Tuple[int, str, int]]:
        # Iterate over the enum members to find the matching opcode and argument length
        for opcode in Instructions.Opcodes:
            if opcode.value.hex_value == opcode_hex:
                return opcode

        return opcode_hex, "UNKNOWN", 0
