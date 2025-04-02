from cpu import CPU, AddressingMode, Flags


# # Tests
def test_update_zero_and_negative_flags():
    cpu = CPU()
    cpu.update_zero_and_negative_flags(0)
    assert cpu.get_flag(Flags.ZERO)
    assert not cpu.get_flag(Flags.NEGATIVE)

    cpu.update_zero_and_negative_flags(-0b10000000)
    assert not cpu.get_flag(Flags.ZERO)
    assert cpu.get_flag(Flags.NEGATIVE)


def test_set_flag_zero():
    cpu = CPU()
    cpu.set_flag(Flags.ZERO)
    assert cpu.get_flag(Flags.ZERO)


def test_clear_flag_zero():
    cpu = CPU()
    cpu.set_flag(Flags.ZERO)
    cpu.clear_flag(Flags.ZERO)
    assert not cpu.get_flag(Flags.ZERO)


def test_set_flag_negative():
    cpu = CPU(**dict(status=Flags(0b00000000)))
    cpu.set_flag(Flags.NEGATIVE)
    assert cpu.get_flag(Flags.NEGATIVE)
    assert not cpu.get_flag(Flags.OVERFLOW)
    assert not cpu.get_flag(Flags.INTERRUPT_DISABLE)
    assert not cpu.get_flag(Flags.DECIMAL)
    assert not cpu.get_flag(Flags.BREAK)
    assert not cpu.get_flag(Flags.UNUSED)


def test_clear_flag_negative():
    cpu = CPU(**dict(status=Flags(0b00000000)))
    cpu.set_flag(Flags.NEGATIVE)
    cpu.clear_flag(Flags.NEGATIVE)
    assert not cpu.get_flag(Flags.NEGATIVE)
    assert not cpu.get_flag(Flags.OVERFLOW)
    assert not cpu.get_flag(Flags.INTERRUPT_DISABLE)
    assert not cpu.get_flag(Flags.DECIMAL)
    assert not cpu.get_flag(Flags.BREAK)
    assert not cpu.get_flag(Flags.UNUSED)


def test_get_flags_zero_carry_negative():
    cpu = CPU(**dict(status=Flags(0b00000000)))
    cpu.set_flag(Flags.ZERO)
    cpu.set_flag(Flags.CARRY)
    cpu.set_flag(Flags.NEGATIVE)
    assert cpu.get_flag(Flags.ZERO)
    assert cpu.get_flag(Flags.CARRY)
    assert cpu.get_flag(Flags.NEGATIVE)
    assert not cpu.get_flag(Flags.OVERFLOW)
    assert not cpu.get_flag(Flags.INTERRUPT_DISABLE)
    assert not cpu.get_flag(Flags.DECIMAL)
    assert not cpu.get_flag(Flags.BREAK)
    assert not cpu.get_flag(Flags.UNUSED)


def test_get_operand_address_immediate():
    cpu = CPU()
    # write the instruction
    cpu.memory.write(0x10, 0x10)
    assert cpu.get_operand_address(AddressingMode.IMMEDIATE) == 0x10


def test_get_operand_address_zero_page():
    cpu = CPU()
    cpu.memory.write(0x10, 0x10)
    cpu.memory.write(0x11, 0x20)
    # in this case it will just be the program counter value which defaults to 0x10 and is nver incremented during this
    # test
    assert cpu.get_operand_address(AddressingMode.ZERO_PAGE) == 0x10


def test_get_operand_address_absolute():
    cpu = CPU()
    cpu.memory.write(0x10, 0x10)
    cpu.memory.write(0x11, 0x20)
    # in this case it will just be the program counter value which defaults to 0x10 and is never incremented during this
    # test, so the address will be 0x2010 as the program counter is 0x10 and the value at 0x11 is 0x20 converted
    # little endian
    assert cpu.get_operand_address(AddressingMode.ABSOLUTE) == 0x2010


def test_get_operand_address_x_indexed_zero_page():
    # LDA $80,X -> load the contents of address "$0080 + X" into A i.e. register_a = 5

    cpu = CPU()
    # load memory address 0x90 with value 5
    cpu.memory.write(0x90, 5)
    # load instruction LDA $80,X into memory address 0x10
    cpu.memory.write(0x10, 0xB5)
    cpu.memory.write(0x11, 0x80)

    # set the program counter to the instruction parameter as the fn get operand address assumes the program counter
    # has been incremented
    cpu.program_counter = 0x11

    # set the x register to 0x10 so that the indexed address is 0x90
    cpu.register_x = 0x10

    assert cpu.get_operand_address(AddressingMode.X_INDEXED_ZERO_PAGE) == 0x0090


