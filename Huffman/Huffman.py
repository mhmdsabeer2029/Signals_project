import heapq
class Node:
    def __init__(self , symbol ,freq):
        self.symbol = symbol
        self.freq = freq
        self.left = None
        self.right = None

def frequency_counter(symbols):
    literal_freq = [0] * 286
    distance_freq = [0] * 30
    for sym in symbols:
        if isinstance(sym, int):
            literal_freq[sym] += 1
        elif isinstance(sym, tuple):
            literal_freq[sym[0]] += 1
            distance_freq[sym[2]] += 1
    return literal_freq, distance_freq
