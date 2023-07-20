"""
Some integration tests testing the state of the cpu and memory given a set of instructions
Used [Easy 6502](https://skilldrick.github.io/easy6502/) to get the step by step dissassembly
and state of the machine - this is the source of truth for the tests.
"""
from typing import List, Optional, Tuple
import pytest
from cpu import CPU, Flag
from instructions import AddressingModes, Opcodes
from memory import Memory
from tests.utils import DEFAULT_FLAG, get_memory_map


def get_state_from_cycle_state(cycle_state: tuple):
    cpu_state = cycle_state[0]
    _memory_state = cycle_state[1]
    status = cycle_state[2]
    a, x, y, sp, pc = [int(v.split("=")[1].replace("$", "0x"), 16) for v in cpu_state.split(" ")]

    if _memory_state:
        memory_state = {}
        for v in _memory_state.split(" "):
            address, value = v.split("=")
            memory_state[address] = int(value.replace("$", "0x"), 16)
    else:
        memory_state = _memory_state

    return a, x, y, sp, pc, memory_state, status


def get_memory_state(memory_state: Optional[dict] = None):
    memory = [0] * 0xFFFF
    if memory_state is None:
        return memory

    for address, value in memory_state.items():
        memory[int(address.replace("$", "0x"), 16)] = value

    return memory


class Test1:
    program_rom: bytearray = bytearray([0xA9, 0xC0, 0xAA, 0xE8, 0x69, 0xC4, 0x00])
    cycle_states: List[dict] = [
        {
            "A": 0xC0,
            "X": 0x0,
            "Y": 0x00,
            "SP": 0xFF,
            "PC": 0x0002,
            "S": DEFAULT_FLAG | Flag.NEGATIVE,
            "memory": get_memory_map({}),
        },
        {
            "A": 0xC0,
            "X": 0xC0,
            "Y": 0x00,
            "SP": 0xFF,
            "PC": 0x0003,
            "S": DEFAULT_FLAG | Flag.NEGATIVE,
            "memory": get_memory_map({}),
        },
        {
            "A": 0xC0,
            "X": 0xC1,
            "Y": 0x00,
            "SP": 0xFF,
            "PC": 0x0004,
            "S": DEFAULT_FLAG | Flag.NEGATIVE,
            "memory": get_memory_map({}),
        },
        {
            "A": 0x84,
            "X": 0xC1,
            "Y": 0x00,
            "SP": 0xFF,
            "PC": 0x0006,
            "S": DEFAULT_FLAG | Flag.NEGATIVE | Flag.CARRY,
            "memory": get_memory_map({}),
        },
        {
            "A": 0x84,
            "X": 0xC1,
            "Y": 0x00,
            "SP": 0xFC,
            "PC": 0x0000,
            "S": DEFAULT_FLAG | Flag.NEGATIVE | Flag.CARRY,
            "memory": get_memory_map({0x1FD: 0xA5, 0x1FE: 0x7}),
        },
    ]
    dissassembly_command_order: List[Tuple[Opcodes, AddressingModes]] = [
        (Opcodes.LDA, AddressingModes.IMMEDIATE),
        (Opcodes.TAX, AddressingModes.IMPLIED),
        (Opcodes.INX, AddressingModes.IMPLIED),
        (Opcodes.ADC, AddressingModes.IMMEDIATE),
        (Opcodes.BRK, AddressingModes.IMPLIED),
    ]


