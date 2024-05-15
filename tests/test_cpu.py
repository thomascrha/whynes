from src.cpu import CPU, Flags, AddressingMode


# # Tests
def test_update_zero_and_negative_flags():
    cpu = CPU()
    cpu.update_zero_and_negative_flags(0)
    assert cpu.get_flag(Flags.ZERO)
    assert not cpu.get_flag(Flags.NEGATIVE)

    cpu.update_zero_and_negative_flags(0b11111111)
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
    cpu.mem_write(0x10, 0x10)
    assert cpu.get_operand_address(AddressingMode.IMMEDIATE) == 0x10

def test_get_operand_address_zero_page():
    cpu = CPU()
    cpu.mem_write(0x10, 0x10)
    cpu.mem_write(0x11, 0x20)
    # in this case it will just be the program counter value which defaults to 0x10 and is nver incremented during this
    # test
    assert cpu.get_operand_address(AddressingMode.ZERO_PAGE) == 0x10

def test_get_operand_address_absolute():
    cpu = CPU()
    cpu.mem_write(0x10, 0x10)
    cpu.mem_write(0x11, 0x20)
    # in this case it will just be the program counter value which defaults to 0x10 and is never incremented during this
    # test, so the address will be 0x2010 as the program counter is 0x10 and the value at 0x11 is 0x20 converted
    # little endian
    assert cpu.get_operand_address(AddressingMode.ABSOLUTE) == 0x2010

def test_get_operand_address_x_indexed_zero_page():
    # LDA $80,X -> load the contents of address "$0080 + X" into A i.e. register_a = 5

    cpu = CPU()
    # load memory address 0x90 with value 5
    cpu.mem_write(0x90, 5)
    # load instruction LDA $80,X into memory address 0x10
    cpu.mem_write(0x10, 0xb5)
    cpu.mem_write(0x11, 0x80)

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
    cpu.mem_write(0x10, 0xb6)
    cpu.mem_write(0x11, 0x60)

    # set the program counter to the instruction parameter as the fn get operand address assumes the program counter
    # has been incremented
    cpu.program_counter = 0x11

    # set the y register to 0x10 so that the indexed address is 0x70
    cpu.register_y = 0x10

    assert cpu.get_operand_address(AddressingMode.Y_INDEXED_ZERO_PAGE) == 0x0070

def test_get_operand_address_x_indexed_absolute():
    # LDA $3120,X -> load the contents of address "$3120 + X" into A
    cpu = CPU()

    cpu.mem_read
    cpu.mem_write(0x10, 0xbd)
    cpu.mem_write(0x11, 0x20)
    cpu.mem_write(0x12, 0x31)

    # set the program counter to the instruction parameter as the fn get operand address assumes the program counter
    # has been incremented
    cpu.program_counter = 0x11
    cpu.register_x = 0x10

    assert cpu.get_operand_address(AddressingMode.X_INDEXED_ABSOLUTE) == 0x3130

def test_get_operand_address_y_indexed_absolute():
    # LDA $3120,Y -> load the contents of address "$3120 + Y" into A
    cpu = CPU()

    cpu.mem_write(0x10, 0xb9)
    cpu.mem_write(0x11, 0x20)
    cpu.mem_write(0x12, 0x31)

    # set the program counter to the instruction parameter as the fn get operand address assumes the program counter
    # has been incremented
    cpu.program_counter = 0x11
    cpu.register_y = 0x10

    assert cpu.get_operand_address(AddressingMode.Y_INDEXED_ABSOLUTE) == 0x3130

def test_get_operand_address_x_indexed_zero_page_indirect():
    # LDA ($20,X) -> load the contents of address $0020 + X into A
    cpu = CPU()

    cpu.mem_write(0x10, 0xa1)
    cpu.mem_write(0x11, 0x20)

    # set the program counter to the instruction parameter as the fn get operand address assumes the program counter
    # has been incremented
    cpu.program_counter = 0x11
    cpu.register_x = 0x10

    cpu.mem_write(0x30, 0x40)
    cpu.mem_write(0x31, 0x50)

    assert cpu.get_operand_address(AddressingMode.X_INDEXED_ZERO_PAGE_INDIRECT) == 0x5040

