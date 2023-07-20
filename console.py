import argparse
import asyncio
from pathlib import Path
from cartrige import Cartridge
from cpu import CPU
from memory import Memory
from pydantic import conbytes


class Console:
    def __init__(self, rom_path: Path) -> None:
        self.cartrige: Cartridge = Cartridge(rom_path=rom_path)
        self.memory: Memory = Memory()
        self.cpu: CPU = CPU(self.memory)

    def load_cartridge(self):
        self.memory.load_cartridge(self.cartrige)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-r",
        "--rom-path",
        type=str,
        help="The filepath of the rom being loaded into the cartridge",
    )

    event_loop = asyncio.new_event_loop()
    args = parser.parse_args()
    console = Console(**args.__dict__)
    console.load_cartridge()
    console.cpu.run()

    # if __name__ == "__main__":
#     app = StopwatchApp()
#     app.run()
