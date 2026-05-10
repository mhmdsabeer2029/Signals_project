"""
Encode a list of DEFLATE events into a Huffman‑coded bit string.
"""

from typing import List, Tuple
from ..Symbol.deflate_events import DEFLATEEvent, LiteralEvent, MatchEvent, EndEvent
from .frequency_counter import count_frequencies
from .tree_builder import build_huffman_tree, extract_code_lengths
from .canonical_codes import build_canonical_codes


def encode_with_huffman(events: List[DEFLATEEvent]) -> Tuple[str, List[int], List[int]]:
    # 1. Count symbol frequencies
    lit_freq, dist_freq = count_frequencies(events)

    # 2. Build Huffman trees
    lit_tree = build_huffman_tree(lit_freq)
    dist_tree = build_huffman_tree(dist_freq)

    # 3. Extract code lengths
    lit_lengths = extract_code_lengths(lit_tree, 286)
    dist_lengths = extract_code_lengths(dist_tree, 30)

    # 4. Build canonical Huffman codes
    lit_codes = build_canonical_codes(lit_lengths)
    dist_codes = build_canonical_codes(dist_lengths)

    # 5. Encode the events
    payload_bits = ""
    for event in events:
        if isinstance(event, LiteralEvent):
            payload_bits += lit_codes[event.symbol]

        elif isinstance(event, MatchEvent):
            payload_bits += lit_codes[event.length_symbol]
            payload_bits += event.length_extra
            payload_bits += dist_codes[event.distance_symbol]
            payload_bits += event.distance_extra

        elif isinstance(event, EndEvent):
            payload_bits += lit_codes[event.symbol]

    return payload_bits, lit_lengths, dist_lengths