def test_get_operand_address_zero_page_indirect_y_indexed():
    # LDA ($20),Y -> load the contents of address $0020 into A
    cpu = CPU()

    cpu.mem_write(0x10, 0xb1)
    cpu.mem_write(0x11, 0x20)

    # set the program counter to the instruction parameter as the fn get operand address assumes the program counter
    # has been incremented
    cpu.program_counter = 0x11
    cpu.register_y = 0x10

    cpu.mem_write(0x20, 0x40)
    cpu.mem_write(0x21, 0x50)

    # the value at 0x20 is 0x5040 little endian
    # 0x5040 + 0x10 = 0x5050

    assert cpu.get_operand_address(AddressingMode.ZERO_PAGE_INDIRECT_Y_INDEXED) == 0x5050

def test_0xa9_lda_immediate_load_data():
    cpu = CPU()
    cpu.load_and_run([0xa9, 0x05, 0x00])
    assert cpu.register_a == 0x05

    # make sure the zero flag isn't set
    assert cpu.get_flag(Flags.ZERO) == False

    # make sure negative flag isn't set
    assert cpu.get_flag(Flags.NEGATIVE) == False

def test_0xa9_lda_zero_flag():
    cpu = CPU()
    cpu.load_and_run([0xa9, 0x00, 0x00])
    assert cpu.get_flag(Flags.ZERO)

def test_0xab_tax_move_a_to_x():
    cpu = CPU()
    cpu.load_and_run([0xa9, 0x0A, 0xaa, 0x00])
    assert cpu.register_x == 10

def test_0x85_sta_absolute():
    cpu = CPU()
    cpu.load_and_run([0xa9, 0xc0, 0xaa, 0xe8, 0x00])
    assert cpu.register_x == 0xc1

def test_inx_overflow():
    cpu = CPU()
    cpu.load_and_run([0xa9, 0xff, 0xaa,0xe8, 0xe8, 0x00])
    assert cpu.register_x == 1

def test_lda_from_memory():
    cpu = CPU()
    cpu.mem_write(0x10, 0x55)
    cpu.load_and_run([0xa5, 0x10, 0x00])
    assert cpu.register_a == 0x55

def test_0x69_adc_immediate():
    cpu = CPU()
    cpu.load_and_run([0x69, 1, 0x69, 1, 0x00])
    assert cpu.register_a == 2

def test_0x69_adc_immediate_overflow():
    cpu = CPU()
    cpu.load_and_run([0x69, 0xff, 0x69, 0x01, 0x00])
    assert cpu.register_a == 0

def test_0x69_adc_immediate_carry():
    cpu = CPU()
    cpu.load_and_run([0x69, 0xff, 0x69, 0x01, 0x00])
    assert cpu.get_flag(Flags.CARRY)

def test_0x69_adc_immediate_overflow_flag():
    cpu = CPU()
    cpu.load_and_run([0x69, 0x7f, 0x69, 0x01, 0x00])
    assert cpu.get_flag(Flags.OVERFLOW)

def test_0x69_adc_immediate_negative_flag():
    cpu = CPU()
    cpu.load_and_run([0x69, 0xfe, 0x69, 0x01, 0x00])
    assert cpu.get_flag(Flags.NEGATIVE)

def test_0x65_adc_zero_page():
    cpu = CPU()
    # write data into memory to be added to the accumulator
    cpu.mem_write(0x10, 0x01)

    # ADC $10
    cpu.load_and_run([0x65, 0x10, 0x00])
    assert cpu.register_a == 1

def test_0x75_adc_zero_page_x():
    cpu = CPU()
    # write data into memory to be added to the accumulator
    cpu.mem_write(0x20, 0x01)

    # ADC ($10,X)
    cpu.load_and_run([0x75, 0x10, 0x00], **{"register_x": 0x10})
    assert cpu.register_a == 1

def test_0x6d_adc_absolute():
    cpu = CPU()
    cpu.mem_write_u16(0x10, 0x01)
    cpu.load_and_run([0x6d, 0x10, 0x00])
    assert cpu.register_a == 1

