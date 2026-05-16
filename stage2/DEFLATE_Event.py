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
    length:int
    lengthExtraBits:str
    distance:int
    distanceExtraBits:str

    def __repr__(self):
        return f"MatchEvent({self.length}, {self.lengthExtraBits}, {self.distance}, {self.distanceExtraBits})"
    
@dataclass(order=True)
class EndEvent:
    #todo :byte of end event is actually a constant 256 so why don't we just set a sonctant value to it? 
    SYMBOL:int = 256 

    def __repr__(self):
        return f"EndEvent({self.SYMBOL})"


#!this union part is just like creating an abstract parent class in java to make sure Event object can hold value of any object from the 3 presented types
deflateEvent = Union[LiteralEvent, MatchEvent, EndEvent]