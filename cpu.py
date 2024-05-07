from typing import List

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

class CPU:
    register_a: int
    register_x: int
    status: int
    program_counter: int

    def __init__(self):
        self.register_x = 0 # 8 bits
        self.register_a = 0 # 8 bits
        self.program_counter = 0
        self.status = 0

    def lda(self, value):
        self.register_a = value
        self.update_zero_and_negative_flags(self.register_a)

    def update_zero_and_negative_flags(self, result):
        # Set zero flag if a is 0
        if result == 0:
            self.status |= 0b00000010
        else:
            self.status &= 0b11111101

        # set Negative flag if a's 7th bit is set
        if result & 0b1000000 != 0:
            self.status |= 0b10000000
        else:
            self.status &= 0b01111111

    def interpret(self, program: List[int]):
        opcode = program[self.program_counter]
        self.program_counter += 1

        match opcode:
            case 0xa9: # LDA
                param = program[self.program_counter]
                self.program_counter += 1
                self.lda(param)

            case 0xaa: # TAX
                self.register_x = self.register_a
                self.update_zero_and_negative_flags(self.register_x)

            case 0xe8: # INX
                self.register_x = (self.register_x + 1) & 0xFF
                self.update_zero_and_negative_flags(self.register_x)

            case 0x00:
                return

def test_0xa9_lda_immediate_load_data():
    cpu = CPU()
    cpu.interpret([0xa9, 0x05, 0x00])
    assert cpu.register_a == 0x05

    # make sure the zero flag isn't set
    assert cpu.status & 0b00000010 == 0b00

    # make sure negative flag isn't set
    assert cpu.status & 0b10000000 == 0b00

def test_0xa9_lda_zero_flag():
    cpu = CPU()
    cpu.interpret([0xa9, 0x00, 0x00])
    assert cpu.status & 0b00000010 == 0b10

def test_0xaa_tax_move_a_to_x():
    cpu = CPU()
    cpu.register_a = 10
    cpu.interpret([0xaa, 0x00])
    assert cpu.register_x == 10

def test_5_ops_working_together():
    cpu = CPU()
    cpu.interpret([0xa9, 0xc0, 0xaa, 0xe8, 0x00])
    assert cpu.register_x == 0xc1

def test_inx_overflow():
    cpu = CPU()
    cpu.register_x = 0xff
    cpu.interpret([0xe8, 0xe8, 0x00])
    assert cpu.register_x == 1
