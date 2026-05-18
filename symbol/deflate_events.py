from dataclasses import dataclass
from typing import Union

@dataclass(order=True)
class LiteralEvent:
    #*this is just type hinting not a declaration at all cuz py don't have declaration. the @dataclass will do the intialization func. job
    symbol:int

    #* Python explicitly ignores __str__ when printing collections and strictly calls __repr__ for every item inside the array.
    def __repr__(self):
        return f"LiteralEvent({self.symbol})"
@dataclass(order=True)
class MatchEvent:
    length_symbol: int
    length_extra: str
    distance_symbol: int
    distance_extra: str

    def __repr__(self):
        return f"MatchEvent({self.length_symbol}, {self.length_extra}, {self.distance_symbol}, {self.distance_extra})"    

@dataclass(order=True)
class EndEvent:
    # Changed SYMBOL to symbol
    symbol: int = 256 

    def __repr__(self):
        return f"EndEvent({self.symbol})"


#!this union part is just like creating an abstract parent class in java to make sure Event object can hold value of any object from the 3 presented types
DEFLATEEvent = Union[LiteralEvent, MatchEvent, EndEvent]