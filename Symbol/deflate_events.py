"""
Event data classes for Stage 2.
Literals, Matches (with extra bits), and End-of-block marker.
"""

from dataclasses import dataclass
from typing import Union


@dataclass
class LiteralEvent:
    """A literal byte symbol (0‑255)."""
    symbol: int

    def __repr__(self):
        return f"LiteralEvent({self.symbol})"


@dataclass
class MatchEvent:
    """
    A match token converted into Huffman symbols and raw extra bits.
    length_extra and distance_extra are strings of '0'/'1' (e.g. "01") or empty "".
    """
    length_symbol: int
    length_extra: str
    distance_symbol: int
    distance_extra: str

    def __repr__(self):
        return (f'MatchEvent({self.length_symbol}, "{self.length_extra}", '
                f'{self.distance_symbol}, "{self.distance_extra}")')


@dataclass
class EndEvent:
    """End‑of‑block marker (symbol 256)."""
    symbol: int = 256

    def __repr__(self):
        return f"EndEvent({self.symbol})"


# A DEFLATE event is any of the three types
DEFLATEEvent = Union[LiteralEvent, MatchEvent, EndEvent]