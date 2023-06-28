import pytest
from cpu import CPU
from instructions import Opcodes
from memory import Memory


@pytest.mark.parametrize(
    "opcode, instruction, machine_state",
    [
        (Opcodes.ADC, bytearray.fromhex("00")),
    ],
)
def test_assembly_cpu(opcode: Opcodes, instruction: bytearray):
    program_rom = bytearray.fromhex(input)
    memory = Memory()
    memory.load_bytes(program_rom=program_rom)
    cpu = CPU(memory=memory)