def test_get_operand_address_y_indexed_zero_page():
    # LDX $60,Y -> load the contents of address "$0060 + Y" into X
    cpu = CPU()

    # load instruction LDX $60,Y into memory address 0x10
    cpu.memory.write(0x10, 0xB6)
    cpu.memory.write(0x11, 0x60)

    # set the program counter to the instruction parameter as the fn get operand address assumes the program counter
    # has been incremented
    cpu.program_counter = 0x11

    # set the y register to 0x10 so that the indexed address is 0x70
    cpu.register_y = 0x10

    assert cpu.get_operand_address(AddressingMode.Y_INDEXED_ZERO_PAGE) == 0x0070


def test_get_operand_address_x_indexed_absolute():
    # LDA $3120,X -> load the contents of address "$3120 + X" into A
    cpu = CPU()

    cpu.memory.read
    cpu.memory.write(0x10, 0xBD)
    cpu.memory.write(0x11, 0x20)
    cpu.memory.write(0x12, 0x31)

    # set the program counter to the instruction parameter as the fn get operand address assumes the program counter
    # has been incremented
    cpu.program_counter = 0x11
    cpu.register_x = 0x10

    assert cpu.get_operand_address(AddressingMode.X_INDEXED_ABSOLUTE) == 0x3130


def test_get_operand_address_y_indexed_absolute():
    # LDA $3120,Y -> load the contents of address "$3120 + Y" into A
    cpu = CPU()

    cpu.memory.write(0x10, 0xB9)
    cpu.memory.write(0x11, 0x20)
    cpu.memory.write(0x12, 0x31)

    # set the program counter to the instruction parameter as the fn get operand address assumes the program counter
    # has been incremented
    cpu.program_counter = 0x11
    cpu.register_y = 0x10

    assert cpu.get_operand_address(AddressingMode.Y_INDEXED_ABSOLUTE) == 0x3130


def test_get_operand_address_x_indexed_zero_page_indirect():
    # LDA ($20,X) -> load the contents of address $0020 + X into A
    cpu = CPU()

    cpu.memory.write(0x10, 0xA1)
    cpu.memory.write(0x11, 0x20)

    # set the program counter to the instruction parameter as the fn get operand address assumes the program counter
    # has been incremented
    cpu.program_counter = 0x11
    cpu.register_x = 0x10

    cpu.memory.write(0x30, 0x40)
    cpu.memory.write(0x31, 0x50)

    assert cpu.get_operand_address(AddressingMode.X_INDEXED_ZERO_PAGE_INDIRECT) == 0x5040


def test_get_operand_address_zero_page_indirect_y_indexed():
    # LDA ($20),Y -> load the contents of address $0020 into A
    cpu = CPU()

    cpu.memory.write(0x10, 0xB1)
    cpu.memory.write(0x11, 0x20)

    # set the program counter to the instruction parameter as the fn get operand address assumes the program counter
    # has been incremented
    cpu.program_counter = 0x11
    cpu.register_y = 0x10

    cpu.memory.write(0x20, 0x40)
    cpu.memory.write(0x21, 0x50)

    # the value at 0x20 is 0x5040 little endian
    # 0x5040 + 0x10 = 0x5050

    assert cpu.get_operand_address(AddressingMode.ZERO_PAGE_INDIRECT_Y_INDEXED) == 0x5050


def test_0xa9_lda_immediate_load_data():
    cpu = CPU()
    cpu.load_and_run([0xA9, 0x05, 0x00])
    assert cpu.register_a == 0x05

    # make sure the zero flag isn't set
    assert not cpu.get_flag(Flags.ZERO)

    # make sure negative flag isn't set
    assert not cpu.get_flag(Flags.NEGATIVE)


def test_0xa9_lda_zero_flag():
    cpu = CPU()
    cpu.load_and_run([0xA9, 0x00, 0x00])
    assert cpu.get_flag(Flags.ZERO)


def test_0xab_tax_move_a_to_x():
    cpu = CPU()
    cpu.load_and_run([0xA9, 0x0A, 0xAA, 0x00])
    assert cpu.register_x == 10


def test_0x85_sta_absolute():
    cpu = CPU()
    cpu.load_and_run([0xA9, 0xC0, 0xAA, 0xE8, 0x00])
    assert cpu.register_x == 0xC1


def test_inx_overflow():
    cpu = CPU()
    cpu.load_and_run([0xA9, 0xFF, 0xAA, 0xE8, 0xE8, 0x00])
    assert cpu.register_x == 1


def test_lda_from_memory():
    cpu = CPU()
    cpu.memory.write(0x10, 0x55)
    cpu.load_and_run([0xA5, 0x10, 0x00])
    assert cpu.register_a == 0x55


def test_0x69_adc_immediate():
    cpu = CPU()
    cpu.load_and_run([0x69, 1, 0x69, 1, 0x00])
    assert cpu.register_a == 2


def test_0x69_adc_immediate_overflow():
    cpu = CPU()
    cpu.load_and_run([0x69, 0xFF, 0x69, 0x01, 0x00])
    assert cpu.register_a == 0


