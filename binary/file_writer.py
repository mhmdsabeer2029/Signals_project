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
        raise ValueError(f"Invalid Huffman code length: {M}. Maximum allowed is 15 bits.")

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


def file_writer(file_name: str, data: bytes, overwrite: bool = False) -> dict:
    """write the compressed file in .sdfl format from raw binary data.

    Args:
        file_name (str): the name of the output file without the .sdfl extension.
        data (bytes): the raw bytes we want to compress.
        overwrite (bool, optional): handling file already exists.
    Returns:
        dict: a dictionary containing debug information and offsets:
            - length_offset_bytes (int): byte offset to the start of the literal/length table.
            - length_offset_bits (int): bit offset within the byte to the start of the literal/length table.
            - distance_offset_bytes (int): byte offset to the start of the distance table.
            - distance_offset_bits (int): bit offset within the byte to the start of the distance table.
            - payload_offset_bytes (int): byte offset to the start of the payload bits.
            - payload_offset_bits (int): bit offset within the byte to the start of the payload bits.
            - LIT_BW (int): bit width used for each entry in the literal/length table.
            - DIST_BW (int): bit width used for each entry in the distance table.
            - length_table (list[int]): the code lengths for the literal/length Huffman tree.
            - distance_table (list[int]): the code lengths for the distance Huffman tree.
    """

    tokens = bytes_to_tokens(data)
    events = tokens_to_events(tokens)
    payload_bits, length_table, distance_table = events_to_bits(events)

    max_len = max(length_table)
    max_dist = max(distance_table)

    # calculate M from max(table) then calculate the correct bit-width
    LIT_BW = _bw_calculator(max_len)
    DIST_BW = _bw_calculator(max_dist)

    # I implemented returning this debug info to make it easier to know what
    # does the encoder think every thing is so that we can compare it to what
    # the decoder think it's and know how to read the hexdump output.
    debug = {}
    length_offset_bytes, length_offset_bits = divmod(8, 8)
    distance_offset_bytes, distance_offset_bits = divmod(8 + 286 * LIT_BW, 8)
    payload_offset_bytes, payload_offset_bits = divmod(
        8 + 286 * LIT_BW + 30 * DIST_BW, 8
    )

    debug["length_offset_bytes"] = length_offset_bytes
    debug["length_offset_bits"] = length_offset_bits
    debug["distance_offset_bytes"] = distance_offset_bytes
    debug["distance_offset_bits"] = distance_offset_bits
    debug["payload_offset_bytes"] = payload_offset_bytes
    debug["payload_offset_bits"] = payload_offset_bits
    debug["LIT_BW"] = LIT_BW
    debug["DIST_BW"] = DIST_BW
    debug["length_table"] = length_table
    debug["distance_table"] = distance_table

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

    return debug


def print_debug_info(debug: dict) -> None:
    """print the compression debug information in a beautiful and structured way.

    Args:
        debug (dict): The debug dictionary returned by file_writer.
    """
    width = 60
    label_w = 30
    header = "SDFL COMPRESSION DEBUG INFO"

    print(f"\n{'=' * width}")
    print(f"{header:^{width}}")
    print(f"{'=' * width}")

    # Section: Metadata
    print(f"{'Metadata':^{width}}")
    print(f"{'-' * width}")
    print(f"{'Literal Bit-Width (LIT_BW):':<{label_w}} {debug['LIT_BW']:>2} bits")
    print(f"{'Distance Bit-Width (DIST_BW):':<{label_w}} {debug['DIST_BW']:>2} bits")

    # Section: Offsets
    print(f"\n{'Offsets (Calculated)':^{width}}")
    print(f"{'-' * width}")

    # Format offsets: right-aligned bytes, zero-padded hex (min 2 digits), right-aligned bits
    def fmt_offset(b, bits):
        return f"{b:>5} Byte (0x{b:02X}), {bits:>1} bits"

    print(
        f"{'Length Table Start:':<{label_w}} {fmt_offset(debug['length_offset_bytes'], debug['length_offset_bits'])}"
    )
    print(
        f"{'Distance Table Start:':<{label_w}} {fmt_offset(debug['distance_offset_bytes'], debug['distance_offset_bits'])}"
    )
    print(
        f"{'Payload Start:':<{label_w}} {fmt_offset(debug['payload_offset_bytes'], debug['payload_offset_bits'])}"
    )

    # Section: Table Summaries
    print(f"\n{'Huffman Table Summaries':^{width}}")
    print(f"{'-' * width}")
    lt = debug["length_table"]
    dt = debug["distance_table"]

    non_zero_lt = [v for v in lt if v > 0]
    non_zero_dt = [v for v in dt if v > 0]

    print(f"Literal/Length Table:")
    print(f"  {'Total Symbols:':<{label_w - 2}} {len(lt):>3}")
    print(f"  {'Active Symbols:':<{label_w - 2}} {len(non_zero_lt):>3}")
    print(f"  {'Max Code Length:':<{label_w - 2}} {max(lt) if lt else 0:>3}")

    print(f"\nDistance Table:")
    print(f"  {'Total Symbols:':<{label_w - 2}} {len(dt):>3}")
    print(f"  {'Active Symbols:':<{label_w - 2}} {len(non_zero_dt):>3}")
    print(f"  {'Max Code Length:':<{label_w - 2}} {max(dt) if dt else 0:>3}")

    print(f"{'=' * width}\n")
