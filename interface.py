"""
interface.py --> Unified API
"""

from typing import List

# Stage 1 : Bytes <--> LZ77 tokens

from lz77.lz77_tokens import lz77Token
from lz77.lz77_encoder import lz77_encode
from lz77.lz77_decoder import lz77_decode


def bytes_to_tokens(data: bytes) -> list[lz77Token]:
    """Compress raw bytes into a list of LZ77 tokens (Literals and Matches)."""
    return lz77_encode(data)


def tokens_to_bytes(tokens: list[lz77Token]) -> bytearray:
    """Reconstruct the original bytes from a list of LZ77 tokens."""
    return lz77_decode(tokens)


# Stage 2 : LZ77 tokens <--> DEFLATE events

from symbol.deflate_events import LiteralEvent, MatchEvent, EndEvent, DEFLATEEvent
from symbol.symbol_converter import tokens__events, events__tokens


def tokens_to_events(tokens: list[lz77Token]) -> list[DEFLATEEvent]:
    """Convert LZ77 tokens into DEFLATE events (Literal, Match, and End)."""
    return tokens__events(tokens)


def events_to_tokens(events: list[DEFLATEEvent]) -> list[lz77Token]:
    """Convert DEFLATE events back into LZ77 tokens."""
    return events__tokens(events)


# Stage 3 : DEFLATE events <--> Huffman‑coded payload + header

from huffman.encoder import encode_with_huffman
from huffman.decoder import decode_with_huffman


def events_to_bits(events: list[DEFLATEEvent]) -> tuple[str, list[int], list[int]]:
    """
    Convert a list of DEFLATE events into:
      - a bit-string of the Huffman-coded payload
      - the literal/length code lengths
      - the distance code lengths
    """
    return encode_with_huffman(events)


def bits_to_events(
    payload_bits: str, lit_lengths: list[int], dist_lengths: list[int]
) -> list[DEFLATEEvent]:
    """
    Reconstruct DEFLATE events from a Huffman-coded bit-string and the
    two code-length tables.
    """
    return decode_with_huffman(payload_bits, lit_lengths, dist_lengths)


if __name__ == "__main__":
    # Comprehensive Round-Trip Test
    data = b"abcabcabcabc"

    # Forward
    t_list = bytes_to_tokens(data)
    e_list = tokens_to_events(t_list)
    bits, l_lens, d_lens = events_to_bits(e_list)
    print(len(l_lens), len(d_lens))

    # Backward
    e_recon = bits_to_events(bits, l_lens, d_lens)
    t_recon = events_to_tokens(e_recon)
    data_recon = tokens_to_bytes(t_recon)

    print(f"Original: {data}")
    print(f"Recovered: {data_recon}")
    assert data == data_recon, "Round-trip failed!"
    print("✅ Full compression pipeline verified!")
