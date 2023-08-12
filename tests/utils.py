from typing import Dict, List
from cpu import Flag


def get_memory_map(changed_values: Dict[int, int] = {}, memory_end: int = 0xFFF) -> List[int]:
    memory = [0] * memory_end
    for address, value in changed_values.items():
        memory[address] = value

    return memory


DEFAULT_FLAG = Flag.INTERRUPT_DISABLE | Flag.UNUSED
DEFAULT_STATE = {"A": 0, "PC": 0x0FFF, "X": 0, "Y": 0, "S": DEFAULT_FLAG, "SP": 255, "MEMORY": get_memory_map()}
