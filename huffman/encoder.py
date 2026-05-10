"""
Encode a list of DEFLATE events into a Huffman-coded bit string.
"""

from typing import List, Tuple
from symbol.deflate_events import DEFLATEEvent, LiteralEvent, MatchEvent, EndEvent
from huffman.frequency_counter import count_frequencies
from huffman.tree_builder import build_huffman_tree, extract_code_lengths
from huffman.canonical_codes import build_canonical_codes


def encode_with_huffman(events: List[DEFLATEEvent]) -> Tuple[str, List[int], List[int]]:
    # 1. Count symbol frequencies
    lit_freq, dist_freq = count_frequencies(events)

    # 2. Build Huffman trees
    lit_tree = build_huffman_tree(lit_freq)
    dist_tree = build_huffman_tree(dist_freq)

    # 3. Extract code lengths
    lit_lengths = extract_code_lengths(lit_tree, 286)
    dist_lengths = extract_code_lengths(dist_tree, 30)

    # Safety check: Huffman code lengths must not exceed 15 bits
    # for the .sdfl header format (LIT_BW/DIST_BW are 4 bits).
    max_lit = max(lit_lengths) if lit_lengths else 0
    max_dist = max(dist_lengths) if dist_lengths else 0
    
    if max_lit > 15 or max_dist > 15:
        raise ValueError(
            f"Huffman tree depth exceeded limit of 15 bits (Lit: {max_lit}, Dist: {max_dist}). "
            "This can happen with extremely large or skewed files. "
            "A length-limited Huffman algorithm is required to support this data."
        )

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