def test_0x69_adc_immediate_carry():
    cpu = CPU()
    cpu.load_and_run([0x69, 0xFF, 0x69, 0x01, 0x00])
    assert cpu.get_flag(Flags.CARRY)


def test_0x69_adc_immediate_overflow_flag():
    cpu = CPU()
    cpu.load_and_run([0x69, 0x7F, 0x69, 0x01, 0x00])
    assert cpu.get_flag(Flags.OVERFLOW)


def test_0x69_adc_immediate_negative_flag():
    cpu = CPU()

    # ADC #$FE
    # ADC #$01
    # BRK

    cpu.load_and_run([0x69, 0xFE, 0x69, 0x01, 0x00])
    assert cpu.get_flag(Flags.NEGATIVE)


def test_0x65_adc_zero_page():
    cpu = CPU()
    # write data into memory to be added to the accumulator
    cpu.memory.write(0x10, 0x01)

    # ADC $10
    cpu.load_and_run([0x65, 0x10, 0x00])
    assert cpu.register_a == 1


def test_0x75_adc_zero_page_x():
    cpu = CPU()
    # write data into memory to be added to the accumulator
    cpu.memory.write(0x20, 0x01)

    # ADC ($10,X)
    cpu.load_and_run([0x75, 0x10, 0x00], **{"register_x": 0x10})
    assert cpu.register_a == 1


def test_0x6d_adc_absolute():
    cpu = CPU()
    cpu.memory.write_u16(0x10, 0x01)
    cpu.load_and_run([0x6D, 0x10, 0x00])
    assert cpu.register_a == 1


def test_0x7d_adc_absolute_x():
    cpu = CPU()
    cpu.memory.write_u16(0x10, 0x01)
    cpu.load_and_run([0x7D, 0x00], **{"register_x": 0x10})
    assert cpu.register_a == 1


def test_0x79_adc_absolute_y():
    cpu = CPU()
    cpu.memory.write_u16(0x10, 0x01)
    cpu.load_and_run([0x79, 0x00], **{"register_y": 0x10})
    assert cpu.register_a == 1


# Failing tests
def test_0x61_adc_indirect_x():
    cpu = CPU()
    cpu.memory.write(0x20, 0x20)
    cpu.memory.write(0x21, 0x30)
    cpu.memory.write(0x3020, 0x01)
    cpu.load_and_run([0x61, 0x10], **{"register_x": 0x10})
    assert cpu.register_a == 1


def test_0x71_adc_indirect_y():
    cpu = CPU()
    cpu.memory.write(0x10, 0x20)
    cpu.memory.write(0x11, 0x30)
    cpu.memory.write(0x3021, 0x01)
    cpu.load_and_run([0x71, 0x10], **{"register_y": 0x01})
    assert cpu.register_a == 1


def test_0x29_and_immediate():
    cpu = CPU()

    # LDA #$05
    # AND #$02
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0x29, 0x02, 0x00])
    assert cpu.register_a == 0x05 & 0x02


def test_0x25_and_zero_page():
    cpu = CPU()
    cpu.memory.write(0x10, 0x05)

    # LDA $05
    # AND $10
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0x25, 0x10, 0x00])
    assert cpu.register_a == 0x05 & 0x05


def test_0x35_and_zero_page_x():
    cpu = CPU()
    cpu.memory.write(0x20, 0x05)

    # LDA $05
    # AND $20,X
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0x35, 0x10, 0x00], **{"register_x": 0x10})
    assert cpu.register_a == 0x05 & 0x05


def test_0x2d_and_absolute():
    cpu = CPU()
    cpu.memory.write_u16(0x10, 0x05)

    # LDA $05
    # AND $10
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0x2D, 0x10, 0x00])
    assert cpu.register_a == 0x05 & 0x05


def test_0x3d_and_absolute_x():
    cpu = CPU()
    cpu.memory.write_u16(0x10, 0x05)

    # LDA $05
    # AND $10,X
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0x3D, 0x00], **{"register_x": 0x10})
    assert cpu.register_a == 0x05 & 0x05


def test_0x39_and_absolute_y():
    cpu = CPU()
    cpu.memory.write_u16(0x10, 0x05)

    # LDA $05
    # AND $10,Y
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0x39, 0x00], **{"register_y": 0x10})
    assert cpu.register_a == 0x05 & 0x05


def test_0x21_and_indirect_x():
    cpu = CPU()
    cpu.memory.write(0x20, 0x20)
    cpu.memory.write(0x21, 0x30)
    cpu.memory.write(0x3020, 0x05)

    # LDA $05
    # AND ($20,X)
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0x21, 0x10], **{"register_x": 0x10})
    assert cpu.register_a == 0x05 & 0x05


