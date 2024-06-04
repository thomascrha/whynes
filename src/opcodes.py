from pathlib import Path
from typing import Dict, List
from constants import AddressingMode


class Opcode:
    code: int
    mnemonic: str
    length: int
    cycles: int
    addressing_mode: AddressingMode
    opcode_params: int

    def __init__(self, code, mnemonic, length, cycles, mode, opcode_params=0):
        self.code = code
        self.mnemonic = mnemonic
        self.length = length
        self.cycles = cycles
        self.addressing_mode = mode

        self.opcode_params = opcode_params

    def string(self, memory: "Memory") -> str:
        """
        I always forget this stuff
        {   # Format identifier
        0:  # first parameter
        0   # fill with zeroes
        {1} # to a length of n characters (including 0x), defined by the second parameter
        x   # hexadecimal number, using lowercase letters for a-f
        }   # End of format identifier
        """
        if self.length == 1:
            string = self.mnemonic
        elif self.length == 2:
            # string = self.mnemonic.replace("nn", f"{(program_offset - self.opcode_params):0{2}X}")
            params = self.opcode_params
            if self.addressing_mode == AddressingMode.IMMEDIATE:
                params = memory.read(self.opcode_params)
            string = self.mnemonic.replace("nn", f"{(params):0{2}X}")
        elif self.length == 3:
            # string = self.mnemonic.replace("nnnn", f"{(program_offset - self.opcode_params):0{4}X}")
            string = self.mnemonic.replace("nnnn", f"{(self.opcode_params):0{4}X}")
        else:
            raise ValueError("Invalid length")

        return string

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

                opcodes[code] = Opcode(code=code, mode=addressing_mode, cycles=cycles, mnemonic=mnemonic, length=length)
            return opcodes

        with open(file_path, "r") as f:
            opcodes = ",".join(f.readlines())
            opcodes = opcodes.split("\n,\n,")
            opcodes = [opcode.split("\n,") for opcode in opcodes]

        _opcodes = {}
        for opcode in opcodes:
            _opcodes = {**_opcodes, **parse_opcode_table(opcode[1:])}

        return _opcodes


# from cpu import Memory
