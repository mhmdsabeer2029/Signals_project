"""This module reads the header of a .sdfl compressed file."""

from binary.BitReader import BitReader


def extract_metadata(reader: BitReader) -> dict:
    """Read the header fields from an open BitReader and return their contents.

    The caller is responsible for opening and closing the BitReader.
    After this function returns, the reader is positioned at the first
    bit of the payload, ready for the decoder to continue.

    The header layout is defined by the spec as:
        LIT_BW     : 4 bits             — bit-width of each literal/length code length entry
        DIST_BW    : 4 bits             — bit-width of each distance code length entry
        LIT_TABLE  : 286 * LIT_BW bits  — code lengths for symbols 0-285
        DIST_TABLE :  30 * DIST_BW bits — code lengths for symbols 0-29

    If LIT_BW or DIST_BW is 0, the corresponding table is all zeros
    (no symbols of that type were used).

    Args:
        reader:
            An open BitReader positioned at the start of the file.

    Returns:
        A dict with keys:
            "LIT_BW"     : int
            "DIST_BW"    : int
            "LIT_TABLE"  : list[int] of length 286
            "DIST_TABLE" : list[int] of length 30
    """

    output = {}

    output["LIT_BW"] = reader.read_bits(4)
    output["DIST_BW"] = reader.read_bits(4)

    # read 286 literal/length code lengths, each LIT_BW bits wide
    # if LIT_BW is 0 all entries remain 0 (read_bits(0) returns 0)
    output["LIT_TABLE"] = [reader.read_bits(output["LIT_BW"]) for _ in range(286)]

    # read 30 distance code lengths, each DIST_BW bits wide
    output["DIST_TABLE"] = [reader.read_bits(output["DIST_BW"]) for _ in range(30)]

    return output


if __name__ == "__main__":

    with BitReader("test.txt") as reader:
        metadata = extract_metadata(reader)
        # reader is now positioned at the payload, ready for decode_payload(reader, metadata)

    print(f'LIT_BW = {metadata["LIT_BW"]}')
    print(f'DIST_BW = {metadata["DIST_BW"]}')
    print(f'LIT_TABLE = {metadata["LIT_TABLE"]}')
    print(f'DIST_TABLE = {metadata["DIST_TABLE"]}')
