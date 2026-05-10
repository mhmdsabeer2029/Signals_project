"""
Convert code lengths into canonical Huffman codes.
"""

from typing import List, Dict


def build_canonical_codes(lengths: List[int]) -> Dict[int, str]:
    """
    Given a list of code lengths (index = symbol), returns
    a dictionary mapping symbol -> canonical bit string.
    """
    # Count how many symbols have each length (1..15)
    count = [0] * 16
    for length in lengths:
        if length > 0:
            count[length] += 1

    count[0] = 0

    # Compute the first code value for each length
    next_code = [0] * 16
    code = 0
    for bits in range(1, 16):
        code = (code + count[bits - 1]) << 1
        next_code[bits] = code

    # Assign codes in increasing symbol order
    symbol_codes = {}
    for symbol in range(len(lengths)):
        length = lengths[symbol]
        if length != 0:
            code_value = next_code[length]
            code_str = format(code_value, f"0{length}b")
            symbol_codes[symbol] = code_str
            next_code[length] += 1

    return symbol_codes
