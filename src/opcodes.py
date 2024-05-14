from pathlib import Path
from typing import  Dict, List
from constants import AddressingMode
script_directory = Path(__file__).parent.resolve()

class Opcode:
    code: int
    mnemonic: str
    length: int
    cycles: int
    mode: AddressingMode

    def __init__(self, code, mnemonic, length, cycles, mode):
        self.code = code
        self.mnemonic = mnemonic
        self.length = length
        self.cycles = cycles
        self.mode = mode

    @staticmethod
    def load_opcodes(file_path: Path = Path(__file__).parent.resolve() / "opcodes.txt") -> Dict[int, "Opcode"]:
        """
        Reads in the file instructions.txt and parses the opcode table.

        Each instruction table is seperated by a blank line - intially we split the
        file using this blank line. Each table is then sent to another function for
        parsing.

        The returned struture is a dictionary where the key is the opcodes HEX
        reperesentation and the value is an instruction object. This object contains
        (mostly) all the information needed to execute the instruction.
        """
        def parse_opcode_table(table: List[str]) -> Dict[int, Opcode]:
            table_headers = table[0].split("\t")
            opcodes = {}
            for opcode in table[1:]:
                row = dict(zip(table_headers, opcode.split("\t")))
                # remove the first character from the opcode (the $) and convert
                # it to an int
                code = int("".join(row["Opcode"][1:]), 16)
                addressing_mode = getattr(AddressingMode, row["Addressing Mode"].replace(" ", "_").replace("-", "_").upper())
                cycles = int(row["No. Cycles"].split("+")[0])
                length = int(row["No. Bytes"])
                mnemonic = row["Assembly Language Form"]

                opcodes[code] = Opcode(
                    code=code,
                    mode=addressing_mode,
                    cycles=cycles,
                    mnemonic=mnemonic,
                    length=length
                )
            return opcodes

        with open(file_path, "r") as f:
            opcodes = ",".join(f.readlines())
            opcodes = opcodes.split("\n,\n,")
            opcodes = [opcode.split("\n,") for opcode in opcodes]

        _opcodes = {}
        for opcode in opcodes:
            _opcodes = {**_opcodes, **parse_opcode_table(opcode[1:])}

        return _opcodes