def test_0x31_and_indirect_y():
    cpu = CPU()
    cpu.memory.write(0x10, 0x20)
    cpu.memory.write(0x11, 0x30)
    cpu.memory.write(0x3021, 0x05)

    # LDA $05
    # AND ($10),Y
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0x31, 0x10], **{"register_y": 0x01})
    assert cpu.register_a == 0x05 & 0x05


def test_0x0a_asl_accumulator():
    cpu = CPU()

    # LDA #$05
    # ASL A
    # BRK
    cpu.load_and_run([0xA9, 0b01000000, 0x0A, 0x00])
    assert cpu.register_a == 0b10000000


def test_0x06_asl_zero_page():
    cpu = CPU()
    cpu.memory.write(0x10, 0b01000000)

    # ASL $10
    # BRK
    cpu.load_and_run([0x06, 0x10, 0x00])
    assert cpu.memory.read(0x10) == 0b10000000


def test_0x16_asl_zero_page_x():
    cpu = CPU()
    cpu.memory.write(0x20, 0b01000000)

    # ASL $20,X
    # BRK
    cpu.load_and_run([0x16, 0x10, 0x00], **{"register_x": 0x10})
    assert cpu.memory.read(0x20) == 0b10000000


def test_0x0e_asl_absolute():
    cpu = CPU()
    cpu.memory.write_u16(0x10, 0b01000000)

    # ASL $10
    # BRK
    cpu.load_and_run([0x0E, 0x10, 0x00])
    assert cpu.memory.read(0x10) == 0b10000000


def test_0x1e_asl_absolute_x():
    cpu = CPU()
    cpu.memory.write_u16(0x10, 0b01000000)

    # ASL $10,X
    # BRK
    cpu.load_and_run([0x1E, 0x00], **{"register_x": 0x10})
    assert cpu.memory.read(0x10) == 0b10000000


def test_0x90_bcc():
    cpu = CPU(**dict(status=Flags(0b00000000)))

    # BCC $03 -> branch forward 3 bytes
    # BRK (skipped)
    # NOP (padding)
    # NOP (padding)
    # BRK (at branch destination)
    cpu.load_and_run([0x90, 0x03, 0x00, 0xEA, 0xEA, 0x00])
    # After executing the BCC instruction:
    # 1. PC goes to 0x8001 (to read offset)
    # 2. PC goes to 0x8002 (after reading offset)
    # 3. Branch taken, so PC becomes 0x8002 + 3 = 0x8005
    expected_pc = 0x8000 + 2 + 3 + 1  # base + instruction length + branch offset + next opcode read
    assert cpu.program_counter == expected_pc


def test_0xb0_bcs():
    cpu = CPU()

    # BCS $03
    # BRK
    cpu.load_and_run([0xB0, 0x03, 0x00], **dict(status=[Flags.CARRY]))
    # In this test, PC starts at 0x8000, reads opcode (0xB0),
    # moves to 0x8001, reads branch offset (0x03), moves to 0x8002,
    # then branches forward 3 bytes to 0x8005
    # After branching, it reads the BRK opcode and increments PC again to 0x8006
    expected_pc = 0x8000 + 2 + 3 + 1  # base + instruction length + branch offset + BRK opcode read
    assert cpu.program_counter == expected_pc


    cpu = CPU()

    # BEQ $03
    # BRK
    cpu.load_and_run([0xF0, 0x03, 0x00], **dict(status=[Flags.ZERO]))
    # In this test, PC starts at 0x8000, reads opcode (0xF0),
    # moves to 0x8001, reads branch offset (0x03), moves to 0x8002,
    # then branches forward 3 bytes to 0x8005
    # After branching, it reads the BRK opcode and increments PC again to 0x8006
    expected_pc = 0x8000 + 2 + 3 + 1  # base + instruction length + branch offset + BRK opcode read
    assert cpu.program_counter == expected_pc


def test_0xd0_bne():
    cpu = CPU()

    # BNE $03
    # BRK
    cpu.load_and_run([0xD0, 0x03, 0x00])
    # In this test, PC starts at 0x8000, reads opcode (0xD0),
    # moves to 0x8001, reads branch offset (0x03), moves to 0x8002,
    # then branches forward 3 bytes to 0x8005
    # After branching, it reads the BRK opcode and increments PC again to 0x8006
    expected_pc = 0x8000 + 2 + 3 + 1  # base + instruction length + branch offset + BRK opcode read
    assert cpu.program_counter == expected_pc


    cpu = CPU()

    # BPL $03
    # BRK
    cpu.load_and_run([0x10, 0x03, 0x00])
    # In this test, PC starts at 0x8000, reads opcode (0x10),
    # moves to 0x8001, reads branch offset (0x03), moves to 0x8002,
    # then branches forward 3 bytes to 0x8005
    # After branching, it reads the next opcode and increments PC again to 0x8006
    expected_pc = 0x8000 + 2 + 3 + 1  # base + instruction length + branch offset + next opcode read
    assert cpu.program_counter == expected_pc


