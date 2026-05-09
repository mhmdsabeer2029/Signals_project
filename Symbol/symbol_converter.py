"""
Converts lists of LZ77 tokens ↔ lists of DEFLATE events.
Uses LengthCoder and DistanceCoder under the hood.
"""
from typing import List
from ..lz77.lz77_tokens import lz77Token, Literal, Match
from deflate_events import LiteralEvent, MatchEvent, EndEvent, DEFLATEEvent
from length_coder import LengthCoder
from distance_coder import DistanceCoder


class SymbolConverter:
    def __init__(self):
        self.length_coder = LengthCoder()
        self.distance_coder = DistanceCoder()

    def tokens_to_events(self, tokens: List[lz77Token]) -> List[DEFLATEEvent]:
        """
        Turn LZ77 tokens into a list of DEFLATE events, ending with EndEvent.
        """
        events: List[DEFLATEEvent] = []
        for token in tokens:
            if isinstance(token, Literal):
                events.append(LiteralEvent(token.byte))
            elif isinstance(token, Match):
                len_sym, len_extra = self.length_coder.encode(token.length)
                dist_sym, dist_extra = self.distance_coder.encode(token.distance)
                events.append(MatchEvent(len_sym, len_extra,
                                         dist_sym, dist_extra))
        events.append(EndEvent())
        return events

    def events_to_tokens(self, events: List[DEFLATEEvent]) -> List[lz77Token]:
        """
        Turn a list of DEFLATE events back into LZ77 tokens.
        EndEvent is ignored.
        """
        tokens: List[lz77Token] = []
        for event in events:
            if isinstance(event, LiteralEvent):
                tokens.append(Literal(event.symbol))
            elif isinstance(event, MatchEvent):
                length = self.length_coder.decode(event.length_symbol,
                                                  event.length_extra)
                distance = self.distance_coder.decode(event.distance_symbol,
                                                       event.distance_extra)
                tokens.append(Match(length, distance))
            elif isinstance(event, EndEvent):
                # EndEvent does not correspond to any data token
                pass
        return tokens

def tokens__events(tokens: List[lz77Token])-> List[DEFLATEEvent]:
    return SymbolConverter().tokens_to_events(list)
def events__tokens(events: List[DEFLATEEvent]) -> List[lz77Token]:
    return SymbolConverter().events_to_tokens(events)