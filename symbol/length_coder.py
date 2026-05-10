"""
Encodes / decodes match lengths using the DEFLATE length symbol table.
"""


class LengthCoder:
    # Look‑up tables (shared by all instances – class attributes)
    _base = [
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        13,
        15,
        17,
        19,
        23,
        27,
        31,
        35,
        43,
        51,
        59,
        67,
        83,
        99,
        115,
        131,
        163,
        195,
        227,
        258,
    ]
    _extra = [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        2,
        2,
        2,
        2,
        3,
        3,
        3,
        3,
        4,
        4,
        4,
        4,
        5,
        5,
        5,
        5,
        0,
    ]

    def encode(self, length: int) -> tuple[int, str]:
        """
        Convert an actual match length (3-258) into (length_symbol, extra_bits).
        length_symbol is 257-285, extra_bits is a string of '0'/'1'.
        """
        for i, base in enumerate(self._base):
            extra_count = self._extra[i]
            if extra_count == 0:
                if length == base:
                    return (257 + i, "")
            else:
                max_val = base + (1 << extra_count) - 1
                if base <= length <= max_val:
                    extra_value = length - base
                    extra_bits = format(extra_value, f"0{extra_count}b")
                    return (257 + i, extra_bits)
        raise ValueError(f"Invalid match length: {length}")

    def decode(self, symbol: int, extra_bits: str) -> int:
        """
        Convert (length_symbol, extra_bits) back to the actual length.
        """
        index = symbol - 257
        base = self._base[index]
        if extra_bits:
            return base + int(extra_bits, 2)
        return base
