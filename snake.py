# import sdl2.ext as sdl2ext
import logging
import random
import threading
import time
from typing import Callable, List, Optional, Tuple
import numpy as np
import pygame
import pygame.surfarray as surfarray
from cpu import CPU
from logger import get_logger
from memory import Memory
from pynput.keyboard import Key, Listener


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()

    return wrapper


class SnakeGame:
    # fmt: off
    CODE: List[int] = [
      # 1536  1537  1538  1539  1540  1541  1542  1543  1544  1545  1546  1547  1548  1549  1550  1551
        0x20, 0x06, 0x06, 0x20, 0x38, 0x06, 0x20, 0x0d, 0x06, 0x20, 0x2a, 0x06, 0x60, 0xa9, 0x02, 0x85,
        0x02, 0xa9, 0x04, 0x85, 0x03, 0xa9, 0x11, 0x85, 0x10, 0xa9, 0x10, 0x85, 0x12, 0xa9, 0x0f, 0x85,
        0x14, 0xa9, 0x04, 0x85, 0x11, 0x85, 0x13, 0x85, 0x15, 0x60, 0xa5, 0xfe, 0x85, 0x00, 0xa5, 0xfe,
        0x29, 0x03, 0x18, 0x69, 0x02, 0x85, 0x01, 0x60, 0x20, 0x4d, 0x06, 0x20, 0x8d, 0x06, 0x20, 0xc3,
        0x06, 0x20, 0x19, 0x07, 0x20, 0x20, 0x07, 0x20, 0x2d, 0x07, 0x4c, 0x38, 0x06, 0xa5, 0xff, 0xc9,
        0x77, 0xf0, 0x0d, 0xc9, 0x64, 0xf0, 0x14, 0xc9, 0x73, 0xf0, 0x1b, 0xc9, 0x61, 0xf0, 0x22, 0x60,
        0xa9, 0x04, 0x24, 0x02, 0xd0, 0x26, 0xa9, 0x01, 0x85, 0x02, 0x60, 0xa9, 0x08, 0x24, 0x02, 0xd0,
        0x1b, 0xa9, 0x02, 0x85, 0x02, 0x60, 0xa9, 0x01, 0x24, 0x02, 0xd0, 0x10, 0xa9, 0x04, 0x85, 0x02,
        0x60, 0xa9, 0x02, 0x24, 0x02, 0xd0, 0x05, 0xa9, 0x08, 0x85, 0x02, 0x60, 0x60, 0x20, 0x94, 0x06,
        0x20, 0xa8, 0x06, 0x60, 0xa5, 0x00, 0xc5, 0x10, 0xd0, 0x0d, 0xa5, 0x01, 0xc5, 0x11, 0xd0, 0x07,
        0xe6, 0x03, 0xe6, 0x03, 0x20, 0x2a, 0x06, 0x60, 0xa2, 0x02, 0xb5, 0x10, 0xc5, 0x10, 0xd0, 0x06,
        0xb5, 0x11, 0xc5, 0x11, 0xf0, 0x09, 0xe8, 0xe8, 0xe4, 0x03, 0xf0, 0x06, 0x4c, 0xaa, 0x06, 0x4c,
        0x35, 0x07, 0x60, 0xa6, 0x03, 0xca, 0x8a, 0xb5, 0x10, 0x95, 0x12, 0xca, 0x10, 0xf9, 0xa5, 0x02,
        0x4a, 0xb0, 0x09, 0x4a, 0xb0, 0x19, 0x4a, 0xb0, 0x1f, 0x4a, 0xb0, 0x2f, 0xa5, 0x10, 0x38, 0xe9,
        0x20, 0x85, 0x10, 0x90, 0x01, 0x60, 0xc6, 0x11, 0xa9, 0x01, 0xc5, 0x11, 0xf0, 0x28, 0x60, 0xe6,
        0x10, 0xa9, 0x1f, 0x24, 0x10, 0xf0, 0x1f, 0x60, 0xa5, 0x10, 0x18, 0x69, 0x20, 0x85, 0x10, 0xb0,
        0x01, 0x60, 0xe6, 0x11, 0xa9, 0x06, 0xc5, 0x11, 0xf0, 0x0c, 0x60, 0xc6, 0x10, 0xa5, 0x10, 0x29,
        0x1f, 0xc9, 0x1f, 0xf0, 0x01, 0x60, 0x4c, 0x35, 0x07, 0xa0, 0x00, 0xa5, 0xfe, 0x91, 0x00, 0x60,
        0xa6, 0x03, 0xa9, 0x00, 0x81, 0x10, 0xa2, 0x00, 0xa9, 0x01, 0x81, 0x10, 0x60, 0xa2, 0x00, 0xea,
        0xea, 0xca, 0xd0, 0xfb, 0x60
    ]
    # fmt: off

    memory: Memory
    cpu: CPU
    logger: logging.Logger

    def __init__(self, display: bool = True, keyboard: bool = True):
        self.display = display
        self.keyboard = keyboard

        self.logger = get_logger(__name__)
        self.memory = Memory()
        # self.memory.setup_snake()
        self.memory.load_program_rom(program_rom=self.CODE, program_rom_offset=0x0600)
        self.cpu = CPU(memory=self.memory, program_offset=0x0600)

        if self.display:
            self.init_display()

        if self.keyboard:
            # start read input thread
            self.read_input()

        self.last_key_pressed = None

        self.running = True
        while self.running:
            self.cpu.step()
            # read in user inputs and set the appropriate memory locations
            if self.last_key_pressed is not None and self.last_key_pressed != self.memory[0xFE]:
                self.memory[0xFE] = self.last_key_pressed

            self.memory[0xFF] = random.randint(0, 0xFF)

            if self.display:
                self.update_display()


        pygame.quit()

    def init_display(self):
        pygame.init()
        self.display = pygame.display.set_mode((320, 320))

    def update_display(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

        surf = pygame.surfarray.make_surface(self.get_memory_pixel_array())
        self.display.blit(surf, (0, 0))

        pygame.display.update()


    def get_memory_pixel_array(self):
        pixel_array = np.array(*[np.array_split(self.memory.memory[0x0200:0x0600], 32)]).astype(np.uint8)
        return pixel_array

    @threaded
    def read_input(self) -> Optional[int]:
        def on_press(key):
            self.logger.info(key)
            if key == Key.up:
                self.last_key_pressed = 0x77
            elif key == Key.down:
                self.last_key_pressed = 0x73
            elif key == Key.left:
                self.last_key_pressed = 0x61
            elif key == Key.right:
                self.last_key_pressed = 0x64

        with Listener(on_press=on_press) as listener:
            listener.join()


SnakeGame(display=False, keyboard=False)
