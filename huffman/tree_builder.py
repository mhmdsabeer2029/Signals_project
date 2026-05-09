"""
Building a Huffman tree from frequencies and extracting code lengths.
"""

import heapq
from typing import List, Optional
from .huffman_node import HuffmanNode


def build_huffman_tree(frequencies: List[int]) -> Optional[HuffmanNode]:
    """
    Build a Huffman tree from a list of symbol frequencies.
    Returns the root node, or None if the alphabet is empty.
    """
    heap = []
    for symbol, freq in enumerate(frequencies):
        if freq > 0:
            node = HuffmanNode(freq, symbol=symbol)
            heapq.heappush(heap, node)

    if len(heap) == 0:
        return None
    if len(heap) == 1:
        return heap[0]          # special case: single symbol

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = HuffmanNode(left.freq + right.freq, left=left, right=right)
        heapq.heappush(heap, merged)

    return heap[0]


def extract_code_lengths(root: Optional[HuffmanNode], num_symbols: int) -> List[int]:
    """
    Walk the tree and record the depth of each leaf.
    Returns a list where index i gives code length for symbol i.
    """
    lengths = [0] * num_symbols

    if root is None:
        return lengths

    # Special case: only one symbol → length 1
    if root.is_leaf():
        lengths[root.symbol] = 1
        return lengths

    # Depth‑first search
    def dfs(node: HuffmanNode, depth: int):
        if node.is_leaf():
            lengths[node.symbol] = depth
        else:
            if node.left:
                dfs(node.left, depth + 1)
            if node.right:
                dfs(node.right, depth + 1)

    dfs(root, 0)
    return lengths