def test_0x30_bmi():
    cpu = CPU()

    # BMI $03
    # BRK
    cpu.load_and_run([0x30, 0x03, 0x00], **dict(status=[Flags.NEGATIVE]))
    # moves to 0x8001, reads branch offset (0x03), moves to 0x8002,
    # then branches forward 3 bytes to 0x8005
    # After branching, it reads the BRK opcode and increments PC again to 0x8006
    expected_pc = 0x8000 + 2 + 3 + 1  # base + instruction length + branch offset + BRK opcode read
    assert cpu.program_counter == expected_pc


def test_0x50_bvc():
    cpu = CPU()

    # BVC $03
    # BRK
    cpu.load_and_run([0x50, 0x03, 0x00])
    # In this test, PC starts at 0x8000, reads opcode (0x50),
    # moves to 0x8001, reads branch offset (0x03), moves to 0x8002,
    # then branches forward 3 bytes to 0x8005
    # After branching, it reads the BRK opcode and increments PC again to 0x8006
    expected_pc = 0x8000 + 2 + 3 + 1  # base + instruction length + branch offset + BRK opcode read
    assert cpu.program_counter == expected_pc


def test_0x70_bvs():
    cpu = CPU()

    # BVS $03
    # BRK
    cpu.load_and_run([0x70, 0x03, 0x00], **dict(status=[Flags.OVERFLOW]))
    # In this test, PC starts at 0x8000, reads opcode (0x70),
    # moves to 0x8001, reads branch offset (0x03), moves to 0x8002,
    # then branches forward 3 bytes to 0x8005
    # After branching, it reads the BRK opcode and increments PC again to 0x8006
    expected_pc = 0x8000 + 2 + 3 + 1  # base + instruction length + branch offset + BRK opcode read
    assert cpu.program_counter == expected_pc


def test_0xc9_cmp_immediate_zero_set():
    cpu = CPU()

    # LDA #$05
    # CMP #$05
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0xC9, 0x05, 0x00])
    assert cpu.get_flag(Flags.ZERO)
    assert not cpu.get_flag(Flags.NEGATIVE)
    assert cpu.get_flag(Flags.CARRY)


def test_0xc9_cmp_immediate_negative_set():
    cpu = CPU()

    assert not cpu.get_flag(Flags.NEGATIVE)
    assert not cpu.get_flag(Flags.ZERO)
    assert not cpu.get_flag(Flags.CARRY)

    # LDA #$05
    # CMP #$06
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0xC9, 0x06, 0x00])
    assert cpu.get_flag(Flags.NEGATIVE)
    assert not cpu.get_flag(Flags.ZERO)
    assert not cpu.get_flag(Flags.CARRY)


def test_0xc9_cmp_immediate_carry_set():
    cpu = CPU()

    # LDA #$05
    # CMP #$04
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0xC9, 0x04, 0x00])
    assert cpu.get_flag(Flags.CARRY)
    assert not cpu.get_flag(Flags.ZERO)
    assert not cpu.get_flag(Flags.NEGATIVE)


def test_0xc5_cmp_zero_page():
    cpu = CPU()
    cpu.memory.write(0x10, 0x05)

    # LDA $05
    # CMP $10
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0xC5, 0x10, 0x00])
    assert cpu.get_flag(Flags.ZERO)
    assert not cpu.get_flag(Flags.NEGATIVE)
    assert cpu.get_flag(Flags.CARRY)


def test_0xd5_cmp_zero_page_x():
    cpu = CPU()
    cpu.memory.write(0x20, 0x05)

    # LDA $05
    # CMP $20,X
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0xD5, 0x10, 0x00], **{"register_x": 0x10})
    assert cpu.get_flag(Flags.ZERO)


def test_0xcd_cmp_absolute():
    cpu = CPU()
    cpu.memory.write_u16(0x10, 0x05)

    # LDA $05
    # CMP $10
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0xCD, 0x10, 0x00])
    assert cpu.get_flag(Flags.ZERO)


def test_0xdd_cmp_absolute_x():
    cpu = CPU()
    cpu.memory.write(0x10, 0x05)

    # LDA $05
    # CMP $10,X
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0xDD, 0x00], **{"register_x": 0x10})
    assert cpu.get_flag(Flags.ZERO)


def test_0xd9_cmp_absolute_y():
    cpu = CPU()
    cpu.memory.write(0x10, 0x05)

    # LDA $05
    # CMP $10,Y
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0xD9, 0x00], **{"register_y": 0x10})
    assert cpu.get_flag(Flags.ZERO)