def test_0x7d_adc_absolute_x():
    cpu = CPU()
    cpu.mem_write_u16(0x10, 0x01)
    cpu.load_and_run([0x7d, 0x00], **{"register_x": 0x10})
    assert cpu.register_a == 1

def test_0x79_adc_absolute_y():
    cpu = CPU()
    cpu.mem_write_u16(0x10, 0x01)
    cpu.load_and_run([0x79, 0x00], **{"register_y": 0x10})
    assert cpu.register_a == 1

# Failing tests
def test_0x61_adc_indirect_x():
    cpu = CPU()
    cpu.mem_write(0x20, 0x20)
    cpu.mem_write(0x21, 0x30)
    cpu.mem_write(0x3020, 0x01)
    cpu.load_and_run([0x61, 0x10], **{"register_x": 0x10})
    assert cpu.register_a == 1

def test_0x71_adc_indirect_y():
    cpu = CPU()
    cpu.mem_write(0x10, 0x20)
    cpu.mem_write(0x11, 0x30)
    cpu.mem_write(0x3021, 0x01)
    cpu.load_and_run([0x71, 0x10], **{"register_y": 0x01})
    assert cpu.register_a == 1

def test_0x29_and_immediate():
    cpu = CPU()

    # LDA #$05
    # AND #$02
    # BRK
    cpu.load_and_run([0xa9, 0x05, 0x29, 0x02, 0x00])
    assert cpu.register_a == 0x05 & 0x02

def test_0x25_and_zero_page():
    cpu = CPU()
    cpu.mem_write(0x10, 0x05)

    # LDA $05
    # AND $10
    # BRK
    cpu.load_and_run([0xa9, 0x05, 0x25, 0x10, 0x00])
    assert cpu.register_a == 0x05 & 0x05

def test_0x35_and_zero_page_x():
    cpu = CPU()
    cpu.mem_write(0x20, 0x05)

    # LDA $05
    # AND $20,X
    # BRK
    cpu.load_and_run([0xa9, 0x05, 0x35, 0x10, 0x00], **{"register_x": 0x10})
    assert cpu.register_a == 0x05 & 0x05

def test_0x2d_and_absolute():
    cpu = CPU()
    cpu.mem_write_u16(0x10, 0x05)

    # LDA $05
    # AND $10
    # BRK
    cpu.load_and_run([0xa9, 0x05, 0x2d, 0x10, 0x00])
    assert cpu.register_a == 0x05 & 0x05

def test_0x3d_and_absolute_x():
    cpu = CPU()
    cpu.mem_write_u16(0x10, 0x05)

    # LDA $05
    # AND $10,X
    # BRK
    cpu.load_and_run([0xa9, 0x05, 0x3d, 0x00], **{"register_x": 0x10})
    assert cpu.register_a == 0x05 & 0x05

def test_0x39_and_absolute_y():
    cpu = CPU()
    cpu.mem_write_u16(0x10, 0x05)

    # LDA $05
    # AND $10,Y
    # BRK
    cpu.load_and_run([0xa9, 0x05, 0x39, 0x00], **{"register_y": 0x10})
    assert cpu.register_a == 0x05 & 0x05

def test_0x21_and_indirect_x():
    cpu = CPU()
    cpu.mem_write(0x20, 0x20)
    cpu.mem_write(0x21, 0x30)
    cpu.mem_write(0x3020, 0x05)

    # LDA $05
    # AND ($20,X)
    # BRK
    cpu.load_and_run([0xa9, 0x05, 0x21, 0x10], **{"register_x": 0x10})
    assert cpu.register_a == 0x05 & 0x05

def test_0x31_and_indirect_y():
    cpu = CPU()
    cpu.mem_write(0x10, 0x20)
    cpu.mem_write(0x11, 0x30)
    cpu.mem_write(0x3021, 0x05)

    # LDA $05
    # AND ($10),Y
    # BRK
    cpu.load_and_run([0xa9, 0x05, 0x31, 0x10], **{"register_y": 0x01})
    assert cpu.register_a == 0x05 & 0x05

def test_0x0a_asl_accumulator():
    cpu = CPU()

    # LDA #$05
    # ASL A
    # BRK
    cpu.load_and_run([0xa9, 0b01000000, 0x0a, 0x00])
    assert cpu.register_a == 0b10000000

