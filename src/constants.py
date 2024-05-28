from enum import STRICT, Enum, Flag, IntFlag, auto

U16 = 0xFFFF
U8 = 0xFF
KB = 1024

MEMORY_SIZE = 0xFFFF
PROGRAM_ROM_START = 0x8000
PROGRAM_ROM_END = 0xFFFF
CHARACTER_ROM_START = 0x0000
CHARACTER_ROM_END = 0x1FFF


class Flags(IntFlag, boundary=STRICT):
    """
    7  bit  0
    ---- ----
    NV1B DIZC
    |||| ||||
    |||| |||+- Carry
    |||| ||+-- Zero
    |||| |+--- Interrupt Disable
    |||| +---- Decimal
    |||+------ (No CPU effect; see: the B flag)
    ||+------- (No CPU effect; always pushed as 1)
    |+-------- Overflow
    +--------- Negative
    """

    CARRY = auto()
    ZERO = auto()
    INTERRUPT_DISABLE = auto()
    DECIMAL = auto()
    BREAK = auto()
    UNUSED = auto()
    OVERFLOW = auto()
    NEGATIVE = auto()


class AddressingMode(Enum):
    IMMEDIATE = "IMMEDIATE"
    ZERO_PAGE = "ZERO_PAGE"
    X_INDEXED_ZERO_PAGE = "X_INDEXED_ZERO_PAGE"
    Y_INDEXED_ZERO_PAGE = "Y_INDEXED_ZERO_PAGE"
    ABSOLUTE = "ABSOLUTE"
    X_INDEXED_ABSOLUTE = "X_INDEXED_ABSOLUTE"
    Y_INDEXED_ABSOLUTE = "Y_INDEXED_ABSOLUTE"
    X_INDEXED_ZERO_PAGE_INDIRECT = "X_INDEXED_ZERO_PAGE_INDIRECT"
    ZERO_PAGE_INDIRECT_Y_INDEXED = "ZERO_PAGE_INDIRECT_Y_INDEXED"
    RELATIVE = "RELATIVE"
    ACCUMULATOR = "ACCUMULATOR"
    IMPLIED = "IMPLIED"
    ABSOLUTE_INDIRECT = "ABSOLUTE_INDIRECT"


class CartridgeFormat(str, Enum):
    ines = "iNES1.0"
    nes20 = "NES2.0"
    ines07 = "iNES0.7"
    archaicines = "ArchaiciNES"


class HeaderFlags6(Flag):
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


class HeaderFlags7(Flag):
    """Flags 7

    76543210
    ||||||||
    |||||||+- VS Unisystem
    ||||||+-- PlayChoice-10 (8KB of Hint Screen data stored after CHR data)
    ||||++--- If equal to 2, flags 8-15 are in NES 2.0 format
    ++++----- Upper nybble of mapper number

    https://www.nesdev.org/wiki/INES
    """


class HeaderFlags9iNES(Flag):
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
