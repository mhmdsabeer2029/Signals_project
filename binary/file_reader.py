from interface import tokens_to_bytes, events_to_tokens, bits_to_events
from binary.BitReader import BitReader


def file_reader(reader: BitReader, metadata: dict) -> bytearray:
    """read the payload and decompress it.

    Args:
        reader (BitReader): the reader that was used in reading the metadata
        and it will be used here again.
        metadata (dict): the output of the extract_metadata function.

    Returns:
        bytearray: the decompressed raw bytes.
    """

    # the decoder will stop when it finds EndEvent
    events = bits_to_events(
        reader.read_rest(), metadata["LIT_TABLE"], metadata["DIST_TABLE"]
    )
    tokens = events_to_tokens(events)
    return tokens_to_bytes(tokens)