def test_0x06_asl_zero_page():
    cpu = CPU()
    cpu.mem_write(0x10, 0b01000000)

    # ASL $10
    # BRK
    cpu.load_and_run([0x06, 0x10, 0x00])
    assert cpu.mem_read(0x10) == 0b10000000

def test_0x16_asl_zero_page_x():
    cpu = CPU()
    cpu.mem_write(0x20, 0b01000000)

    # ASL $20,X
    # BRK
    cpu.load_and_run([0x16, 0x10, 0x00], **{"register_x": 0x10})
    assert cpu.mem_read(0x20) == 0b10000000

def test_0x0e_asl_absolute():
    cpu = CPU()
    cpu.mem_write_u16(0x10, 0b01000000)

    # ASL $10
    # BRK
    cpu.load_and_run([0x0e, 0x10, 0x00])
    assert cpu.mem_read(0x10) == 0b10000000

def test_0x1e_asl_absolute_x():
    cpu = CPU()
    cpu.mem_write_u16(0x10, 0b01000000)

    # ASL $10,X
    # BRK
    cpu.load_and_run([0x1e, 0x00], **{"register_x": 0x10})
    assert cpu.mem_read(0x10) == 0b10000000

def test_0x90_bcc():
    cpu = CPU(**dict(status=Flags(0b00000000)))

    # Program Counter 0xFFFC

    # BCC $03 -> #3
    # BRK
    cpu.load_and_run([0x90, 0x03, 0x00])
                                # branch + pc + (len(prog) - 1)
    assert cpu.program_counter ==  0x03 + 0x8000 + 0x02

def test_0xb0_bcs():
    cpu = CPU()

    # BCS $03
    # BRK
    cpu.load_and_run([0xb0, 0x03, 0x00], **dict(status=[Flags.CARRY]))
                                # branch + pc + (len(prog) - 1)
    assert cpu.program_counter ==  0x03 + 0x8000 + 0x02

def test_0xf0_beq():
    cpu = CPU()

    # BEQ $03
    # BRK
    cpu.load_and_run([0xf0, 0x03, 0x00], **dict(status=[Flags.ZERO]))
                                # branch + pc + (len(prog) - 1)
    assert cpu.program_counter ==  0x03 + 0x8000 + 0x02

def test_0xd0_bne():
    cpu = CPU()

    # BNE $03
    # BRK
    cpu.load_and_run([0xd0, 0x03, 0x00])
                                # branch + pc + (len(prog) - 1)
    assert cpu.program_counter ==  0x03 + 0x8000 + 0x02

def test_0x10_bpl():
    cpu = CPU()

    # BPL $03
    # BRK
    cpu.load_and_run([0x10, 0x03, 0x00])
                                # branch + pc + (len(prog) - 1)
    assert cpu.program_counter ==  0x03 + 0x8000 + 0x02

def test_0x30_bmi():
    cpu = CPU()

    # BMI $03
    # BRK
    cpu.load_and_run([0x30, 0x03, 0x00], **dict(status=[Flags.NEGATIVE]))
                                # branch + pc + (len(prog) - 1)
    assert cpu.program_counter ==  0x03 + 0x8000 + 0x02

def test_0x50_bvc():
    cpu = CPU()

    # BVC $03
    # BRK
    cpu.load_and_run([0x50, 0x03, 0x00])
                                # branch + pc + (len(prog) - 1)
    assert cpu.program_counter ==  0x03 + 0x8000 + 0x02

def test_0x70_bvs():
    cpu = CPU()

    # BVS $03
    # BRK
    cpu.load_and_run([0x70, 0x03, 0x00], **dict(status=[Flags.OVERFLOW]))
                                # branch + pc + (len(prog) - 1)
    assert cpu.program_counter ==  0x03 + 0x8000 + 0x02


def test_0xc9_cmp_immediate():
    cpu = CPU()

    # LDA #$05
    # CMP #$05
    # BRK
    cpu.load_and_run([0xa9, 0x05, 0xc9, 0x05, 0x00])
    assert cpu.get_flag(Flags.ZERO)

