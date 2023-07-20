from typing import List


def get_bytes_ordered(bytes_: List[bytes]) -> bytes:
    print(f"len {len(bytes_)}")
    if len(bytes_) == 1:
        return bytes_[0]
    elif len(bytes_) == 2:
        a = bytes_[0]
        b = bytes_[1]
        b = b << 8
        print(f"a {a}")
        print(f"b {b}")
        print(f"b | a {b | a}")
        return b | a
    else:
        # no command should have more than 2 bytes for a 6502 processor
        raise ValueError("Unsupported number of bytes")
