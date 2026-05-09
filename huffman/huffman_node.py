"""
Node used in a Huffman tree.
"""


class HuffmanNode:
    def __init__(self, freq: int, symbol: int = None, left=None, right=None):
        self.freq = freq
        self.symbol = symbol          # int for leaf, None for internal node
        self.left = left
        self.right = right

        # For tie‑breaking: the smallest symbol in the subtree
        if symbol is not None:
            self.min_symbol = symbol
        else:
            self.min_symbol = min(left.min_symbol, right.min_symbol)

    def is_leaf(self) -> bool:
        return self.symbol is not None

    def __lt__(self, other: 'HuffmanNode') -> bool:
        # Python uses __lt__ for the min‑heap ordering
        if self.freq != other.freq:
            return self.freq < other.freq
        return self.min_symbol < other.min_symbol