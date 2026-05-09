"""this module handles writing the header of the compressed file."""

from math import floor, log2
from BitWriter import BitWriter


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


def header_writer(
    file_name: str,
    length_table: list[int],
    distance_table: list[int],
    overwrite: bool = False,
) -> None:
    # I will not write a docstring for now because I will still add more functionality
    if len(length_table) != 286 or len(distance_table) != 30:
        raise ValueError("The length of the table(s) don't match the specification")

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

        # this is a temporary marker at the end of the file for testing
        # purposes only and will be removed when I add the payload
        writer.write_bits("1111-1111")

        # payload writing should go here but I will wait until DEFLATE and
        # Huffman are implemented to put the code for it


if __name__ == "__main__":
    from random import randint

    length_table = [randint(0, 15) for _ in range(286)]
    distance_table = [randint(0, 10) for _ in range(30)]
    distance_offset_bytes, distance_offset_bits = divmod(
        4 + 4 + 286 * _bw_calculator(max(length_table)), 8
    )
    payload_offset_bytes, payload_offset_bits = divmod(
        4
        + 4
        + 286 * _bw_calculator(max(length_table))
        + 30 * _bw_calculator(max(distance_table)),
        8,
    )

    print(
        f"LIT_BW = {_bw_calculator(max(length_table))} \n"
        f"DIST_BW = {_bw_calculator(max(distance_table))} \n"
        f"length_table[0:5] {length_table[0:5]} \n"
        f"length_table[281:286] {length_table[281:286]} \n"
        f"distance_offset = {hex(distance_offset_bytes)} bytes + {distance_offset_bits} bits \n"
        f"distance_table[0:5] {distance_table[0:5]} \n"
        f"distance_table[25:30] {distance_table[25:30]} \n"
        f"payload_offset = {hex(payload_offset_bytes)} bytes + {payload_offset_bits} bits"
    )

    header_writer("test.txt", length_table, distance_table, overwrite=True)
