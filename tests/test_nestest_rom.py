from pathlib import Path
from typing import Dict, Optional
from cartridge import Cartridge
from cpu import CPU
from memory import Memory

CURRENT_PATH = Path(__file__).parent
ROM_PATH = Path("files/nestest.nes")


def parse_log_line(log_line: str) -> Dict[str, str]:
    return log_line.split(" ")


def test_nestest_rom(
    rom_file: Optional[Path] = Path(__file__).parent / Path("files/nestest.nes"),
    rom_file_log: Optional[Path] = Path(__file__).parent / Path("./files/nestest.log"),
):
    # cart = Cartridge(rom_path=rom_file)
    # memory = Memory()
    # cpu = CPU(memory)
    # memory.load_cartridge(cart)
    # with open(rom_file_log, "r") as f:
    #     log = parse_log_line(f.readline())
    #
    #     cpu.step()
    #     print(log)
    #     assert str(cpu) == log
    #
    #     cpu.step()
    pass
