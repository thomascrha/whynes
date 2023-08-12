"""
These test assume that the first 0x0FFF of memory are RAM whist the rest is ROM.
"""

from typing import List, Tuple
import pytest
from cpu import CPU
from instructions import AddressingModes, Opcodes
from memory import Memory
from tests.utils import DEFAULT_FLAG, DEFAULT_STATE, get_memory_map


def compare_lists(list1, list2):
    return {i: (list1[i], list2[i]) for i in range(len(list1)) if list1[i] != list2[i]}


@pytest.mark.parametrize(
    "opcode, addressing_mode, instruction_sequence_steps, initial_state, exit_state",
    [
        (
            # program shape
            # JSR $1000 ;jump to subroutine at $1000              0x0FFF
            # push next instruction to stack i.e. 0x1000
            (Opcodes.JSR,),
            (AddressingModes.ABSOLUTE,),
            ([0x20, 0x00, 0x10], 1),
            DEFAULT_STATE,  # lo -> 254(sp)  hi -> 255(sp)
            {
                "A": 0,
                "PC": 0x1000,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG,
                "SP": 253,
                "MEMORY": get_memory_map({0x01FE: 0x00, 0x01FF: 0x10}),
            },
        ),
        # (
        #     # program shape
        #     # JSR $1000 ;jump to subroutine at $1000                           0x0FFF
        #     # LDA #$01 ;<- PROGRAM COUNTER LOCATION AT END                     0x1000
        #     # ...more code...
        #     # some_routine:
        #     #     LDA #$01 ;load accumulator with 1 (immediate addressing)     0x1001
        #     #     RTS ;return from subroutine                                  0x1002
        #     # ...more code...
        #     # """
        #     (Opcodes.JSR, Opcodes.LDA, Opcodes.RTS),
        #     (AddressingModes.ABSOLUTE, AddressingModes.IMMEDIATE, AddressingModes.IMPLIED),
        #     ([0x20, 0x02, 0x10, 0xA9, 0x01, 0x60], 3),
        #     DEFAULT_STATE,
        #     {"A": 1, "PC": 0x1000, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "MEMORY": get_memory_map()}
        # ),
    ],
)
def test_assembly_cpu(
    opcode: Opcodes,
    addressing_mode: AddressingModes,
    instruction_sequence_steps: Tuple[List[int], int],
    initial_state: dict,
    exit_state: dict,
):
    intstruction_sequence, steps = instruction_sequence_steps
    memory = Memory()
    memory.load_program_rom(program_rom=intstruction_sequence, program_rom_offset=0x0FFF)

    cpu = CPU(memory=memory)
    cpu.set_state(initial_state)

    _steps = 0
    while _steps < steps:
        cpu.step()

        assert cpu.instruction.opcode == opcode[_steps]
        assert cpu.instruction.addressing_mode == addressing_mode[_steps]

        _steps += 1

    print(compare_lists(cpu.state["MEMORY"], exit_state["MEMORY"]))
    assert cpu.state == exit_state


# find the largest number divisible
