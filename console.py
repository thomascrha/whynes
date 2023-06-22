import argparse
from pathlib import Path
from cartrige import Cartridge
from cpu import CPU
from memory import Memory


class Console:
    def __init__(self, rom_path: Path) -> None:
        self.cartrige: Cartridge = Cartridge(rom_path=rom_path)
        self.memory: Memory = Memory()
        self.cpu: CPU = CPU(self.memory)

    def load_cartridge(self):
        self.memory.setup(self.cartrige)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-r",
        "--rom-path",
        type=str,
        help="The filepath of the rom being loaded into the cartridge",
    )

    args = parser.parse_args()
    console = Console(**args.__dict__)
    console.load_cartridge()
    console.cpu.decompile_program()
