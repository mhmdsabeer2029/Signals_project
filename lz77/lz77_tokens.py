"""create the tokens used in lz77 compression procedure

Classes:
- Literal(byte)
- Match(length, distance)
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Literal:
    """Represents a literal byte in the LZ77 stream."""
    byte: int

    def __repr__(self) -> str:
        return f"Literal({self.byte})"


@dataclass
class Match:
    """Represents a (length, distance) match in the LZ77 stream."""
    length: int
    distance: int

    def __repr__(self) -> str:
        return f"Match(length={self.length}, distance={self.distance})"


lz77Token = Literal | Match