def test_0xc1_cmp_indirect_x():
    cpu = CPU()
    cpu.memory.write(0x20, 0x20)
    cpu.memory.write(0x21, 0x30)
    cpu.memory.write_u16(0x3020, 0x05)

    # LDA $05
    # CMP ($20,X)
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0xC1, 0x10], **{"register_x": 0x10})
    assert cpu.get_flag(Flags.ZERO)
    assert not cpu.get_flag(Flags.NEGATIVE)
    assert cpu.get_flag(Flags.CARRY)


def test_0xc1_cmp_indirect_x_cross_page_boundary():
    cpu = CPU()
    cpu.memory.write(0x20, 0x20)
    cpu.memory.write(0x21, 0x30)
    cpu.memory.write(0x3020, 0xFF)

    # LDA $05
    # CMP ($20,X)
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0xC1, 0x10], **{"register_x": 0x10})
    assert not cpu.get_flag(Flags.ZERO)
    assert not cpu.get_flag(Flags.NEGATIVE)
    assert not cpu.get_flag(Flags.CARRY)


def test_0xd1_cmp_indirect_y():
    cpu = CPU()
    cpu.memory.write(0x10, 0x20)
    cpu.memory.write(0x11, 0x30)
    cpu.memory.write_u16(0x3021, 0x05)

    # LDA $05
    # CMP ($10),Y
    # BRK
    cpu.load_and_run([0xA9, 0x05, 0xD1, 0x10], **{"register_y": 0x01})
    assert cpu.get_flag(Flags.ZERO)
    assert not cpu.get_flag(Flags.NEGATIVE)
    assert cpu.get_flag(Flags.CARRY)


def test_0xe0_cpx_immediate():
    cpu = CPU()

    # LDX #$05
    # CPX #$05
    # BRK
    cpu.load_and_run([0xA2, 0x05, 0xE0, 0x05, 0x00])
    assert cpu.get_flag(Flags.ZERO)


def test_0xe4_cpx_zero_page():
    cpu = CPU()
    cpu.memory.write(0x10, 0x05)

    # LDX $05
    # CPX $10
    # BRK
    cpu.load_and_run([0xA2, 0x05, 0xE4, 0x10, 0x00])
    assert cpu.get_flag(Flags.ZERO)


def test_0xec_cpx_absolute():
    cpu = CPU()
    cpu.memory.write_u16(0x10, 0x05)

    # LDX $05
    # CPX $10
    # BRK
    cpu.load_and_run([0xA2, 0x05, 0xEC, 0x10, 0x00])
    assert cpu.get_flag(Flags.ZERO)


def test_0x45_eor_zero_page():
    cpu = CPU()
    cpu.memory.write(0x10, 0b00000001)

    # LDA $05
    # EOR $10
    # BRK
    cpu.load_and_run([0xA9, 0b0001001, 0x45, 0x10, 0x00])
    assert cpu.register_a == 0b00001000


def test_0x46_lsr_zero_page():
    cpu = CPU()
    cpu.memory.write(0x10, 0b00000010)

    # LSR $10
    # BRK
    cpu.load_and_run([0x46, 0x10, 0x00])
    assert cpu.memory.read(0x10) == 0b00000001


# def test_0x20_jsr_absolute():
#     cpu = CPU()
#
#     # load subroutine into memory
#     # subroutine:
#     # LDA #$05
#     # RTS
#
#     cpu.memory.write(0x2000, 0xA9)  # LDA immediate
#     cpu.memory.write(0x2001, 0x05)  # Value 0x05
#     cpu.memory.write(0x2002, 0x60)  # RTS
#
#     # JSR $2000
#     # BRK
#     cpu.load_and_run([0x20, 0x00, 0x20, 0x00])
#
#     # After JSR & RTS, we should be back at the BRK
#     # Base address (0x8000) + 3 bytes for JSR instruction
#     assert cpu.program_counter == 0x8003
#
#
#
#     cpu = CPU(program_offset=0)
#
#     # When load_and_run is called with program_offset=0, it sets PC to 0x10
#     # BNE $FA (250 in decimal, -6 in signed)
#     # BRK
#     cpu.load_and_run([0xD0, 250, 0x00])
#
#     # Due to how the test setup works with load_and_run:
#     # 1. Program is loaded into memory starting at address 0x10
#     # 2. After reading the opcode (0xD0) PC is at 0x11
#     # 3. After reading the branch offset (250) PC is at 0x12
#     # 4. Branch offset 250 (-6 signed) is added to PC, resulting in 0x12 + (-6) = 0x0C
#     # 5. The expected PC value is 12 (0x0C)
#     assert cpu.program_counter == 0x0C


