# LZ77 Tokens has two types of tokens: Literal & Match
# dataClass decorator (Much shorter for quick writing constructors)
from dataclasses import dataclass
# adding Union to tell the compiler that the type can be either of the two types (Literal or Match)
from typing import Union
@dataclass
class Literal:
    # abcabcabcabc
    # byte is the value of the literal, which is an integer (0-255)
    byte : int
    def __repr__(self):
        # return a string representation of the literal in the format "Literal(byte)"
        return f"Literal({self.byte})"
    
@dataclass
class Match:
    # go back ..(distance) and copy ..(length) bytes
    length :int
    distance : int
    def __repr__(self):
        # return a string representation of the match in the format "Match(distance, length)"
        return f"Match(length={self.length}, distance={self.distance})"

lz77Token=Union[Literal, Match]
# AS THE LZ77TOKEN CAN BE EITHER A LITERAL OR A MATCH
