"""
Some integration tests testing the state of the cpu and memory given a set of instructions
Used [Easy 6502](https://skilldrick.github.io/easy6502/) to get the step by step dissassembly
and state of the machine - this is the source of truth for the tests.
"""
from typing import Optional
from cpu import CPU, Flags
from instructions import AddressingModes, Opcodes
from memory import Memory


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


def test_assembly_cpu(input: str, cycle_states: list, dissassembly_command_order: list):
    program_rom = bytearray.fromhex(input)
    memory = Memory()
    memory.load_bytes(program_rom=program_rom)
    cpu = CPU(memory=memory)

    # intial state
    a, x, y, sp, pc, memory_state, status = get_state_from_cycle_state(cycle_states[0])
    assert cpu.a == a
    assert cpu.x == x
    assert cpu.y == y
    assert cpu.stack_pointer == sp
    assert cpu.program_counter == pc
    assert cpu.status == Flags(status)

    for i, cycle_state in enumerate(cycle_states[1:]):
        if i == 0:
            cpu.step(first=True)
        else:
            cpu.step()
        a, x, y, sp, pc, memory_state, status = get_state_from_cycle_state(cycle_state)
        assert cpu.a == a
        assert cpu.x == x
        assert cpu.y == y
        assert cpu.stack_pointer == sp
        assert cpu.program_counter == pc
        assert cpu.status == Flags(status)

        assert get_memory_state(memory_state) == cpu.memory
        assert cpu.instruction.opcode == dissassembly_command_order[i][0]
        assert cpu.instruction.addressing_mode == dissassembly_command_order[i][1]

    print(cpu.instruction)
    print(cpu)


program_asl_1 = """
Address  Hexdump   Dissassembly
-------------------------------
$0000    a9 01     LDA #$01
$0002    8d 00 02  STA $0200
$0005    a9 05     LDA #$05
$0007    8d 01 02  STA $0201
$000a    a9 08     LDA #$08
$000c    8d 02 02  STA $0202
"""

program_rom_1 = "a9 01 8d 00 02 a9 05 8d 01 02 a9 08 8d 02 02"
dissassembly_command_order_1 = [
    (Opcodes.LDA, AddressingModes.IMMEDIATE),
    (Opcodes.STA, AddressingModes.ABSOLUTE),
    (Opcodes.LDA, AddressingModes.IMMEDIATE),
    (Opcodes.STA, AddressingModes.ABSOLUTE),
    (Opcodes.LDA, AddressingModes.IMMEDIATE),
    (Opcodes.STA, AddressingModes.ABSOLUTE),
]

cycle_states_1 = [
    ("A=$00 X=$00 Y=$00 SP=$ff PC=$0000", "$0200=$00 $0201=$00 $0202=$00", 0b00110000),
    ("A=$01 X=$00 Y=$00 SP=$ff PC=$0002", "$0200=$00 $0201=$00 $0202=$00", 0b00110000),
    ("A=$01 X=$00 Y=$00 SP=$ff PC=$0005", "$0200=$01 $0201=$00 $0202=$00", 0b00110000),
    ("A=$05 X=$00 Y=$00 SP=$ff PC=$0007", "$0200=$01 $0201=$00 $0202=$00", 0b00110000),
    ("A=$05 X=$00 Y=$00 SP=$ff PC=$000a", "$0200=$01 $0201=$05 $0202=$00", 0b00110000),
    ("A=$08 X=$00 Y=$00 SP=$ff PC=$000c", "$0200=$01 $0201=$05 $0202=$00", 0b00110000),
    ("A=$08 X=$00 Y=$00 SP=$ff PC=$000f", "$0200=$01 $0201=$05 $0202=$08", 0b00110000),
]

print(program_asl_1)
test_assembly_cpu(program_rom_1, cycle_states_1, dissassembly_command_order_1)

program_asl_2 = """
Address  Hexdump   Dissassembly
-------------------------------
$0000    a9 c0     LDA #$c0
$0002    aa        TAX
$0003    e8        INX
$0004    69 c4     ADC #$c4
$0006    00        BRK
"""

program_rom_2 = "a9 c0 aa e8 69 c4 00"
dissassembly_command_order_2 = [
    (Opcodes.LDA, AddressingModes.IMMEDIATE),
    (Opcodes.TAX, AddressingModes.IMPLIED),
    (Opcodes.INX, AddressingModes.IMPLIED),
    (Opcodes.ADC, AddressingModes.IMMEDIATE),
    (Opcodes.BRK, AddressingModes.IMPLIED),
]

cycle_states_2 = [
    ("A=$00 X=$00 Y=$00 SP=$ff PC=$0000", None, 0b00110000),
    ("A=$c0 X=$00 Y=$00 SP=$ff PC=$0002", None, 0b10110000),
    ("A=$c0 X=$c0 Y=$00 SP=$ff PC=$0003", None, 0b10110000),
    ("A=$c0 X=$c1 Y=$00 SP=$ff PC=$0004", None, 0b10110000),
    ("A=$84 X=$c1 Y=$00 SP=$ff PC=$0006", None, 0b10110001),
]

print(program_asl_2)
test_assembly_cpu(program_rom_2, cycle_states_2, dissassembly_command_order_2)

