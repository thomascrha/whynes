import sys
from enum import Enum
from typing import List
from pydantic import FilePath
from constants import CartridgeFormat, HeaderFlags6, HeaderFlags9iNES
from logger import get_logger

logger = get_logger(__name__)

U16 = 16
U8 = 8
KB = 1024


class Mirroring(str, Enum):
    VERTICAL = "Vertical"
    HORIZONTAL = "Horizontal"
    FOUR_SCREEN = "Four Screen"


class Rom:
    def __init__(self, rom_path: FilePath) -> None:
        self.rom_path = rom_path
        self.raw = self.validate(self.rom_path)

        self.mapper = (self.raw[7] & 0b1111_0000) | (self.raw[6] >> 4)

        four_screen = self.raw[6] & 0b1000 != 0
        vertical_mirroring = self.raw[6] & 0b1 != 0
        self.screen_mirroring = Mirroring.FOUR_SCREEN if four_screen else Mirroring.VERTICAL if vertical_mirroring else Mirroring.HORIZONTAL

        self.prg_rom_size = self.raw[4] * U16
        self.chr_rom_size = self.raw[5] * U8

        skip_trainer = self.raw[6] & 0b100 != 0

        prg_rom_start = U16 + 512 if skip_trainer else U16
        chr_rom_start = prg_rom_start + self.prg_rom_size

        self.program_rom = self.raw[prg_rom_start : prg_rom_start + self.prg_rom_size]
        self.character_rom = self.raw[chr_rom_start : chr_rom_start + self.chr_rom_size]

        logger.debug(f"Mapper type: {self.mapper}")
        logger.debug(f"Screen mirroring: {self.screen_mirroring}")

    def validate(self, rom_path: FilePath) -> List[int]:
        # Only accept either iNes type files
        # https://www.nesdev.org/wiki/NES_2.0

        with open(rom_path, "rb") as _raw_bytes:
            raw_bytes = list(_raw_bytes.read())

        # this is true of ALL the NES rom formats - if this true then the ROM file provided is upto spec
        if not (chr(raw_bytes[0]) == "N" and chr(raw_bytes[1]) == "E" and chr(raw_bytes[2]) == "S" and raw_bytes[3] == 0x1A):
            logger.critical(f"The provided ROM file {rom_path} can't be identified")
            sys.exit(1)

        logger.debug(f"ROM file {rom_path} is a valid NES ROM")
        logger.debug(f"First 4 bytes: {raw_bytes[:4]}")

        if raw_bytes[:4] != [78, 69, 83, 26]:
            logger.critical("File is not in iNES file format")
            sys.exit(1)

        ines_ver = (raw_bytes[7] >> 2) & 0b11
        if ines_ver != 0:
            logger.critical("NES2.0 format is not supported")
            sys.exit(1)

        return raw_bytes


#
# class Cartridge:
#     """A class that defines the specification of a 'virtual' cartridge - fundamentally it implements whats defined
#     in the iNES and NES2.0 file format specs for detailing how the ROM file is constructed.
#
#     https://www.nesdev.org/wiki/INES
#     https://www.nesdev.org/wiki/NES_2.0
#
#     * Loads the rom from a file and determines if the file provided is valid
#     * utilising the header determine the size of the PGR and CHR ROM
#
#     Raises:
#         Exception: if the specified rom file is not determined to be in the iiNES or NES2.0 format
#
#     Returns:
#         Cartridge
#     """
#
#     rom_path: FilePath
#     raw_bytes: List[int]
#
#     type_: CartridgeFormat
#     header: List[int]
#     program_rom: List[int]
#     character_rom: List[int]
#     program_rom_size: int
#     character_rom_size: int
#     program_rom_size_multiplier: int
#     character_rom_size_multiplier: int
#
#     mapper_type: int
#     screen_mirroring: Mirroring
#
#     def __init__(self, rom_path: FilePath) -> None:
#         self.rom_path = rom_path
#         self.raw_bytes = self.validate(self.rom_path)
#         self.type_ = self.identify()
#
#         logger.debug(f"The ROM at {self.rom_path} is of type {self.type_}")
#
#         self.header = self.raw_bytes[:U16]
#
#         self.program_rom_size_multiplier = self.header[4]
#         self.program_rom_size = self.program_rom_size_multiplier * U16
#
#         self.character_rom_size_multiplier = self.header[5]
#         self.character_rom_size = self.character_rom_size_multiplier * U8
#
#         logger.debug(f"The PRG ROM size is {int(self.program_rom_size_multiplier)}x16Kb = {hex(self.program_rom_size)}")
#         logger.debug(f"The CHR ROM size is {int(self.character_rom_size_multiplier)}x8Kb = {hex(self.character_rom_size)}")
#
#         if self.type_ in [CartridgeFormat.ines, CartridgeFormat.ines07]:
#             logger.debug(HeaderFlags6(self.header[6]))
#             logger.debug(HeaderFlags9iNES(self.header[9]))
#
#         # PRG ROM is contained in 16Kb chunks after the header
#         self.program_rom = self.raw_bytes[U16 : (U16 * KB) * self.program_rom_size_multiplier]
#
#         # CHR ROM is contained in 8kb chunks after the header and the PGR ROM
#         self.character_rom = self.raw_bytes[U16 + (U16 * KB) * self.program_rom_size_multiplier : (U8 * KB) * self.character_rom_size_multiplier]
#
#         self.mapper = (self.header[7] & 0b1111_0000) | (self.header[6] >> 4)
#
#         logger.debug(f"Mapper type: {self.mapper}")
#
#         four_screen = self.header[6] & 0b1000 != 0
#         vertical_mirroring = self.header[6] & 0b1 != 0
#
#         self.screen_mirroring = Mirroring.FOUR_SCREEN if four_screen else Mirroring.VERTICAL if vertical_mirroring else Mirroring.HORIZONTAL
#         logger.debug(f"Screen mirroring: {self.screen_mirroring}")
#
#     def identify(self) -> CartridgeFormat:
#         """Recommended detection procedure:
#
#         If byte 7 AND $0C = $08, and the size taking into account byte 9 does not exceed the actual size of the ROM
#             image, then NES 2.0.
#         If byte 7 AND $0C = $04, archaic iNES.
#         If byte 7 AND $0C = $00, and bytes 12-15 are all 0, then iNES.
#         Otherwise, iNES 0.7 or archaic iNES.
#         """
#         type_ = CartridgeFormat.ines07
#
#         if (self.raw_bytes[7] & 0x0C) == 0x08:
#             type_ = CartridgeFormat.nes20
#
#         if (self.raw_bytes[7] & 0x0C) == 0x04:
#             type_ = CartridgeFormat.archaicines
#
#         if (self.raw_bytes[7] & 0x0C) == 0x00 and self.raw_bytes[13] == 0x00 and self.raw_bytes[14] == 0x00 and self.raw_bytes[15] == 0x00 and self.raw_bytes[16] == 0x00:
#             type_ = CartridgeFormat.ines
#
#         return type_
