"""
Huffman decoder: reads a bit string and reconstructs DEFLATE events.
"""

from typing import List, Dict, Tuple, Optional
from symbol.deflate_events import LiteralEvent, MatchEvent, EndEvent, DEFLATEEvent
from .canonical_codes import build_canonical_codes
from .deflate_constants import LENGTH_EXTRA, DISTANCE_EXTRA


class HuffmanDecoder:
    """Decodes a canonical Huffman‑coded stream."""

    def __init__(self, lengths: List[int]):
        self.lengths = lengths
        self.decode_table: Dict[str, int] = self._build_decode_table()

    def _build_decode_table(self) -> Dict[str, int]:
        """Create a reverse mapping: bitstring → symbol."""
        codes = build_canonical_codes(self.lengths)
        return {code: symbol for symbol, code in codes.items()}

    def decode_symbol(self, bits: str, start: int) -> Tuple[int, int]:
        """
        Read one Huffman symbol from 'bits' starting at 'start'.
        Returns (symbol, number of bits consumed).
        """
        max_len = min(16, len(bits) - start)
        for length in range(1, max_len + 1):
            if start + length > len(bits):
                break
            code = bits[start:start + length]
            if code in self.decode_table:
                return self.decode_table[code], length
        raise ValueError(f"Invalid Huffman code at position {start}")


def decode_with_huffman(
    payload_bits: str,
    lit_lengths: List[int],
    dist_lengths: List[int]
) -> List[DEFLATEEvent]:
    """
    Decode a Huffman‑coded bit string back into DEFLATE events.
    """
    lit_decoder = HuffmanDecoder(lit_lengths)
    dist_decoder = HuffmanDecoder(dist_lengths)

    events: List[DEFLATEEvent] = []
    pos = 0

    while pos < len(payload_bits):
        # 1. Decode literal/length symbol
        symbol, consumed = lit_decoder.decode_symbol(payload_bits, pos)
        pos += consumed

        # 2. Interpret symbol
        if 0 <= symbol <= 255:
            events.append(LiteralEvent(symbol))

        elif symbol == 256:
            events.append(EndEvent())
            break

        elif 257 <= symbol <= 285:
            # Match: read length extra bits
            index = symbol - 257
            len_extra_count = LENGTH_EXTRA[index]
            len_extra_bits = ""
            if len_extra_count > 0:
                len_extra_bits = payload_bits[pos:pos + len_extra_count]
                pos += len_extra_count

            # Decode distance symbol
            dist_symbol, consumed = dist_decoder.decode_symbol(payload_bits, pos)
            pos += consumed

            # Read distance extra bits
            dist_extra_count = DISTANCE_EXTRA[dist_symbol]
            dist_extra_bits = ""
            if dist_extra_count > 0:
                dist_extra_bits = payload_bits[pos:pos + dist_extra_count]
                pos += dist_extra_count

            events.append(MatchEvent(
                symbol, len_extra_bits,
                dist_symbol, dist_extra_bits
            ))
        else:
            raise ValueError(f"Unknown literal/length symbol: {symbol}")

    return events