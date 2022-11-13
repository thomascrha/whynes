import argparse
import enum
from typing import List, Annotated
from pydantic import FilePath

from logger import get_logger


class CartridgeFormat(str, enum.Enum):
    ines = "iNESFormat"
    nes20 = "NES20Format"


HEX_16 = 0x10
HEX_8 = 0x08

KB = 1024


class Cartridge:
    type: CartridgeFormat
    header: Annotated[List[bytes], HEX_16]
    prg_rom: List[bytes]
    chr_rom: List[bytes]

    def __init__(self, rom_path: FilePath):
        self.rom_path = rom_path
        self.logger = get_logger(self.__class__.__name__)
        self.load()

        if self.valid is False:
            raise Exception("The provided ROM file can't be identified")

        self.logger.info(f"The ROM at {self.rom_path} is of type {self.type}")
        line = ""
        for i, _byte in enumerate(self.raw_bytes):
            if i % 16 == 0:
                self.logger.debug(line)
                line = ""

            line += " {}".format(hex(_byte))

    @property
    def type(self) -> CartridgeFormat:
        if not hasattr(self, "_type"):
            self.validate()
        return self._type

    @property
    def valid(self) -> bool:
        if not hasattr(self, "_valid"):
            self.validate()

        return self._valid

    def load(self):
        with open(self.rom_path, "rb") as raw_bytes:
            self.raw_bytes = raw_bytes.read()

        self.header = self.raw_bytes[:HEX_16]

        self.prg_rom_size_multiplier = self.header[4]
        self.prg_rom_size = self.prg_rom_size_multiplier * HEX_16

        self.chr_rom_size_multiplier = self.header[5]
        self.chr_rom_size = self.chr_rom_size_multiplier * HEX_8

        self.logger.info(
            f"The PRG ROM size is {int(self.prg_rom_size_multiplier)}x16Kb = {hex(self.prg_rom_size)}"
        )
        self.logger.info(
            f"The CHR ROM size is {int(self.chr_rom_size_multiplier)}x8Kb = {hex(self.prg_rom_size)}"
        )

        # PRG ROM is contained in 16Kb chunks after the header
        self.prg_rom = self.raw_bytes[
            HEX_16 : (HEX_16 * KB) * self.prg_rom_size_multiplier
        ]

        # CHR ROM is contained in 8kb chunks after the header and the PGR ROM
        self.chr_rom = self.raw_bytes[
            HEX_16
            + (HEX_16 * KB)
            * self.prg_rom_size_multiplier : (HEX_8 * KB)
            * self.chr_rom_size_multiplier
        ]

    def validate(self) -> None:
        # Only accept either iNes or NES2.0 type files
        # https://www.nesdev.org/wiki/NES_2.0

        self._valid = False

        # if (header[0]=='N' && header[1]=='E' && header[2]=='S' && header[3]==0x1A)
        #         iNESFormat=true;
        if (
            chr(self.raw_bytes[0]) == "N"
            and chr(self.raw_bytes[1]) == "E"
            and chr(self.raw_bytes[2]) == "S"
            and self.raw_bytes[3] == 0x1A
        ):
            self._valid = True
            self._type = CartridgeFormat.ines

        # if (iNESFormat==true && (header[7]&0x0C)==0x08)
        #         NES20Format=true;
        if self.type == CartridgeFormat.ines and (self.raw_bytes[7] & 0x0C) == 0x08:
            self._type = CartridgeFormat.nes20


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-r",
        "--rom-path",
        type=str,
        help="The filepath of the rom being loaded into the cartridge",
    )

    args = parser.parse_args()

    cart = Cartridge(**args.__dict__)
