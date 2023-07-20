import pytest
from cpu import CPU, Flag
from instructions import AddressingModes, Opcodes
from memory import Memory
from tests.utils import DEFAULT_FLAG, DEFAULT_STATE, get_memory_map


@pytest.mark.parametrize(
    "opcode, addressing_mode, instruction, initial_state, exit_state",
    [
        (
            Opcodes.ADC,
            AddressingModes.IMMEDIATE,
            bytearray([0x69, 0x01]),
            DEFAULT_STATE,
            {"A": 0x01, "PC": 2, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({})},
        ),
        (
            Opcodes.AND,
            AddressingModes.ZERO_PAGE,
            bytearray([0x25, 0x01]),
            DEFAULT_STATE,
            {"A": 0, "PC": 2, "X": 0, "Y": 0, "S": DEFAULT_FLAG | Flag.ZERO, "SP": 255, "memory": get_memory_map({})},
        ),
        (
            Opcodes.AND,
            AddressingModes.IMMEDIATE,
            bytearray([0x29, 0x01]),
            {"A": 1, "PC": 0, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({})},
            {"A": 1, "PC": 2, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({})},
        ),
        (
            Opcodes.ASL,
            AddressingModes.ACCUMULATOR,
            bytearray([0x0A]),
            DEFAULT_STATE,
            {"A": 0, "PC": 1, "X": 0, "Y": 0, "S": DEFAULT_FLAG | Flag.ZERO, "SP": 255, "memory": get_memory_map({})},
        ),
        (
            Opcodes.BCC,
            AddressingModes.RELATIVE,
            bytearray([0x90, 0x29]),
            DEFAULT_STATE,
            {"A": 0, "PC": 0x29, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({})},
        ),
        (
            Opcodes.BCC,
            AddressingModes.RELATIVE,
            bytearray([0x90, 0x01]),
            {
                "A": 0,
                "PC": 0x0,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.CARRY,
                "SP": 255,
                "memory": get_memory_map({}),
            },
            {
                "A": 0,
                "PC": 0x02,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.CARRY,
                "SP": 255,
                "memory": get_memory_map({}),
            },
        ),
        (
            Opcodes.BCS,
            AddressingModes.RELATIVE,
            bytearray([0xB0, 0x2C]),
            DEFAULT_STATE,
            {"A": 0, "PC": 0x02, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({})},
        ),
        (
            Opcodes.BCS,
            AddressingModes.RELATIVE,
            bytearray([0xB0, 0x2C]),
            {
                "A": 0,
                "PC": 0x00,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.CARRY,
                "SP": 255,
                "memory": get_memory_map({}),
            },
            {
                "A": 0,
                "PC": 0x2C,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.CARRY,
                "SP": 255,
                "memory": get_memory_map({}),
            },
        ),
        (
            Opcodes.BEQ,
            AddressingModes.RELATIVE,
            bytearray([0xF0, 0x01]),
            DEFAULT_STATE,
            {"A": 0, "PC": 2, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({})},
        ),
        (
            Opcodes.BEQ,
            AddressingModes.RELATIVE,
            bytearray([0xF0, 0x2C]),
            {"A": 0, "PC": 0x0, "X": 0, "Y": 0, "S": DEFAULT_FLAG | Flag.ZERO, "SP": 255, "memory": get_memory_map({})},
            {
                "A": 0,
                "PC": 0x2C,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.ZERO,
                "SP": 255,
                "memory": get_memory_map({}),
            },
        ),
        (
            Opcodes.BIT,
            AddressingModes.ABSOLUTE,
            bytearray([0x2C, 0x01, 0x00]),
            DEFAULT_STATE,
            {"A": 0, "PC": 3, "X": 0, "Y": 0, "S": DEFAULT_FLAG | Flag.ZERO, "SP": 255, "memory": get_memory_map({})},
        ),
        (
            Opcodes.BIT,
            AddressingModes.ZERO_PAGE,
            bytearray([0x24, 0x01]),
            DEFAULT_STATE,
            {"A": 0, "PC": 2, "X": 0, "Y": 0, "S": DEFAULT_FLAG | Flag.ZERO, "SP": 255, "memory": get_memory_map({})},
        ),
        (
            Opcodes.BMI,
            AddressingModes.RELATIVE,
            bytearray([0x30, 0x01]),
            DEFAULT_STATE,
            {"A": 0, "PC": 2, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({})},
        ),
        # what ?!
        (
            Opcodes.BNE,
            AddressingModes.RELATIVE,
            bytearray([0xD0, 0x30]),
            DEFAULT_STATE,
            {"A": 0, "PC": 0x30, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({})},
        ),
        (
            Opcodes.BNE,
            AddressingModes.RELATIVE,
            bytearray([0xD0, 0x01]),
            DEFAULT_STATE,
            {"A": 0, "PC": 1, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({})},
        ),
        (
            Opcodes.BPL,
            AddressingModes.RELATIVE,
            bytearray([0x10, 0x29]),
            DEFAULT_STATE,
            {"A": 0, "PC": 0x29, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({})},
        ),
        # (
        #     Opcodes.BRK,
        #     AddressingModes.IMPLIED,
        #     bytearray([0x00]),
        #     DEFAULT_STATE,
        #     {"A": 0, "PC": 0x0, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 252, "memory": get_memory_map({})}
        # ),
        (
            Opcodes.BVC,
            AddressingModes.RELATIVE,
            bytearray([0x50, 0x01]),
            DEFAULT_STATE,
            {"A": 0, "PC": 1, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({})},
        ),
        (
            Opcodes.BVC,
            AddressingModes.RELATIVE,
            bytearray([0x50, 0x01]),
            {
                "A": 0,
                "PC": 0,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.OVERFLOW,
                "SP": 255,
                "memory": get_memory_map({}),
            },
            {
                "A": 0,
                "PC": 2,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.OVERFLOW,
                "SP": 255,
                "memory": get_memory_map({}),
            },
        ),
        (
            Opcodes.BVS,
            AddressingModes.RELATIVE,
            bytearray([0x70, 0x01]),
            DEFAULT_STATE,
            {"A": 0, "PC": 2, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({})},
        ),
        (
            Opcodes.BVS,
            AddressingModes.RELATIVE,
            bytearray([0x70, 0x01]),
            {
                "A": 0,
                "PC": 0,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.OVERFLOW,
                "SP": 255,
                "memory": get_memory_map({}),
            },
            {
                "A": 0,
                "PC": 1,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.OVERFLOW,
                "SP": 255,
                "memory": get_memory_map({}),
            },
        ),
        (
            Opcodes.CLC,
            AddressingModes.IMPLIED,
            bytearray([0x18]),
            {"A": 0, "PC": 0, "X": 0, "Y": 0, "S": DEFAULT_FLAG | Flag.CARRY, "SP": 255, "memory": get_memory_map({})},
            {"A": 0, "PC": 1, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({})},
        ),
        (
            Opcodes.CLD,
            AddressingModes.IMPLIED,
            bytearray([0xD8]),
            {
                "A": 0,
                "PC": 0,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.DECIMAL,
                "SP": 255,
                "memory": get_memory_map({}),
            },
            {"A": 0, "PC": 1, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({})},
        ),
        (
            Opcodes.CLV,
            AddressingModes.IMPLIED,
            bytearray([0xB8]),
            {
                "A": 0,
                "PC": 0,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.OVERFLOW,
                "SP": 255,
                "memory": get_memory_map({}),
            },
            {"A": 0, "PC": 1, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({})},
        ),
        (
            Opcodes.CMP,
            AddressingModes.IMMEDIATE,
            bytearray([0xC9, 0x01]),
            DEFAULT_STATE,
            {
                "A": 0,
                "PC": 2,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.NEGATIVE,
                "SP": 255,
                "memory": get_memory_map({}),
            },
        ),
        (
            Opcodes.CMP,
            AddressingModes.ZERO_PAGE,
            bytearray([0xC5, 0x01]),
            DEFAULT_STATE,
            {
                "A": 0,
                "PC": 2,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.ZERO | Flag.CARRY,
                "SP": 255,
                "memory": get_memory_map({}),
            },
        ),
        (
            Opcodes.CMP,
            AddressingModes.X_INDEXED_ZERO_PAGE,
            bytearray([0xD5, 0x01]),
            {
                "A": 0,
                "PC": 0,
                "X": 1,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.ZERO | Flag.CARRY,
                "SP": 255,
                "memory": get_memory_map({}),
            },
            {
                "A": 0,
                "PC": 2,
                "X": 1,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.ZERO | Flag.CARRY,
                "SP": 255,
                "memory": get_memory_map({}),
            },
        ),
        (
            Opcodes.CMP,
            AddressingModes.ABSOLUTE,
            bytearray([0xCD, 0x00, 0x01]),
            DEFAULT_STATE,
            {
                "A": 0,
                "PC": 3,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.ZERO | Flag.CARRY,
                "SP": 255,
                "memory": get_memory_map({}),
            },
        ),
        (
            Opcodes.CPY,
            AddressingModes.IMMEDIATE,
            bytearray([0xC0, 0x01]),
            DEFAULT_STATE,
            {
                "A": 0,
                "PC": 2,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.NEGATIVE,
                "SP": 255,
                "memory": get_memory_map({}),
            },
        ),
        (
            Opcodes.CPY,
            AddressingModes.ZERO_PAGE,
            bytearray([0xC4, 0x01]),
            DEFAULT_STATE,
            {
                "A": 0,
                "PC": 2,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.ZERO | Flag.CARRY,
                "SP": 255,
                "memory": get_memory_map({}),
            },
        ),
        # (
        #     Opcodes.DEC,
        #     AddressingModes.ZERO_PAGE,
        #     bytearray([0xC6, 0x01]),
        #     DEFAULT_STATE,
        #     {"A": 0, "PC": 2, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({0x01: 0xFF})}
        # ),
        # (
        #     Opcodes.DEC,
        #     AddressingModes.X_INDEXED_ZERO_PAGE,
        #     bytearray([0xD6, 0x01]),
        #     {"A": 0, "PC": 0, "X": 1, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({0x02: 0xFF})},
        #     {"A": 0, "PC": 2, "X": 1, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({0x02: 0xFF})}
        # ),
        # (
        #     Opcodes.DEC,
        #     AddressingModes.ABSOLUTE,
        #     bytearray([0xCE, 0x00, 0x01]),
        #     DEFAULT_STATE,
        #     {"A": 0, "PC": 3, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "memory": get_memory_map({0x0100: 0xFF})}
        # ),
        # (
        #     Opcodes.DEX,
        #     AddressingModes.IMPLIED,
        #     bytearray([0xCA]),
        #     DEFAULT_STATE,
        #     {"A": 0, "PC": 1, "X": 0, "Y": 0, "S": DEFAULT_FLAG | Flag.ZERO, "SP": 255, "memory": get_memory_map({})},
        # )
    ],
)
def test_assembly_cpu(
    opcode: Opcodes, addressing_mode: AddressingModes, instruction: bytearray, initial_state: dict, exit_state: dict
):
    memory = Memory()
    memory.load_bytes(program_rom=instruction)
    cpu = CPU(memory=memory)

    cpu.set_state(initial_state)

    cpu.step()  # ADC #$01

    assert cpu.instruction.opcode == opcode
    assert cpu.instruction.addressing_mode == addressing_mode

    assert cpu.state == exit_state
