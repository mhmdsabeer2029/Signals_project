import heapq

class Node:
    def __init__(self, symbol, freq):
        self.symbol = symbol  # None for internal nodes, 0-285 for literals/lengths, 0-29 for distances
        self.freq = freq      # Occurrence count of this symbol in the input data
        self.left = None      # 0-bit branch
        self.right = None     # 1-bit branch

    # heapq needs this to break frequency ties without comparing Node objects
    def __lt__(self, other):
        return self.freq < other.freq


def frequency_counter(symbols):
    # DEFLATE spec: 0-255 = raw bytes, 256 = end-of-block, 257-285 = length codes
    literal_freq = [0] * 286
    # DEFLATE spec: 30 distance codes representing backwards distances in the sliding window
    distance_freq = [0] * 30

    for sym in symbols:
        if isinstance(sym, int):
            # Literal byte, directly maps to its ASCII/byte value
            literal_freq[sym] += 1
        elif isinstance(sym, tuple):
            # Back-reference (length_code, length, distance_code, distance)
            # sym[0] is the length code (257-285), sym[2] is the distance code (0-29)
            literal_freq[sym[0]] += 1
            distance_freq[sym[2]] += 1

    return literal_freq, distance_freq


def tree_builder(freq_array):
    heap = []

    # Only symbols that actually appear in the data get nodes — zero-frequency symbols are excluded
    for sym, freq in enumerate(freq_array):
        if freq > 0:
            heapq.heappush(heap, (freq, Node(sym, freq)))

    # Greedy merge: always combine the two rarest symbols first, minimizing total weighted path length
    while len(heap) != 1:
        sym1 = heapq.heappop(heap)  # Rarest symbol/subtree
        sym2 = heapq.heappop(heap)  # Second-rarest symbol/subtree

        # Internal node has no symbol, its frequency is the combined weight of both subtrees
        parent = Node(None, sym1[0] + sym2[0])
        parent.left = sym1[1]
        parent.right = sym2[1]

        heapq.heappush(heap, (parent.freq, parent))

    # Single-symbol input never enters the loop — the one node is already the root
    tree = heap[0][1]
    return tree


def huffman_lengths(tree, huffman_bitlengths, length):
    # Leaf: depth in the tree == bit-length of its code, min 1 handles the single-symbol edge case
    if tree.left is None and tree.right is None:
        huffman_bitlengths[tree.symbol] = max(length, 1)
        return

    # Going deeper adds one bit to the code length for everything in that subtree
    huffman_lengths(tree.left, huffman_bitlengths, length + 1)
    huffman_lengths(tree.right, huffman_bitlengths, length + 1)


def canonical_huffman(huffman_bitlengths, symbol_codes):
    # How many symbols share each code length — drives the starting code calculation
    count = [0] * 16
    for length in huffman_bitlengths:
        count[length] += 1

    # Length-0 means unused symbol, must not influence starting code calculations
    count[0] = 0

    # RFC 1951 algorithm: shift previous length's count up, add to running code
    # This guarantees all codes of the same length are numerically consecutive
    code = 0
    next_available_code = [0] * 16
    for bits in range(1, 16):
        code = (code + count[bits - 1]) << 1
        next_available_code[bits] = code

    # Symbols are assigned codes in order of their index — this is what makes it canonical
    for sym, length in enumerate(huffman_bitlengths):
        if length != 0:
            symbol_codes[sym] = next_available_code[length]
            next_available_code[length] += 1