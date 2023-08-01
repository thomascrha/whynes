from typing import List
import pytest
from cpu import CPU, Flag
from instructions import AddressingModes, Opcodes
from memory import Memory
from tests.utils import DEFAULT_FLAG, DEFAULT_STATE


@pytest.mark.parametrize(
    "opcode, addressing_mode, instruction, initial_state, exit_state",
    [
        (
            Opcodes.ADC,
            AddressingModes.IMMEDIATE,
            [0x69, 0x01],
            DEFAULT_STATE,
            {"A": 0x01, "PC": 2, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255},
        ),
        (
            Opcodes.AND,
            AddressingModes.ZERO_PAGE,
            [0x25, 0x01],
            DEFAULT_STATE,
            {"A": 0, "PC": 2, "X": 0, "Y": 0, "S": DEFAULT_FLAG | Flag.ZERO, "SP": 255},
        ),
        (
            Opcodes.AND,
            AddressingModes.IMMEDIATE,
            [0x29, 0x01],
            {"A": 1, "PC": 0, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255},
            {"A": 1, "PC": 2, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255},
        ),
        (
            Opcodes.ASL,
            AddressingModes.ACCUMULATOR,
            [0x0A],
            DEFAULT_STATE,
            {"A": 0, "PC": 1, "X": 0, "Y": 0, "S": DEFAULT_FLAG | Flag.ZERO, "SP": 255},
        ),
        (
            Opcodes.BCC,
            AddressingModes.RELATIVE,
            [0x90, 0x29],
            DEFAULT_STATE,
            {"A": 0, "PC": 0x29, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255},
        ),
        (
            Opcodes.BCC,
            AddressingModes.RELATIVE,
            [0x90, 0x01],
            {
                "A": 0,
                "PC": 0x0,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.CARRY,
                "SP": 255,
            },
            {
                "A": 0,
                "PC": 0x02,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.CARRY,
                "SP": 255,
            },
        ),
        (
            Opcodes.BCS,
            AddressingModes.RELATIVE,
            [0xB0, 0x2C],
            DEFAULT_STATE,
            {"A": 0, "PC": 0x02, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255},
        ),
        (
            Opcodes.BCS,
            AddressingModes.RELATIVE,
            [0xB0, 0x2C],
            {
                "A": 0,
                "PC": 0x00,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.CARRY,
                "SP": 255,
            },
            {
                "A": 0,
                "PC": 0x2C,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.CARRY,
                "SP": 255,
            },
        ),
        (
            Opcodes.BEQ,
            AddressingModes.RELATIVE,
            [0xF0, 0x01],
            DEFAULT_STATE,
            {"A": 0, "PC": 2, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255},
        ),
        (
            Opcodes.BEQ,
            AddressingModes.RELATIVE,
            [0xF0, 0x2C],
            {"A": 0, "PC": 0x0, "X": 0, "Y": 0, "S": DEFAULT_FLAG | Flag.ZERO, "SP": 255},
            {
                "A": 0,
                "PC": 0x2C,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.ZERO,
                "SP": 255,
            },
        ),
        (
            Opcodes.BIT,
            AddressingModes.ABSOLUTE,
            [0x2C, 0x01, 0x00],
            DEFAULT_STATE,
            {"A": 0, "PC": 3, "X": 0, "Y": 0, "S": DEFAULT_FLAG | Flag.ZERO, "SP": 255},
        ),
        (
            Opcodes.BIT,
            AddressingModes.ZERO_PAGE,
            [0x24, 0x01],
            DEFAULT_STATE,
            {"A": 0, "PC": 2, "X": 0, "Y": 0, "S": DEFAULT_FLAG | Flag.ZERO, "SP": 255},
        ),
        (
            Opcodes.BMI,
            AddressingModes.RELATIVE,
            [0x30, 0x01],
            DEFAULT_STATE,
            {"A": 0, "PC": 2, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255},
        ),
        (
            Opcodes.BNE,
            AddressingModes.RELATIVE,
            [0xD0, 0x30],
            DEFAULT_STATE,
            {"A": 0, "PC": 0x30, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255},
        ),
        (
            Opcodes.BNE,
            AddressingModes.RELATIVE,
            [0xD0, 0x01],
            DEFAULT_STATE,
            {"A": 0, "PC": 1, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255},
        ),
        (
            Opcodes.BPL,
            AddressingModes.RELATIVE,
            [0x10, 0x29],
            DEFAULT_STATE,
            {"A": 0, "PC": 0x29, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255},
        ),
        (
            Opcodes.BRK,
            AddressingModes.IMPLIED,
            [0x00],
            DEFAULT_STATE,
            {"A": 0, "PC": 0x0, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 252},
        ),
        (
            Opcodes.BVC,
            AddressingModes.RELATIVE,
            [0x50, 0x01],
            DEFAULT_STATE,
            {"A": 0, "PC": 1, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255},
        ),
        (
            Opcodes.BVC,
            AddressingModes.RELATIVE,
            [0x50, 0x01],
            {
                "A": 0,
                "PC": 0,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.OVERFLOW,
                "SP": 255,
            },
            {
                "A": 0,
                "PC": 2,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.OVERFLOW,
                "SP": 255,
            },
        ),
        (
            Opcodes.BVS,
            AddressingModes.RELATIVE,
            [0x70, 0x01],
            DEFAULT_STATE,
            {
                "A": 0,
                "PC": 2,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG,
                "SP": 255,
            },
        ),
        (
            Opcodes.BVS,
            AddressingModes.RELATIVE,
            [0x70, 0x01],
            {
                "A": 0,
                "PC": 0,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.OVERFLOW,
                "SP": 255,
            },
            {
                "A": 0,
                "PC": 1,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.OVERFLOW,
                "SP": 255,
            },
        ),
        (
            Opcodes.CLC,
            AddressingModes.IMPLIED,
            [0x18],
            {
                "A": 0,
                "PC": 0,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.CARRY,
                "SP": 255,
            },
            {
                "A": 0,
                "PC": 1,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG,
                "SP": 255,
            },
        ),
        (
            Opcodes.CLD,
            AddressingModes.IMPLIED,
            [0xD8],
            {
                "A": 0,
                "PC": 0,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.DECIMAL,
                "SP": 255,
            },
            {"A": 0, "PC": 1, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255},
        ),
        (
            Opcodes.CLV,
            AddressingModes.IMPLIED,
            [0xB8],
            {
                "A": 0,
                "PC": 0,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.OVERFLOW,
                "SP": 255,
            },
            {"A": 0, "PC": 1, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255},
        ),
        (
            Opcodes.CMP,
            AddressingModes.IMMEDIATE,
            [0xC9, 0x01],
            {"A": 0x01, "PC": 0, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255},
            {
                "A": 0x01,
                "PC": 2,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG | Flag.CARRY,
                "SP": 255,
            },
        ),
        (
            Opcodes.CMP,
            AddressingModes.ABSOLUTE,
            [0xCD, 0x00, 0x00],
            {"A": 0x01, "PC": 0, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255},
            {
                "A": 0x01,
                "PC": 3,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG,
                "SP": 255,
            },
        ),
    ],
)
def test_assembly_cpu(
    opcode: Opcodes, addressing_mode: AddressingModes, instruction: List[int], initial_state: dict, exit_state: dict
):
    memory = Memory()
    memory.load_program_rom(program_rom=instruction, program_rom_offset=0x0000)

    cpu = CPU(memory=memory, program_rom_offset=0x0000)
    cpu.set_state(initial_state)

    cpu.step()

    assert cpu.instruction.opcode == opcode
    assert cpu.instruction.addressing_mode == addressing_mode

    assert cpu.state == exit_state
