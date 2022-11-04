import argparse
from pydantic import FilePath


class Cartridge:

    def __init__(self, rom: FilePath):
        self.rom = rom
        print(self.rom)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-r", "--rom", type=str, help="The filepath of the rom being loaded into the cartridge")

    args = parser.parse_args()

    cart = Cartridge(**args.__dict__)