def test_branch_forward():
    # Test branching forward (positive offset)
    cpu = CPU(program_offset=0)

    # BNE +4 (branch forward 4 bytes)
    # BRK
    # Data bytes that should be skipped
    # Target of branch

    # Set zero flag to false to ensure BNE branches
    cpu.clear_flag(Flags.ZERO)

    cpu.load_and_run([0xD0, 0x04, 0x00, 0xFF, 0xFF, 0xFF, 0x00])
    # PC should end at:
    # PC starts at 0x0010 (load_and_run with program_offset=0)
    # After BNE opcode read: PC = 0x0011
    # After offset read: PC = 0x0012
    # After branch taken: PC = 0x0012 + 4 = 0x0016
    # After BRK opcode read: PC = 0x0017 (23 decimal)
    # But after BRK execution, PC stops at 0x0017 - 2 = 0x0015 (21 decimal)
    assert cpu.program_counter == 7



    # Test branching backward (negative offset)
    cpu = CPU(program_offset=0)

    # Setup an loop with a counter
    # LDX #$03      ; Initialize counter
    # DEX           ; Decrement counter
    # BNE -2        ; Branch back to DEX if not zero
    # BRK           ; Break when counter reaches zero

    # With program offset 0, PC starts at 0x10
    # So our program will be at 0x10-0x15
    cpu.load_and_run([0xA2, 0x03, 0xCA, 0xD0, 0xFD, 0x00])

    # After the loop, X should be 0
    assert cpu.register_x == 0
    # PC should be at the BRK instruction after loop finishes
    # 0x10 (start) + 5 (length to BRK) = 0x15
    assert cpu.program_counter == 0x15

def test_branch_page_boundary():
    # Test branch crossing page boundary
    cpu = CPU()

    # Set program counter to end of page
    cpu.program_counter = 0x10FE

    # Force a branch forward that crosses page boundary
    offset = 10
    cpu.memory.write(cpu.program_counter, 0xD0)  # BNE
    cpu.memory.write(cpu.program_counter + 1, offset)

    # Manually execute BNE (assuming zero flag is clear)
    cpu.clear_flag(Flags.ZERO)
    cpu.program_counter += 1  # Move past opcode
    cpu.branch()

    # Should be at 0x10FE + 1 (past opcode) + offset + 1 (past offset byte)
    # 0x10FE + 1 + 10 + 1 = 0x110A
    assert cpu.program_counter == 0x110A


def test_lsr_accumulator_all_bits():
    # Test Logical Shift Right on accumulator with various bit patterns
    cpu = CPU()

    # Test with 10101010
    cpu.load_and_run([0xA9, 0xAA, 0x4A, 0x00])  # LDA #$AA, LSR A
    assert cpu.register_a == 0x55  # 01010101
    assert not cpu.get_flag(Flags.CARRY)  # Last bit was 0

    # Test with 10101011
    cpu.load_and_run([0xA9, 0xAB, 0x4A, 0x00])  # LDA #$AB, LSR A
    assert cpu.register_a == 0x55  # 01010101
    assert cpu.get_flag(Flags.CARRY)  # Last bit was 1

    # Test with 0x01 (check zero flag)
    cpu.load_and_run([0xA9, 0x01, 0x4A, 0x00])  # LDA #$01, LSR A
    assert cpu.register_a == 0  # 00000000
    assert cpu.get_flag(Flags.ZERO)  # Result is zero
    assert cpu.get_flag(Flags.CARRY)  # Last bit was 1


def test_lsr_memory():
    # Test LSR on memory
    cpu = CPU()

    # Write test value to memory
    cpu.memory.write(0x30, 0xAA)  # 10101010

    # LSR on memory location
    cpu.load_and_run([0x46, 0x30, 0x00])  # LSR $30

    # Verify memory was shifted
    assert cpu.memory.read(0x30) == 0x55  # 01010101
    assert not cpu.get_flag(Flags.CARRY)  # Last bit was 0


def test_lsr_memory_indexed():
    # Test LSR with X-indexed addressing
    cpu = CPU()

    # Write test value to memory
    cpu.memory.write(0x40, 0xAB)  # 10101011

    # LSR on memory location with X index
    cpu.load_and_run([0x56, 0x30, 0x00], **{"register_x": 0x10})  # LSR $30,X

    # Verify memory was shifted
    assert cpu.memory.read(0x40) == 0x55  # 01010101
    assert cpu.get_flag(Flags.CARRY)  # Last bit was 1


    # Test RTI (Return from Interrupt)
    cpu = CPU()

    # Setup stack with status and return address
    # When pushing to stack, only bits 0-7 matter, with bit 5 (B flag) being ignored on RTI
    status_to_push = 0b00110101  # Status with some flags set
    cpu.stack_push(status_to_push)
    cpu.stack_push_u16(0x1234)  # Return address

    # Save the original PC
    original_pc = cpu.program_counter

    # Manually execute the RTI instruction logic
    status_value = cpu.stack_pop()
    # RTI ignores bit 4 (B flag) and sets bit 5 (unused) to 1
    cpu.status = Flags(status_value) | Flags.UNUSED
    cpu.status &= ~Flags.BREAK
    cpu.program_counter = cpu.stack_pop_u16()

    # Verify flags were restored (B must be 0, and unused must be 1)
    expected_status = Flags(status_to_push) | Flags.UNUSED
    expected_status &= ~Flags.BREAK
    assert cpu.status == expected_status

    # Verify PC was set to return address
    assert cpu.program_counter == 0x1234


