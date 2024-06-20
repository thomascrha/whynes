"""
Small game of snake implemented in 6502 assembly - https://gist.github.com/wkjagt/9043907

The game is implemented in 6502 assembly and runs on a virtual 6502 CPU implemented in Python.

By default the game will run in a pygame window, but you can also deassemble the code by passing the -d flag.
"""
import argparse
import datetime
import random
from typing import List, Tuple
import numpy as np
import pygame
from pynput.keyboard import Key, Listener
from cartridge import Cartridge
from constants import Flags
from cpu import CPU
from logger import get_logger
from memory import Memory

logger = get_logger(__name__)
WIDTH = 32
HEIGHT = 32
SCREEN_SIZE = (WIDTH, HEIGHT)
PIXEL_SIZE = 20
COLORS = {
    0: (0, 0, 0),  # Black
    1: (255, 255, 255),  # White
    2: (255, 0, 0),  # Red
    3: (0, 255, 0),  # Green
    4: (0, 0, 255),  # Blue
    5: (255, 255, 0),  # Yellow
    6: (255, 0, 255),  # Magenta
    7: (0, 255, 255),  # Cyan
}


class SnakeGame:
    # fmt: off
    CODE_: List[int] = [
        0x20, 0x06, 0x06,
        0x20, 0x38, 0x06,
        0x20, 0x0d, 0x06,
        0x20, 0x2a, 0x06,
        0x60,
        0xa9, 0x02,
        0x85, 0x02,
        0xa9, 0x04,
        0x85, 0x03,
        0xa9, 0x11,
        0x85, 0x10,
        0xa9, 0x10, 0x85, 0x12, 0xa9, 0x0f, 0x85,
        0x14, 0xa9, 0x04, 0x85, 0x11, 0x85, 0x13, 0x85, 0x15, 0x60, 0xa5, 0xfe, 0x85, 0x00, 0xa5, 0xfe,
        0x29, 0x03, 0x18, 0x69, 0x02, 0x85, 0x01, 0x60, 0x20, 0x4d, 0x06, 0x20, 0x8d, 0x06, 0x20, 0xc3,
        0x06, 0x20, 0x19, 0x07, 0x20, 0x20, 0x07, 0x20, 0x2d, 0x07, 0x4c, 0x38, 0x06, 0xa5, 0xff, 0xc9,
        0x77, 0xf0, 0x0d, 0xc9, 0x64, 0xf0, 0x14, 0xc9, 0x73, 0xf0, 0x1b, 0xc9, 0x61, 0xf0, 0x22, 0x60,
        0xa9, 0x04, 0x24, 0x02, 0xd0, 0x26, 0xa9, 0x01, 0x85, 0x02, 0x60, 0xa9, 0x08, 0x24, 0x02, 0xd0,
        0x1b, 0xa9, 0x02, 0x85, 0x02, 0x60, 0xa9, 0x01, 0x24, 0x02, 0xd0, 0x10, 0xa9, 0x04, 0x85, 0x02,
        0x60, 0xa9, 0x02, 0x24, 0x02, 0xd0, 0x05, 0xa9, 0x08, 0x85, 0x02, 0x60, 0x60, 0x20, 0x94, 0x06,
        0x20, 0xa8, 0x06, 0x60,
        0xa5, 0x00, # LDA
        0xc5, 0x10, # CMP
        0xd0, 0x0d, # BNE +13
        0xa5, 0x01, # LDA
        0xc5, 0x11, # CMP
        0xd0, 0x07, # BNE
        0xe6, 0x03, # INC
        0xe6, 0x03, # INC
        0x20, 0x2a, 0x06, # JSR
        0x60, # RTS


        0xa2, 0x02,
        0xb5, 0x10, 0xc5, 0x10, 0xd0, 0x06,
        0xb5, 0x11, 0xc5, 0x11, 0xf0, 0x09, 0xe8, 0xe8, 0xe4, 0x03, 0xf0, 0x06, 0x4c, 0xaa, 0x06, 0x4c,
        0x35, 0x07, 0x60, 0xa6, 0x03, 0xca, 0x8a, 0xb5, 0x10, 0x95, 0x12, 0xca,

        0x10, 0xf9, # BPL -7


        0xa5, 0x02,
        0x4a, 0xb0, 0x09, 0x4a, 0xb0, 0x19, 0x4a, 0xb0, 0x1f, 0x4a, 0xb0, 0x2f, 0xa5, 0x10, 0x38, 0xe9,
        0x20, 0x85, 0x10, 0x90, 0x01, 0x60, 0xc6, 0x11, 0xa9, 0x01, 0xc5, 0x11, 0xf0, 0x28, 0x60, 0xe6,
        0x10, 0xa9, 0x1f, 0x24, 0x10, 0xf0, 0x1f, 0x60, 0xa5, 0x10, 0x18, 0x69, 0x20, 0x85, 0x10, 0xb0,
        0x01, 0x60, 0xe6, 0x11, 0xa9, 0x06, 0xc5, 0x11, 0xf0, 0x0c, 0x60, 0xc6, 0x10, 0xa5, 0x10, 0x29,
        0x1f, 0xc9, 0x1f, 0xf0, 0x01, 0x60, 0x4c, 0x35, 0x07, 0xa0, 0x00, 0xa5, 0xfe, 0x91, 0x00, 0x60,
        0xa6, 0x03, 0xa9, 0x00, 0x81, 0x10, 0xa2, 0x00, 0xa9, 0x01, 0x81, 0x10, 0x60, 0xa2, 0x00, 0xea,
        0xea, 0xca, 0xd0, 0xfb, 0x60, 0x00
    ]
    # fmt: off

    cpu: CPU

    def __init__(self, rom_path: None | str = None) -> None:
        self.rom_path = rom_path

        self.cartridge = None
        program_offset=0x0600
        if self.rom_path is not None:
            self.cartridge = Cartridge(rom_path=self.rom_path)
            program_offset=0x8600

        self.memory = Memory(rom=self.cartridge)
        self.cpu = CPU(self.memory, callback=self.callback, program_offset=program_offset)
        self.last_key_pressed = None
        self.previous_screen = None
        self.exit = False

        self.callback_times: list[datetime.datetime] = []

    @property
    def CODE(self) -> List[int]:
        if self.rom_path is None:
            return self.CODE_

        if self.cartridge is None:
            raise ValueError("No ROM loaded")

        return self.cartridge.program_rom

    def run(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH*PIXEL_SIZE, HEIGHT*PIXEL_SIZE))

        key_listener = self.read_input_listener()
        key_listener.start()

        escape_listener = self.escape_listener()
        escape_listener.start()

        if not self.rom_path:

            self.cpu.load_and_run(self.CODE)
        else:
            self.cpu.reset()
            self.cpu.run

        key_listener.join()
        pygame.quit()

    def deassemble(self):
        if not self.rom_path:
            return self.cpu.load_and_deassemble(self.CODE)

        self.cpu.reset()
        return self.cpu.deassemble()

    def colour(self, byte: int) -> Tuple[int, int, int]:
        match byte:
            case 0:
                return (0, 0, 0) # Black
            case 1:
                return (255, 255, 255) # White
            case 2, 9:
                return (128, 128, 128) # Gray
            case 3, 10:
                return (255, 0, 0) # Red
            case 4, 11:
                return (0, 255, 0) # Green
            case 5, 12:
                return (0, 0, 255) # Blue
            case 6, 13:
                return (255, 0, 255) # Magenta
            case 7, 14:
                return (255, 255, 0) # Yellow
            case _:
                return (0, 255, 255) # Cyan

    def read_input_listener(self):
        def on_press(key):
            logger.debug(key)
            if key == Key.up:
                self.last_key_pressed = 0x77
            elif key == Key.down:
                self.last_key_pressed = 0x73
            elif key == Key.left:
                self.last_key_pressed = 0x61
            elif key == Key.right:
                self.last_key_pressed = 0x64

        listener = Listener(on_press=on_press, supress=True)
        return listener

    def escape_listener(self):
        def on_press(key):
            if key == Key.esc:
                self.exit = True

        listener = Listener(on_press=on_press, supress=True)
        return listener

    def redraw(self, surface: pygame.Surface) -> None:
        # Scale the surface up
        surface = pygame.transform.scale(surface, (WIDTH * PIXEL_SIZE, HEIGHT * PIXEL_SIZE))

        self.screen.blit(surface, (0, 0))
        pygame.display.update()

    def callback(self) -> None:
        if self.exit:
            logger.info("Exiting...")
            exit(0)

        logger.debug(f"Opcode: {getattr(self.cpu.opcode, 'mnemonic', None)} PC: {self.cpu.program_counter}, A: {self.cpu.register_a}, X: {self.cpu.register_x}, Y: {self.cpu.register_y}, SP: {self.cpu.stack_pointer}, Status: {Flags(int(self.cpu.status))}")

        self.callback_times.append(datetime.datetime.now())

        # read user input and write it to mem[0xFF]
        if self.last_key_pressed:
            self.cpu.memory.write(0xff, self.last_key_pressed)
            self.last_key_pressed = None

        # update mem[0xFE] with new Random Number
        self.cpu.memory.write(0xfe, random.randint(1, 16))
        # read mem mapped screen state

        self.current_screen = self.cpu.memory.slice(0x0200, 0x0600)
        if self.previous_screen is None or not np.array_equal(self.current_screen, self.previous_screen):
            self.previous_screen = self.current_screen
            # Create a new surface
            surface = pygame.Surface((WIDTH, HEIGHT))

            # Create a pixel array from the surface
            pixels = pygame.PixelArray(surface)

            for i, colour in enumerate(self.cpu.memory.slice(0x0200, 0x0600)):
                x = i % WIDTH
                y = i // WIDTH
                pixels[x, y] = self.colour(colour)

            # Delete the pixel array to make the surface usable again
            del pixels

            self.redraw(surface)

        # generate random number between 1-16 and store in memory location 0xfe
        self.cpu.memory.write(0xfe, random.randint(1, 16))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("-d", "--deassemble", action="store_true", help="Deassemble the code")
    parser.add_argument("-r", "--rom-path", type=str, help="The filepath of the rom being loaded into the cartridge")

    args = parser.parse_args()

    try:
        if args.deassemble:
            if args.rom_path:
                SnakeGame(args.rom_path).deassemble()
                exit(0)
            SnakeGame().deassemble()
            exit(0)

        if args.rom_path:
            SnakeGame(args.rom_path).run()
            exit(0)

        SnakeGame().run()
    except KeyboardInterrupt:
        print("Exiting...")
        exit(0)
