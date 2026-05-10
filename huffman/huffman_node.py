"""
Node used in a Huffman tree.
"""


class HuffmanNode:
    def __init__(self, freq: int, symbol: int = -1, left=None, right=None):
        self.freq = freq
        self.symbol = symbol  # int for leaf, -1 for internal node
        self.left = left
        self.right = right

        # For tie‑breaking: the smallest symbol in the subtree
        if symbol != -1:
            self.min_symbol = symbol
        else:
            # Internal nodes should have children, but we handle None for safety/typing
            left_min = left.min_symbol if left is not None else float('inf')
            right_min = right.min_symbol if right is not None else float('inf')
            self.min_symbol = min(left_min, right_min)

    def is_leaf(self) -> bool:
        return self.symbol != -1

    def __lt__(self, other: "HuffmanNode") -> bool:
        # Python uses __lt__ for the min‑heap ordering
        if self.freq != other.freq:
            return self.freq < other.freq
        return self.min_symbol < other.min_symbol
