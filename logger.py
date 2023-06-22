import functools
import logging
import os
from os.path import join
from copy import copy



class ColoredFormatter(logging.Formatter):
    """
    Colored log formatter. Depending on level the message will be colored with the correct escape sequences.
    """

    MAPPING = {
        "DEBUG": 34,  # blue
        "INFO": 32,  # cyan
        "WARNING": 33,  # yellow
        "ERROR": 31,  # red
        "SYSTEM": 33,  # yellow
        "CRITICAL": 41,  # white on red bg
    }

    PREFIX = "\033["
    SUFFIX = "\033[0m"

    def __init__(self, fmt=None, datefmt=None):
        logging.Formatter.__init__(self, fmt=fmt, datefmt=datefmt)

    def format(self, record):
        colored_record = copy(record)
        levelname = colored_record.levelname
        message = colored_record.msg

        seq = self.MAPPING.get(levelname, 37)  # default white
        seq = self.MAPPING.get(levelname, 37)  # default white
        colored_message = ("{0}{1}m{2}{3}").format(
            self.PREFIX, seq, message, self.SUFFIX
        )
        colored_levelname = ("{0}{1}m{2}{3}").format(
            self.PREFIX, seq, levelname, self.SUFFIX
        )

        colored_record.levelname = colored_levelname
        colored_record.msg = colored_message
        return logging.Formatter.format(self, colored_record)


@functools.lru_cache
def get_logger(name: str) -> logging.Logger:

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.DEBUG)

    logger.addHandler(consoleHandler)

    formatter = ColoredFormatter(
        fmt="%(asctime)s.%(msecs)03d | %(name)s {%(filename)s:%(lineno)d} | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    consoleHandler.setFormatter(formatter)

    return logger
