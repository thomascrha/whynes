import argparse
from pathlib import Path
from cartridge import Cartridge
from cpu import CPU
from logger import get_logger

logger = get_logger(__name__)


class Console:
    cartrige: Cartridge
    cpu: CPU

    def __init__(self, rom_path: Path) -> None:
        self.cartrige = Cartridge(rom_path=rom_path)
        self.cpu = CPU()


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
