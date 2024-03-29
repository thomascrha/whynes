import enum
from pathlib import Path
from typing import Callable, Dict, List

# from cpu import CPU

"""
 def BMI(self, value):
        # Branch on Result Minus
        if self.get_flag(Flag.NEGATIVE) == 1:
            self.program_counter = value

    def BNE(self, value):
        # Branch on Result not Zero
        # Fetch the value from memory based on the addressing mode
        if self.get_flag(Flag.ZERO) == 0:
            self.program_counter = value

    def BPL(self, value):
        # Branch on Result Plus
        if self.get_flag(Flag.NEGATIVE) == 0:
            self.program_counter = value
    def BVC(self, value):
        # Branch on Overflow Clear
        if self.get_flag(Flag.OVERFLOW) == 0:
            self.program_counter += value

    def BVS(self, value):
        # Branch on Overflow Set
        if self.get_flag(Flag.OVERFLOW) == 1:
            self.program_counter += value

    def BCC(self, value):
        # Branch on Carry Clear
        if self.get_flag(Flag.CARRY) == 0:
            self.program_counter += value

    def BCS(self, value):
        # Branch on Carry Set
        # branch on C = 1

        if self.get_flag(Flag.CARRY) == 1:
            self.program_counter += value

    def BEQ(self, value):
        # Branch on Result Zero
        if self.get_flag(Flag.ZERO) == 1:
            self.program_counter += value


"""

class AddressingModes(str, enum.Enum):
    IMPLIED = "IMPLIED"
    ACCUMULATOR = "ACCUMULATOR"
    IMMEDIATE = "IMMEDIATE"
    ABSOLUTE = "ABSOLUTE"
    X_INDEXED_ABSOLUTE = "X_INDEXED_ABSOLUTE"
    Y_INDEXED_ABSOLUTE = "Y_INDEXED_ABSOLUTE"
    ABSOLUTE_INDIRECT = "ABSOLUTE_INDIRECT"
    ZERO_PAGE = "ZERO_PAGE"
    X_INDEXED_ZERO_PAGE = "X_INDEXED_ZERO_PAGE"
    Y_INDEXED_ZERO_PAGE = "Y_INDEXED_ZERO_PAGE"
    X_INDEXED_ZERO_PAGE_INDIRECT = "X_INDEXED_ZERO_PAGE_INDIRECT"
    ZERO_PAGE_INDIRECT_Y_INDEXED = "ZERO_PAGE_INDIRECT_Y_INDEXED"
    RELATIVE = "RELATIVE"


class Opcodes(str, enum.Enum):
    ADC = "ADC"
    AND = "AND"
    ASL = "ASL"
    BCC = "BCC"
    BCS = "BCS"
    BEQ = "BEQ"
    BIT = "BIT"
    BMI = "BMI"
    BNE = "BNE"
    BPL = "BPL"
    BRK = "BRK"
    BVC = "BVC"
    BVS = "BVS"
    CLC = "CLC"
    CLD = "CLD"
    CLI = "CLI"
    CLV = "CLV"
    CMP = "CMP"
    CPX = "CPX"
    CPY = "CPY"
    DEC = "DEC"
    DEX = "DEX"
    DEY = "DEY"
    EOR = "EOR"
    INC = "INC"
    INX = "INX"
    INY = "INY"
    JMP = "JMP"
    JSR = "JSR"
    LDA = "LDA"
    LDX = "LDX"
    LDY = "LDY"
    LSR = "LSR"
    NOP = "NOP"
    ORA = "ORA"
    PHA = "PHA"
    PHP = "PHP"
    PLA = "PLA"
    PLP = "PLP"
    ROL = "ROL"
    ROR = "ROR"
    RTI = "RTI"
    RTS = "RTS"
    SBC = "SBC"
    SEC = "SEC"
    SED = "SED"
    SEI = "SEI"
    STA = "STA"
    STX = "STX"
    STY = "STY"
    TAX = "TAX"
    TAY = "TAY"
    TSX = "TSX"
    TXA = "TXA"
    TXS = "TXS"
    TYA = "TYA"


class Instruction:
    def __init__(
        self,
        opcode: Opcodes,
        opcode_hex: str,
        addressing_mode: AddressingModes,
        no_bytes: int,
        run: Callable,
        cycles: int,
        cycle_flags: List[str],
        assembly: str = "",
        assembly_hex: str = "",
    ) -> None:
        self.opcode = opcode
        self.opcode_hex = opcode_hex
        self.addressing_mode = addressing_mode
        self.cycles = cycles
        self.cycle_flags = cycle_flags
        self.no_bytes = no_bytes
        self.assembly = assembly
        self.assembly_hex = assembly_hex
        self.run = run

    def __str__(self) -> str:
        return f"{self.opcode} - {self.addressing_mode} - {self.no_bytes}"


def parse_opcode_addressing_mode(cpu: "CPU", table: List[str], opcode_name: str) -> Dict[int, Instruction]:
    table_headers = table[0].split("\t")
    opcodes = {}
    for opcode in table[1:]:
        row = dict(zip(table_headers, opcode.split("\t")))
        # remove the first character from the opcode (the $) and convert
        # it to an int
        key = int("".join(row["Opcode"][1:]), 16)
        addressing_mode = row["Addressing Mode"].replace(" ", "_").replace("-", "_").upper()
        cycles = row["No. Cycles"]
        cycle_flags = []
        if "+" in cycles:
            cycles = cycles.split("+")
            cycle_flags = cycles[1:]
            cycles = cycles[:1][0]

        opcodes[key] = Instruction(
            opcode=getattr(Opcodes, opcode_name.upper()),
            run=getattr(cpu, opcode_name.upper()),
            addressing_mode=getattr(AddressingModes, addressing_mode),
            no_bytes=int(row["No. Bytes"]),
            opcode_hex=hex(key).split("x")[1:][0],
            cycles=int(cycles),
            cycle_flags=cycle_flags,
        )

    return opcodes


def load_opcodes(cpu: "CPU", file_path: Path = Path("src/instructions.txt")) -> Dict[int, Instruction]:
    """
    Reads in the file instructions.txt and parses the opcode table.

    Each instruction table is seperated by a blank line - intially we split the
    file using this blank line. Each table is then sent to another function for
    parsing.

    The returned struture is a dictionary where the key is the opcodes HEX
    reperesentation and the value is an instruction object. This object contains
    (mostly) all the information needed to execute the instruction.
    """

    with open(file_path, "r") as f:
        opcodes = ",".join(f.readlines())
        opcodes = opcodes.split("\n,\n,")
        opcodes = [opcode.split("\n,") for opcode in opcodes]

    _opcodes = {}
    for opcode in opcodes:
        opcode_name = getattr(Opcodes, opcode[0].split(" - ")[0])
        _opcodes = {**_opcodes, **parse_opcode_addressing_mode(cpu, opcode[1:], opcode_name)}

    return _opcodes
