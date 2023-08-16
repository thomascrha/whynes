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
    "opcodes, addressing_modes, instruction_sequence_steps, initial_state, exit_state",
    [
        (
            # program shape
            # JSR $1000 ;jump to subroutine at $1000              0x0FFF
            # push next instruction to stack i.e. 0x1002
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
                "MEMORY": get_memory_map({0x01FE: 0x02, 0x01FF: 0x10}),
            },
        ),
        (
            # program shape
            # JSR $1004 ;jump to subroutine at $1004                           0x0FFF
            # LDA #$01 ;<- PROGRAM COUNTER LOCATION AT END                     0x1002
            # ...more code...
            # some_routine:
            #     LDA #$01 ;load accumulator with 1 (immediate addressing)     0x1004
            #     RTS ;return from subroutine                                  0x1006
            # ...more code...
            # """
            (Opcodes.JSR, Opcodes.LDA, Opcodes.RTS),
            (AddressingModes.ABSOLUTE, AddressingModes.IMMEDIATE, AddressingModes.IMPLIED),
            ([0x20, 0x04, 0x10, 0xA9, 0x02, 0xA9, 0x01, 0x60], 3),
            DEFAULT_STATE,
            {
                "A": 1,
                "PC": 0x1002,
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG,
                "SP": 255,
                "MEMORY": get_memory_map({0x01FE: 0x02, 0x01FF: 0x10}),
            },
        ),
        (
            # program shape
            # start the snake in a horizontal position in the middle of the game field
            # having a total length of one head and 4 bytes for the segments, meaning a
            # total length of 3: the head and two segments.
            # The head is looking right, and the snaking moving to the right.
            #
            # initial snake direction (2 => right)
            #   LDA #2   ;start direction, put the dec number 2 in register A                                    0x0FFF
            #   STA $02  ;store value of register A at address $02                                               0x1001
            #
            # initial snake length of 4
            #   LDA #4   ;start length, put the dec number 4 (the snake is 4 bytes long) in register A           0x1003
            #   STA $03  ;store value of register A at address $03                                               0x1005
            #
            # Initial snake head's location's least significant byte to determine
            # where in a 8x32 strip the head will start. hex $11 is just right
            # of the center of the first row of a strip
            #   LDA #$11 ;put the hex number $11 (dec 17) in register A                                          0x1007
            #   STA $10  ;store value of register A at address hex 10                                            0x1009
            #
            # Initial snake body, two least significant bytes set to hex $10
            # and hex $0f, one and two places left of the head respectively
            #   LDA #$10 ;put the hex number $10 (dec 16) in register A                                          0x100b
            #   STA $12  ;store value of register A at address hex $12                                           0x100d
            #   LDA #$0f ;put the hex number $0f (dec 15) in register A                                          0x100f
            #   STA $14  ;store value of register A at address hex $14                                           0x1011
            #
            # the most significant bytes of the head and body of the snake
            # are all set to hex $04, which is the third 8x32 strip.
            #   LDA #$04 ;put the hex number $04 in register A                                                   0x1013
            #   STA $11  ;store value of register A at address hex 11                                            0x1015
            #   STA $13  ;store value of register A at address hex 13                                            0x1017
            #   STA $15  ;store value of register A at address hex 15                                            0x1019
            (
                Opcodes.LDA,
                Opcodes.STA,
                Opcodes.LDA,
                Opcodes.STA,
                Opcodes.LDA,
                Opcodes.STA,
                Opcodes.LDA,
                Opcodes.STA,
                Opcodes.LDA,
                Opcodes.STA,
                Opcodes.LDA,
                Opcodes.STA,
                Opcodes.STA,
                Opcodes.STA,
            ),
            (
                AddressingModes.IMMEDIATE,
                AddressingModes.ZERO_PAGE,
                AddressingModes.IMMEDIATE,
                AddressingModes.ZERO_PAGE,
                AddressingModes.IMMEDIATE,
                AddressingModes.ZERO_PAGE,
                AddressingModes.IMMEDIATE,
                AddressingModes.ZERO_PAGE,
                AddressingModes.IMMEDIATE,
                AddressingModes.ZERO_PAGE,
                AddressingModes.IMMEDIATE,
                AddressingModes.ZERO_PAGE,
                AddressingModes.ZERO_PAGE,
                AddressingModes.ZERO_PAGE,
            ),
            (
                # fmt: off
                [
                    0xa9, 0x02,
                    0x85, 0x02,
                    0xa9, 0x04,
                    0x85, 0x03,
                    0xa9, 0x11,
                    0x85, 0x10,
                    0xa9, 0x10,
                    0x85, 0x12,
                    0xa9, 0x0f,
                    0x85, 0x14,
                    0xa9, 0x04,
                    0x85, 0x11,
                    0x85, 0x13,
                    0x85, 0x15,
                ],
                # fmt: on
                14
            ),
            DEFAULT_STATE,
            {
                "A": 4,
                "PC": 0x101B,  # 0x1019 + 2
                "X": 0,
                "Y": 0,
                "S": DEFAULT_FLAG,
                "SP": 255,
                "MEMORY": get_memory_map(
                    {
                        0x0002: 0x02,  # initial snake direction (2 => right)
                        0x0003: 0x04,  # initial snake length of 4
                        0x0010: 0x11,  # Initial snake head's location's least significant bytes
                        0x0011: 0x04,  # the most significant bytes of the head and body of the snake
                        0x0012: 0x10,  # Initial snake body, two least significant bytes set to hex $10
                        0x0013: 0x04,  # the most significant bytes of the head and body of the snake
                        0x0014: 0x0F,  # Initial snake body, two least significant bytes set to hex $0f
                        0x0015: 0x04,  # the most significant bytes of the head and body of the snake
                    }
                ),
            },
        ),
    ],
)
def test_assembly_cpu(
    opcodes: Opcodes,
    addressing_modes: AddressingModes,
    instruction_sequence_steps: Tuple[List[int], int],
    initial_state: dict,
    exit_state: dict,
):
    intstruction_sequence, steps = instruction_sequence_steps
    assert len(opcodes) == len(addressing_modes) == steps

    memory = Memory(program_rom_offset=0x0FFF)
    memory.load_program_rom(program_rom=intstruction_sequence)

    cpu = CPU(memory=memory)
    cpu.set_state(initial_state)

    _steps = 0
    while _steps < steps:
        cpu.step()

        assert cpu.instruction.opcode == opcodes[_steps]
        assert cpu.instruction.addressing_mode == addressing_modes[_steps]

        _steps += 1

    assert cpu.state == exit_state
