"""
Count symbol frequencies from a list of DEFLATE events.
"""

from typing import List, Tuple
from symbol.deflate_events import DEFLATEEvent, LiteralEvent, MatchEvent, EndEvent


def count_frequencies(events: List[DEFLATEEvent]) -> Tuple[List[int], List[int]]:
    lit_freq = [0] * 286   # literal/length alphabet
    dist_freq = [0] * 30   # distance alphabet

    for event in events:
        if isinstance(event, LiteralEvent):
            lit_freq[event.symbol] += 1
        elif isinstance(event, MatchEvent):
            lit_freq[event.length_symbol] += 1
            dist_freq[event.distance_symbol] += 1
        elif isinstance(event, EndEvent):
            lit_freq[event.symbol] += 1

    return lit_freq, dist_freq