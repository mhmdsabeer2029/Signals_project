import heapq
class Node:
    def __init__(self , symbol ,freq):
        self.symbol = symbol
        self.freq = freq
        self.left = None
        self.right = None
#added this to fix small bug
    def __lt__(self, other):
        return self.freq < other.freq

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

def tree_builder(freq_array):
    heap = []
    for sym, freq in enumerate(freq_array):
        if freq > 0:
            heapq.heappush(heap, (freq, Node(sym, freq)))
    while len(heap) != 1:
        sym1 = heapq.heappop(heap)
        sym2 = heapq.heappop(heap)
        parent = Node(None, sym1[0] + sym2[0])
        parent.left = sym1[1]
        parent.right = sym2[1]
        heapq.heappush(heap, (parent.freq, parent))
    tree = heap[0][1]
    return tree

def huffman_lengths(tree, huffman_bitlengths, length):
    if tree.left is None and tree.right is None:
        huffman_bitlengths[tree.symbol] = max(length, 1)
        return
    huffman_lengths(tree.left, huffman_bitlengths, length + 1)
    huffman_lengths(tree.right, huffman_bitlengths, length + 1) #fixed small bug here from extra useless assignment

def canonical_huffman(huffman_bitlengths , symbol_codes):
    count = [0] * 16
    for length in huffman_bitlengths:
        count[length] += 1
    count[0] = 0
    code = 0
    next_available_code = [0] * 16
    for bits in range(1 , 16):
        code = (code + count[bits - 1]) << 1
        next_available_code[bits] = code
    for sym, length in enumerate(huffman_bitlengths):
        if length != 0:
            symbol_codes[sym] = next_available_code[length]
            next_available_code[length] += 1
