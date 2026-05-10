"""
Encodes / decodes match distances using the DEFLATE distance symbol table.
"""


class DistanceCoder:
    _base = [
        1,
        2,
        3,
        4,
        5,
        7,
        9,
        13,
        17,
        25,
        33,
        49,
        65,
        97,
        129,
        193,
        257,
        385,
        513,
        769,
        1025,
        1537,
        2049,
        3073,
        4097,
        6145,
        8193,
        12289,
        16385,
        24577,
    ]
    _extra = [
        0,
        0,
        0,
        0,
        1,
        1,
        2,
        2,
        3,
        3,
        4,
        4,
        5,
        5,
        6,
        6,
        7,
        7,
        8,
        8,
        9,
        9,
        10,
        10,
        11,
        11,
        12,
        12,
        13,
        13,
    ]

    def encode(self, distance: int) -> tuple[int, str]:
        """
        Convert an actual distance (1-32768) into (distance_symbol, extra_bits).
        distance_symbol is 0-29, extra_bits is a string of '0'/'1'.
        """
        for i, base in enumerate(self._base):
            extra_count = self._extra[i]
            if extra_count == 0:
                if distance == base:
                    return (i, "")
            else:
                max_val = base + (1 << extra_count) - 1
                if base <= distance <= max_val:
                    extra_value = distance - base
                    extra_bits = format(extra_value, f"0{extra_count}b")
                    return (i, extra_bits)
        raise ValueError(f"Invalid match distance: {distance}")

    def decode(self, symbol: int, extra_bits: str) -> int:
        """
        Convert (distance_symbol, extra_bits) back to the actual distance.
        """
        base = self._base[symbol]
        if extra_bits:
            return base + int(extra_bits, 2)
        return base