def test_0xc5_cmp_zero_page():
    cpu = CPU()
    cpu.mem_write(0x10, 0x05)

    # LDA $05
    # CMP $10
    # BRK
    cpu.load_and_run([0xa9, 0x05, 0xc5, 0x10, 0x00])
    assert cpu.get_flag(Flags.ZERO)

def test_0xd5_cmp_zero_page_x():
    cpu = CPU()
    cpu.mem_write(0x20, 0x05)

    # LDA $05
    # CMP $20,X
    # BRK
    cpu.load_and_run([0xa9, 0x05, 0xd5, 0x10, 0x00], **{"register_x": 0x10})
    assert cpu.get_flag(Flags.ZERO)

def test_0xcd_cmp_absolute():
    cpu = CPU()
    cpu.mem_write_u16(0x10, 0x05)

    # LDA $05
    # CMP $10
    # BRK
    cpu.load_and_run([0xa9, 0x05, 0xcd, 0x10, 0x00])
    assert cpu.get_flag(Flags.ZERO)

def test_0xdd_cmp_absolute_x():
    cpu = CPU()
    cpu.mem_write_u16(0x10, 0x05)

    # LDA $05
    # CMP $10,X
    # BRK
    cpu.load_and_run([0xa9, 0x05, 0xdd, 0x00], **{"register_x": 0x10})
    assert cpu.get_flag(Flags.ZERO)

def test_0xd9_cmp_absolute_y():
    cpu = CPU()
    cpu.mem_write_u16(0x10, 0x05)

    # LDA $05
    # CMP $10,Y
    # BRK
    cpu.load_and_run([0xa9, 0x05, 0xd9, 0x00], **{"register_y": 0x10})
    assert cpu.get_flag(Flags.ZERO)

def test_0xc1_cmp_indirect_x():
    cpu = CPU()
    cpu.mem_write(0x20, 0x20)
    cpu.mem_write(0x21, 0x30)
    cpu.mem_write(0x3020, 0x05)

    # LDA $05
    # CMP ($20,X)
    # BRK
    cpu.load_and_run([0xa9, 0x05, 0xc1, 0x10], **{"register_x": 0x10})
    assert cpu.get_flag(Flags.ZERO)

def test_0xd1_cmp_indirect_y():
    cpu = CPU()
    cpu.mem_write(0x10, 0x20)
    cpu.mem_write(0x11, 0x30)
    cpu.mem_write(0x3021, 0x05)

    # LDA $05
    # CMP ($10),Y
    # BRK
    cpu.load_and_run([0xa9, 0x05, 0xd1, 0x10], **{"register_y": 0x01})
    assert cpu.get_flag(Flags.ZERO)

def test_0xe0_cpx_immediate():
    cpu = CPU()

    # LDX #$05
    # CPX #$05
    # BRK
    cpu.load_and_run([0xa2, 0x05, 0xe0, 0x05, 0x00])
    assert cpu.get_flag(Flags.ZERO)

def test_0xe4_cpx_zero_page():
    cpu = CPU()
    cpu.mem_write(0x10, 0x05)

    # LDX $05
    # CPX $10
    # BRK
    cpu.load_and_run([0xa2, 0x05, 0xe4, 0x10, 0x00])
    assert cpu.get_flag(Flags.ZERO)

def test_0xec_cpx_absolute():
    cpu = CPU()
    cpu.mem_write_u16(0x10, 0x05)

    # LDX $05
    # CPX $10
    # BRK
    cpu.load_and_run([0xa2, 0x05, 0xec, 0x10, 0x00])
    assert cpu.get_flag(Flags.ZERO)

def test_0x45_eor_zero_page():
    cpu = CPU()
    cpu.mem_write(0x10, 0b00000001)

    # LDA $05
    # EOR $10
    # BRK
    cpu.load_and_run([0xa9, 0b0001001, 0x45, 0x10, 0x00])
    assert cpu.register_a == 0b00001000

def test_0x46_lsr_zero_page():
    cpu = CPU()
    cpu.mem_write(0x10, 0b00000010)

    # LSR $10
    # BRK
    cpu.load_and_run([0x46, 0x10, 0x00])
    assert cpu.mem_read(0x10) == 0b00000001