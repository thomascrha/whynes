import sys
from enum import Enum
from pydantic import FilePath
from constants import HEX_8, HEX_16, KB, CartridgeFormat, HeaderFlags6, HeaderFlags9iNES
from logger import get_logger

logger = get_logger(__name__)


class Mirroring(str, Enum):
    VERTICAL = "Vertical"
    HORIZONTAL = "Horizontal"
    FOUR_SCREEN = "Four Screen"


class Cartridge:
    """A class that defines the specification of a 'virtual' cartridge - fundamentally it implements whats defined
    in the iNES and NES2.0 file format specs for detailing how the ROM file is constructed.

    https://www.nesdev.org/wiki/INES
    https://www.nesdev.org/wiki/NES_2.0

    * Loads the rom from a file and determines if the file provided is valid
    * utilising the header determine the size of the PGR and CHR ROM

    Raises:
        Exception: if the specified rom file is not determined to be in the iiNES or NES2.0 format

    Returns:
        Cartridge
    """

    rom_path: FilePath
    raw_bytes: bytearray

    type_: CartridgeFormat
    header: bytearray
    program_rom: bytearray
    character_rom: bytearray
    program_rom_size: int
    character_rom_size: int
    program_rom_size_multiplier: int
    character_rom_size_multiplier: int

    mapper_type: int
    screen_mirroring: Mirroring

    def __init__(self, rom_path: FilePath) -> None:
        self.rom_path = rom_path
        self.raw_bytes = self.validate(self.rom_path)
        self.type_ = self.identify()

        logger.debug(f"The ROM at {self.rom_path} is of type {self.type}")

        self.header = self.raw_bytes[:HEX_16]

        self.program_rom_size_multiplier = self.header[4]
        self.program_rom_size = self.program_rom_size_multiplier * HEX_16

        self.character_rom_size_multiplier = self.header[5]
        self.character_rom_size = self.character_rom_size_multiplier * HEX_8

        logger.debug(f"The PRG ROM size is {int(self.program_rom_size_multiplier)}x16Kb = {hex(self.program_rom_size)}")
        logger.debug(f"The CHR ROM size is {int(self.character_rom_size_multiplier)}x8Kb = {hex(self.character_rom_size)}")

        if self.type_ in [CartridgeFormat.ines, CartridgeFormat.ines07]:
            logger.debug(HeaderFlags6(self.header[6]))
            logger.debug(HeaderFlags9iNES(self.header[9]))

        # PRG ROM is contained in 16Kb chunks after the header
        self.program_rom = self.raw_bytes[HEX_16 : (HEX_16 * KB) * self.program_rom_size_multiplier]

        # CHR ROM is contained in 8kb chunks after the header and the PGR ROM
        self.character_rom = self.raw_bytes[HEX_16 + (HEX_16 * KB) * self.program_rom_size_multiplier : (HEX_8 * KB) * self.character_rom_size_multiplier]

        self.mapper = (self.header[7] & 0b1111_0000) | (self.header[6] >> 4)

        four_screen = self.header[6] & 0b1000 != 0
        vertical_mirroring = self.header[6] & 0b1 != 0

        self.screen_mirroring = Mirroring.FOUR_SCREEN if four_screen else Mirroring.VERTICAL if vertical_mirroring else Mirroring.HORIZONTAL

    def validate(self, rom_path: FilePath) -> bytearray:
        # Only accept either iNes or NES2.0 type files
        # https://www.nesdev.org/wiki/NES_2.0

        with open(rom_path, "rb") as _raw_bytes:
            raw_bytes = _raw_bytes.read()

        # this is true of ALL the NES rom formats - if this true then the ROM file provided is upto spec
        if not (chr(raw_bytes[0]) == "N" and chr(raw_bytes[1]) == "E" and chr(raw_bytes[2]) == "S" and raw_bytes[3] == 0x1A):
            logger.critical(f"The provided ROM file {rom_path} can't be identified")
            sys.exit(1)

        return bytearray(raw_bytes)

    def identify(self) -> CartridgeFormat:
        """Recommended detection procedure:

        If byte 7 AND $0C = $08, and the size taking into account byte 9 does not exceed the actual size of the ROM
            image, then NES 2.0.
        If byte 7 AND $0C = $04, archaic iNES.
        If byte 7 AND $0C = $00, and bytes 12-15 are all 0, then iNES.
        Otherwise, iNES 0.7 or archaic iNES.
        """
        type_ = CartridgeFormat.ines07

        if (self.raw_bytes[7] & 0x0C) == 0x08:
            type_ = CartridgeFormat.nes20

        if (self.raw_bytes[7] & 0x0C) == 0x04:
            type_ = CartridgeFormat.archaicines

        if (self.raw_bytes[7] & 0x0C) == 0x00 and self.raw_bytes[13] == 0x00 and self.raw_bytes[14] == 0x00 and self.raw_bytes[15] == 0x00 and self.raw_bytes[16] == 0x00:
            type_ = CartridgeFormat.ines

        return type_