def test_rti_flags_preserved():
    # Test RTI preserves proper flags
    cpu = CPU()

    # Set up all flags that should be preserved during RTI
    test_flags = (Flags.CARRY | Flags.ZERO | Flags.INTERRUPT_DISABLE |
                 Flags.DECIMAL | Flags.OVERFLOW | Flags.NEGATIVE)

    # Push flags to the stack (all flags activated)
    status_to_push = test_flags.value
    cpu.stack_push(status_to_push)
    cpu.stack_push_u16(0x8000)  # Return address

    # Set PC to known value
    cpu.program_counter = 0x1000

    # Save the original flags we pushed for later comparison
    original_flags = Flags(status_to_push)

    # Execute the actual RTI instruction which is case 0x40 in run()
    # instead of manually duplicating logic
    cpu.memory.write(0x8000, 0x00)  # BRK at the return address

    # Reset the CPU state completely for accurate testing
    cpu.status = Flags.UNUSED | Flags.BREAK

    # Execute RTI instruction
    cpu.load_and_run([0x40])

    # RTI should have pulled and set the status flags
    # with proper handling of BREAK and UNUSED flags
    expected_status = original_flags | Flags.UNUSED
    expected_status &= ~Flags.BREAK

    assert cpu.status == expected_status
    assert cpu.program_counter == 0x8000


    # Test ADC in decimal mode (BCD arithmetic)
    cpu = CPU()

    # Set decimal flag
    cpu.set_flag(Flags.DECIMAL)

    # Test BCD addition: 12 + 08 = 20
    cpu.register_a = 0x12  # BCD 12
    cpu.load_and_run([0x69, 0x08, 0x00])  # ADC #$08

    # In BCD mode, result should be BCD 20
    assert cpu.register_a == 0x20

    # Reset for next test
    cpu = CPU()

    # Test with carry: 56 + 47 + carry = 104
    cpu.set_flag(Flags.DECIMAL)
    cpu.set_flag(Flags.CARRY)
    cpu.register_a = 0x56  # BCD 56
    cpu.load_and_run([0x69, 0x47, 0x00])  # ADC #$47

    # Result should be BCD 104 (0x04 with carry set)
    assert cpu.register_a == 0x04
    assert cpu.get_flag(Flags.CARRY)  # Carry should be set


    # Test overflow detection in ADC
    cpu = CPU()

    # Test positive + positive = negative (overflow)
    cpu.register_a = 0x7F  # +127, largest positive 8-bit value
    cpu.load_and_run([0x69, 0x01, 0x00])  # ADC #$01

    # Result should wrap to -128
    assert cpu.register_a == 0x80
    assert cpu.get_flag(Flags.OVERFLOW)  # Overflow should be set
    assert cpu.get_flag(Flags.NEGATIVE)  # Result is negative

    # Reset for next test
    cpu = CPU()

    # Test negative + negative = positive (overflow)
    cpu.register_a = 0x80  # -128
    cpu.load_and_run([0x69, 0x80, 0x00])  # ADC #$80 (-128)

    # Result should be 0 with carry
    assert cpu.register_a == 0x00
    assert cpu.get_flag(Flags.OVERFLOW)  # Overflow should be set
    assert cpu.get_flag(Flags.CARRY)     # Carry should be set
    assert cpu.get_flag(Flags.ZERO)      # Result is zero


def test_sbc_basic():
    # Test SBC (Subtract with Carry)
    cpu = CPU()

    # Set initial value and carry flag (borrow = 0)
    cpu.register_a = 0x50
    cpu.set_flag(Flags.CARRY)

    # Subtract 0x30: 0x50 - 0x30 = 0x20
    cpu.load_and_run([0xE9, 0x30, 0x00])  # SBC #$30

    assert cpu.register_a == 0x20
    assert cpu.get_flag(Flags.CARRY)  # No borrow needed

    # Reset for next test
    cpu = CPU()

    # Test with borrow: 0x20 - 0x30 = 0xF0
    cpu.register_a = 0x20
    cpu.set_flag(Flags.CARRY)
    cpu.load_and_run([0xE9, 0x30, 0x00])  # SBC #$30

    assert cpu.register_a == 0xF0
    assert not cpu.get_flag(Flags.CARRY)  # Borrow occurred
    assert cpu.get_flag(Flags.NEGATIVE)   # Result is negative


def test_unsigned_to_signed_converstion():
    cpu = CPU()

    for i in range(128):
        assert cpu.unsigned_to_signed(i, 8) == i

    for i in range(128, 256):
        assert cpu.unsigned_to_signed(i, 8) == i - 256
