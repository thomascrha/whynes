import argparse
from cartrige import Cartridge
from cpu import CPU

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-r",
        "--rom-path",
        type=str,
        help="The filepath of the rom being loaded into the cartridge",
    )

    args = parser.parse_args()

    cart = Cartridge(**args.__dict__)
    cpu = CPU(cart).decompile_program()
