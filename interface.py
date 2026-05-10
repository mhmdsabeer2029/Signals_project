"""
interface.py --> Unified API
"""

from typing import List

# Stage 1 : Bytes <--> LZ77 tokens

from lz77.lz77_tokens import lz77Token
from lz77.lz77_encoder import lz77_encode
from lz77.lz77_decoder import lz77_decode


def bytes_to_tokens(data: bytes):
    """Compress raw bytes into a list of LZ77 tokens (Literals and Matches)."""
    return lz77_encode(data)

tokens = bytes_to_tokens(b"abcabcabcabc")
print(tokens)

def tokens_to_bytes(tokens):
    """Reconstruct the original bytes from a list of LZ77 tokens."""
    return lz77_decode(tokens)

# print([byte for byte in tokens_to_bytes(tokens)])

# Stage 2 : LZ77 tokens <--> DEFLATE events

from symbol.symbol_converter import events__tokens, tokens__events
from symbol.deflate_events import LiteralEvent, MatchEvent, EndEvent, DEFLATEEvent


def token__event(tokens: List[lz77Token]) -> List[DEFLATEEvent]:
    return tokens__events(tokens)

print(token__event(tokens))

def event__token(events: List[DEFLATEEvent]) -> List[lz77Token]:
    return events__tokens(events)


# Stage 3 : DEFLATE events <--> Huffman‑coded payload + header
from huffman.encoder import encode_with_huffman
from huffman.decoder import decode_with_huffman


def events_to_bits(events):
    """
    Convert a list of DEFLATE events into:
      - a bit-string of the Huffman-coded payload
      - the literal/length code lengths
      - the distance code lengths
    """
    return encode_with_huffman(
        events
    )  # ---------> (payload_bits, lit_lengths, dist_lengths)


def bits_to_events(payload_bits, lit_lengths, dist_lengths):
    """
    Reconstruct DEFLATE events from a Huffman-coded bit-string and the
    two code-length tables.
    """
    return decode_with_huffman(payload_bits, lit_lengths, dist_lengths)