program_asl_3 = """
Address  Hexdump   Dissassembly
-------------------------------
$0000    a2 08     LDX #$08
$0002    ca        DEX
$0003    8e 00 02  STX $0200
$0006    e0 03     CPX #$03
$0008    d0 02     BNE $0002
$000a    8e 01 02  STX $0201
$000d    00        BRK
"""

program_rom_3 = "a2 08 ca 8e 00 02 e0 03 d0 02 8e 01 02 00"
dissassembly_command_order_3 = [
    (Opcodes.LDX, AddressingModes.IMMEDIATE),
    (Opcodes.DEX, AddressingModes.IMPLIED),
    (Opcodes.STX, AddressingModes.ABSOLUTE),
    (Opcodes.CPX, AddressingModes.IMMEDIATE),
    (Opcodes.BNE, AddressingModes.RELATIVE),
    (Opcodes.DEX, AddressingModes.IMPLIED),
    (Opcodes.STX, AddressingModes.ABSOLUTE),
    (Opcodes.CPX, AddressingModes.IMMEDIATE),
    (Opcodes.BNE, AddressingModes.RELATIVE),
    (Opcodes.DEX, AddressingModes.IMPLIED),
    (Opcodes.STX, AddressingModes.ABSOLUTE),
    (Opcodes.CPX, AddressingModes.IMMEDIATE),
    (Opcodes.BNE, AddressingModes.RELATIVE),
    (Opcodes.DEX, AddressingModes.IMPLIED),
    (Opcodes.STX, AddressingModes.ABSOLUTE),
    (Opcodes.CPX, AddressingModes.IMMEDIATE),
    (Opcodes.BNE, AddressingModes.RELATIVE),
    (Opcodes.DEX, AddressingModes.IMPLIED),
    (Opcodes.STX, AddressingModes.ABSOLUTE),
    (Opcodes.CPX, AddressingModes.IMMEDIATE),
    (Opcodes.BNE, AddressingModes.RELATIVE),
    (Opcodes.STX, AddressingModes.ABSOLUTE),
    (Opcodes.BRK, AddressingModes.IMPLIED),
]

cycle_states_3 = [
    ("A=$00 X=$00 Y=$00 SP=$ff PC=$0000", "$0200=$00 $0201=$00", 0b00110000),
    ("A=$00 X=$08 Y=$00 SP=$ff PC=$0002", "$0200=$00 $0201=$00", 0b00110000),
    ("A=$00 X=$07 Y=$00 SP=$ff PC=$0003", "$0200=$00 $0201=$00", 0b00110000),
    ("A=$00 X=$07 Y=$00 SP=$ff PC=$0006", "$0200=$07 $0201=$00", 0b00110000),
    ("A=$00 X=$07 Y=$00 SP=$ff PC=$0008", "$0200=$07 $0201=$00", 0b00110001),
    ("A=$00 X=$07 Y=$00 SP=$ff PC=$0002", "$0200=$07 $0201=$00", 0b00110001),
    ("A=$00 X=$06 Y=$00 SP=$ff PC=$0003", "$0200=$07 $0201=$00", 0b00110001),
    ("A=$00 X=$06 Y=$00 SP=$ff PC=$0006", "$0200=$06 $0201=$00", 0b00110001),
    ("A=$00 X=$06 Y=$00 SP=$ff PC=$0008", "$0200=$06 $0201=$00", 0b00110001),
    ("A=$00 X=$06 Y=$00 SP=$ff PC=$0002", "$0200=$06 $0201=$00", 0b00110001),
    ("A=$00 X=$05 Y=$00 SP=$ff PC=$0003", "$0200=$06 $0201=$00", 0b00110001),
    ("A=$00 X=$05 Y=$00 SP=$ff PC=$0006", "$0200=$05 $0201=$00", 0b00110001),
    ("A=$00 X=$05 Y=$00 SP=$ff PC=$0008", "$0200=$05 $0201=$00", 0b00110001),
    ("A=$00 X=$05 Y=$00 SP=$ff PC=$0002", "$0200=$05 $0201=$00", 0b00110001),
    ("A=$00 X=$04 Y=$00 SP=$ff PC=$0003", "$0200=$05 $0201=$00", 0b00110001),
    ("A=$00 X=$04 Y=$00 SP=$ff PC=$0006", "$0200=$04 $0201=$00", 0b00110001),
    ("A=$00 X=$04 Y=$00 SP=$ff PC=$0008", "$0200=$04 $0201=$00", 0b00110001),
    ("A=$00 X=$04 Y=$00 SP=$ff PC=$0002", "$0200=$04 $0201=$00", 0b00110001),
    ("A=$00 X=$03 Y=$00 SP=$ff PC=$0003", "$0200=$04 $0201=$00", 0b00110001),
    ("A=$00 X=$03 Y=$00 SP=$ff PC=$0006", "$0200=$03 $0201=$00", 0b00110001),
    ("A=$00 X=$03 Y=$00 SP=$ff PC=$0008", "$0200=$03 $0201=$00", 0b00110011),
    ("A=$00 X=$03 Y=$00 SP=$ff PC=$000a", "$0200=$03 $0201=$00", 0b00110011),
    ("A=$00 X=$03 Y=$00 SP=$ff PC=$000d", "$0200=$03 $0201=$03", 0b00110011),
]

print(program_asl_3)
test_assembly_cpu(program_rom_3, cycle_states_3, dissassembly_command_order_3)