# class Test2:
#
#     # program_rom_2 = "a2 08 ca 8e 00 02 e0 03 d0 02 8e 01 02 00"
#     program_rom: bytearray = bytearray([0xA2, 0x08, 0xCA, 0x8E, 0x00, 0x02, 0xE0, 0x03, 0xD0, 0x8E, 0x01, 0x02, 0x00])
#     cycle_states: List[dict] =
#     dissassembly_command_order: List[Tuple[Opcodes, AddressingModes]] =  [
#     (Opcodes.LDX, AddressingModes.IMMEDIATE),
#     (Opcodes.DEX, AddressingModes.IMPLIED),
#     (Opcodes.STX, AddressingModes.ABSOLUTE),
#     (Opcodes.CPX, AddressingModes.IMMEDIATE),
#     (Opcodes.BNE, AddressingModes.RELATIVE),
#     (Opcodes.DEX, AddressingModes.IMPLIED),
#     (Opcodes.STX, AddressingModes.ABSOLUTE),
#     (Opcodes.CPX, AddressingModes.IMMEDIATE),
#     (Opcodes.BNE, AddressingModes.RELATIVE),
#     (Opcodes.DEX, AddressingModes.IMPLIED),
#     (Opcodes.STX, AddressingModes.ABSOLUTE),
#     (Opcodes.CPX, AddressingModes.IMMEDIATE),
#     (Opcodes.BNE, AddressingModes.RELATIVE),
#     (Opcodes.DEX, AddressingModes.IMPLIED),
#     (Opcodes.STX, AddressingModes.ABSOLUTE),
#     (Opcodes.CPX, AddressingModes.IMMEDIATE),
#     (Opcodes.BNE, AddressingModes.RELATIVE),
#     (Opcodes.DEX, AddressingModes.IMPLIED),
#     (Opcodes.STX, AddressingModes.ABSOLUTE),
#     (Opcodes.CPX, AddressingModes.IMMEDIATE),
#     (Opcodes.BNE, AddressingModes.RELATIVE),
#     (Opcodes.STX, AddressingModes.ABSOLUTE),
#     (Opcodes.BRK, AddressingModes.IMPLIED),
# ]
# cycle_states_2 = [
#     ("A=$00 X=$08 Y=$00 SP=$ff PC=$0002", "$0200=$00 $0201=$00", 0b00100100),
#     ("A=$00 X=$07 Y=$00 SP=$ff PC=$0003", "$0200=$00 $0201=$00", 0b00100100),
#     ("A=$00 X=$07 Y=$00 SP=$ff PC=$0006", "$0200=$07 $0201=$00", 0b00100100),
#     ("A=$00 X=$07 Y=$00 SP=$ff PC=$0008", "$0200=$07 $0201=$00", 0b00100101),
#     ("A=$00 X=$07 Y=$00 SP=$ff PC=$0002", "$0200=$07 $0201=$00", 0b00100101),
#     ("A=$00 X=$06 Y=$00 SP=$ff PC=$0003", "$0200=$07 $0201=$00", 0b00100101),
#     ("A=$00 X=$06 Y=$00 SP=$ff PC=$0006", "$0200=$06 $0201=$00", 0b00100101),
#     ("A=$00 X=$06 Y=$00 SP=$ff PC=$0008", "$0200=$06 $0201=$00", 0b00100101),
#     ("A=$00 X=$06 Y=$00 SP=$ff PC=$0002", "$0200=$06 $0201=$00", 0b00100101),
#     ("A=$00 X=$05 Y=$00 SP=$ff PC=$0003", "$0200=$06 $0201=$00", 0b00100101),
#     ("A=$00 X=$05 Y=$00 SP=$ff PC=$0006", "$0200=$05 $0201=$00", 0b00100101),
#     ("A=$00 X=$05 Y=$00 SP=$ff PC=$0008", "$0200=$05 $0201=$00", 0b00100101),
#     ("A=$00 X=$05 Y=$00 SP=$ff PC=$0002", "$0200=$05 $0201=$00", 0b00100101),
#     ("A=$00 X=$04 Y=$00 SP=$ff PC=$0003", "$0200=$05 $0201=$00", 0b00100101),
#     ("A=$00 X=$04 Y=$00 SP=$ff PC=$0006", "$0200=$04 $0201=$00", 0b00100101),
#     ("A=$00 X=$04 Y=$00 SP=$ff PC=$0008", "$0200=$04 $0201=$00", 0b00100101),
#     ("A=$00 X=$04 Y=$00 SP=$ff PC=$0002", "$0200=$04 $0201=$00", 0b00100101),
#     ("A=$00 X=$03 Y=$00 SP=$ff PC=$0003", "$0200=$04 $0201=$00", 0b00100101),
#     ("A=$00 X=$03 Y=$00 SP=$ff PC=$0006", "$0200=$03 $0201=$00", 0b00100101),
#     ("A=$00 X=$03 Y=$00 SP=$ff PC=$0008", "$0200=$03 $0201=$00", 0b00100111),
#     ("A=$00 X=$03 Y=$00 SP=$ff PC=$000a", "$0200=$03 $0201=$00", 0b00100111),
#     ("A=$00 X=$03 Y=$00 SP=$ff PC=$000d", "$0200=$03 $0201=$03", 0b00100111),
#     ("A=$00 X=$03 Y=$00 SP=$fc PC=$0000", "$0200=$03 $0201=$03 $01fd=$27 $01fe=$0e", 0b00100111),
# ]


@pytest.mark.parametrize(
    "program_rom,cycle_states,dissassembly_command_order",
    [
        (Test1.program_rom, Test1.cycle_states, Test1.dissassembly_command_order),
    ],
)
def test_assembly_cpu(program_rom: bytearray, cycle_states: list, dissassembly_command_order: list):
    memory = Memory()
    memory.load_bytes(program_rom=program_rom)
    cpu = CPU(memory=memory)

    for i, cycle_state in enumerate(cycle_states):
        cpu.step()

        assert cpu.state["A"] == cycle_state["A"]
        assert cpu.state["X"] == cycle_state["X"]
        assert cpu.state["Y"] == cycle_state["Y"]
        assert cpu.state["SP"] == cycle_state["SP"]
        assert cpu.state["PC"] == cycle_state["PC"]
        assert cpu.state["S"] == cycle_state["S"]
        # assert cpu.state["memory"] == cycle_state["memory"]

        assert cpu.instruction.opcode == dissassembly_command_order[i][0]
        assert cpu.instruction.addressing_mode == dissassembly_command_order[i][1]
