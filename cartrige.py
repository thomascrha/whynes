import enum
import sys
from typing import Annotated, List
from logger import get_logger
from pydantic import FilePath


class CartridgeFormat(str, enum.Enum):
    ines = "iNES1.0"
    nes20 = "NES2.0"
    ines07 = "iNES0.7"
    archaicines = "ArchaiciNES"


class HeaderFlags6(enum.Flag):
    """Flags 6

    76543210
    ||||||||
    |||||||+- Mirroring: 0: horizontal (vertical arrangement) (CIRAM A10 = PPU A11)
    |||||||              1: vertical (horizontal arrangement) (CIRAM A10 = PPU A10)
    ||||||+-- 1: Cartridge contains battery-backed PRG RAM ($6000-7FFF) or other persistent memory
    |||||+--- 1: 512-byte trainer at $7000-$71FF (stored before PRG data)
    ||||+---- 1: Ignore mirroring control or above mirroring bit; instead provide four-screen VRAM
    ++++----- Lower nybble of mapper number

    https://www.nesdev.org/wiki/INES
    """

    MIRRORING_HORIZONTAL = 0
    MIRRORING_VERTICAL = 1
    BATTERY = 2
    TRAINER = 4
    IGNORE_MIRRORING = 8
    LOWER_NYBBLE_MAPPER_NO_0 = 16
    LOWER_NYBBLE_MAPPER_NO_1 = 32
    LOWER_NYBBLE_MAPPER_NO_2 = 64
    LOWER_NYBBLE_MAPPER_NO_3 = 128


class HeaderFlags7(enum.Flag):
    """Flags 7

    76543210
    ||||||||
    |||||||+- VS Unisystem
    ||||||+-- PlayChoice-10 (8KB of Hint Screen data stored after CHR data)
    ||||++--- If equal to 2, flags 8-15 are in NES 2.0 format
    ++++----- Upper nybble of mapper number

    https://www.nesdev.org/wiki/INES
    """


class HeaderFlags9iNES(enum.Flag):
    """Flags 9

    76543210
    ||||||||
    |||||||+- TV system (0: NTSC; 1: PAL)
    +++++++-- Reserved, set to zero

    https://www.nesdev.org/wiki/INES
    """

    NTSC = 0
    PAL = 1
    REVERSED_0 = 2
    REVERSED_1 = 4
    REVERSED_2 = 8
    REVERSED_3 = 16
    REVERSED_4 = 32
    REVERSED_5 = 64
    REVERSED_6 = 128


HEX_16 = 0x10
HEX_8 = 0x08

KB = 1024


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

    type: CartridgeFormat
    header: Annotated[List[bytes], HEX_16]
    prg_rom: List[bytes]
    chr_rom: List[bytes]
    prg_rom_size: int
    chr_rom_size: int
    prg_rom_size_multiplier: int
    chr_rom_size_multiplier: int

    def __init__(self, rom_path: FilePath):
        self.logger = get_logger(self.__class__.__name__)

        self.rom_path = rom_path
        self.raw_bytes = self.validate(self.rom_path)
        self.type = self.identify()

        self.logger.debug(f"The ROM at {self.rom_path} is of type {self.type}")

        self.load()

    def load(self):
        self.header = self.raw_bytes[:HEX_16]

        self.prg_rom_size_multiplier = self.header[4]
        self.prg_rom_size = self.prg_rom_size_multiplier * HEX_16

        self.chr_rom_size_multiplier = self.header[5]
        self.chr_rom_size = self.chr_rom_size_multiplier * HEX_8

        # print(HeaderFlags6(self.header[6]))

        self.logger.info(f"The PRG ROM size is {int(self.prg_rom_size_multiplier)}x16Kb = {hex(self.prg_rom_size)}")
        self.logger.info(f"The CHR ROM size is {int(self.chr_rom_size_multiplier)}x8Kb = {hex(self.prg_rom_size)}")

        if self.type in [CartridgeFormat.ines, CartridgeFormat.ines07]:
            self.logger.info(HeaderFlags6(self.header[6]))
            self.logger.info(HeaderFlags9iNES(self.header[9]))

        # PRG ROM is contained in 16Kb chunks after the header
        self.prg_rom = self.raw_bytes[HEX_16 : (HEX_16 * KB) * self.prg_rom_size_multiplier]

        # CHR ROM is contained in 8kb chunks after the header and the PGR ROM
        self.chr_rom = self.raw_bytes[
            HEX_16 + (HEX_16 * KB) * self.prg_rom_size_multiplier : (HEX_8 * KB) * self.chr_rom_size_multiplier
        ]

    def validate(self, rom_path) -> List[bytes]:
        # Only accept either iNes or NES2.0 type files
        # https://www.nesdev.org/wiki/NES_2.0

        with open(rom_path, "rb") as raw_bytes:
            raw_bytes = raw_bytes.read()

        # this is true of ALL the NES rom formats - if this true then the ROM file provided is upto spec
        if not (
            chr(raw_bytes[0]) == "N" and chr(raw_bytes[1]) == "E" and chr(raw_bytes[2]) == "S" and raw_bytes[3] == 0x1A
        ):
            self.logger.critical(f"The provided ROM file {rom_path} can't be identified")
            sys.exit(1)

        return raw_bytes

    def identify(self) -> CartridgeFormat:
        """Recommended detection procedure:

        If byte 7 AND $0C = $08, and the size taking into account byte 9 does not exceed the actual size of the ROM
            image, then NES 2.0.
        If byte 7 AND $0C = $04, archaic iNES.
        If byte 7 AND $0C = $00, and bytes 12-15 are all 0, then iNES.
        Otherwise, iNES 0.7 or archaic iNES.
        """
        type = CartridgeFormat.ines07

        if (self.raw_bytes[7] & 0x0C) == 0x08:
            type = CartridgeFormat.nes20

        if (self.raw_bytes[7] & 0x0C) == 0x04:
            type = CartridgeFormat.archaicines

        if (
            (self.raw_bytes[7] & 0x0C) == 0x00
            and self.raw_bytes[13] == 0x00
            and self.raw_bytes[14] == 0x00
            and self.raw_bytes[15] == 0x00
            and self.raw_bytes[16] == 0x00
        ):
            type = CartridgeFormat.ines

        return type
