"""this module handles writing the compressed file."""

from math import floor, log2
from binary.BitWriter import BitWriter
from interface import bytes_to_tokens, tokens_to_events, events_to_bits


def _bw_calculator(M: int) -> int:
    """compute table bit width used in the file header.

    Args:
        M (int): the largest code length in a given table.

    Raises:
        TypeError: is raised if M isn't an integer.
        ValueError: is raised if the Value of M falls outside of [0, 15].

    Returns:
        int: the bit width used in length and distance tables stored at
        the header of the file.
    """

    if not isinstance(M, int):
        raise TypeError("M must be an integer")
    if M < 0 or M > 15:
        raise ValueError("M must fall in the range from 0 to 15 inclusive.")

    if M == 0:
        return 0

    return floor(log2(M)) + 1


def _pad(num: int, bits: int) -> str:
    """pad a given number in a number of bits and return it as a string.

    Args:
        num (int): the number we want to pad.
        bits (int): the number of bits we want to pad in.

    Raises:
        ValueError: if we want to pad a number in a less number of bits than it takes.

    Returns:
        str: the padded number as a string.
    """

    raw_binary = bin(num)[2:]
    length_raw_binary = len(raw_binary)
    if length_raw_binary > bits:
        raise ValueError(f"We can't pad {length_raw_binary} bits in {bits} bits.")

    return (bits - length_raw_binary) * "0" + raw_binary


def file_writer(file_name: str, data: bytes, overwrite: bool = False) -> None:
    """write the compressed file in .sdfl format from raw binary data.

    Args:
        file_name (str): the name of the output file without the .sdfl extension.
        data (bytes): the raw bytes we want to compress.
        overwrite (bool, optional): handling file already exists.
    """

    tokens = bytes_to_tokens(data)
    events = tokens_to_events(tokens)
    payload_bits, length_table, distance_table = events_to_bits(events)

    # calculate M from max(table) then calculate the correct bit-width
    LIT_BW = _bw_calculator(max(length_table))
    DIST_BW = _bw_calculator(max(distance_table))

    with BitWriter(file_name, overwrite=overwrite) as writer:
        # we get the 4 padding constant from the specification
        writer.write_bits(_pad(LIT_BW, 4))
        writer.write_bits(_pad(DIST_BW, 4))

        for length in length_table:
            writer.write_bits(_pad(length, LIT_BW))

        for distance in distance_table:
            if DIST_BW > 0:
                writer.write_bits(_pad(distance, DIST_BW))

        writer.write_bits(payload_bits)
