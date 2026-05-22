import heapq
from typing import List, Tuple
from symbol.deflate_events import DEFLATEEvent, LiteralEvent, MatchEvent, EndEvent

#todo: this class must be modified extending the __lt__ function and adding self.minSymbol to the branches
class Node:
    def __init__(self, symbol, freq, left=None, right=None):
        self.symbol = symbol  # None for internal nodes, 0-285 for literals/lengths, 0-29 for distances
        self.freq = freq  # Occurrence count of this symbol in the input data
        self.left = left  # 0-bit branch
        self.right = right  # 1-bit branch

        # THE TIE-BREAKER FIX: Track the absolute smallest symbol in this subtree
        if symbol is not None:
            self.min_symbol = symbol
        else:
            # Safely grab the smallest symbol from the children to prevent collisions
            left_min = left.min_symbol if left is not None else float('inf')
            right_min = right.min_symbol if right is not None else float('inf')
            self.min_symbol = min(left_min, right_min)

    # heapq only reaches this function if the tuple frequencies are an exact match
    def __lt__(self, other):
        # Break the tie directly using the smallest symbol in the subtree
        return self.min_symbol < other.min_symbol

#* ________________________________________________________________1:freq arrays_____________________________________________________________
def frequency_counter(events: List[DEFLATEEvent]):
    # DEFLATE spec: 0-255 = raw bytes, 256 = end-of-block, 257-285 = length codes
    literal_freq = [0] * 286
    # DEFLATE spec: 30 distance codes representing backwards distances in the sliding window
    distance_freq = [0] * 30

    for event in events:
        if isinstance(event, LiteralEvent):
            literal_freq[event.symbol] += 1
        elif isinstance(event, MatchEvent):
            literal_freq[event.length_symbol] += 1
            distance_freq[event.distance_symbol] += 1
        elif isinstance(event, EndEvent):
            literal_freq[event.symbol] += 1

    return literal_freq, distance_freq

#* ________________________________________________________________2:Build the tree_____________________________________________________________
def tree_builder(freq_array):
    heap = []
    #!In Python, enumerate() is a built-in function that takes a list (or any iterable) and loops over it, but instead of just handing you the 
    #! items one by one, it hands you a tuple containing both the index and the item.
    # Only symbols that actually appear in the data get nodes — zero-frequency symbols are excluded
    for sym, freq in enumerate(freq_array):
        if freq > 0:
            #! we are pushing a tuple of frequency and Node not just Nodes
            #? why did u add freq to the tuple when we have the __lt__ function in the Node?
            heapq.heappush(heap, (freq, Node(sym, freq)))

    if len(heap) == 0:
        return None
    if len(heap) == 1:
        return heap[0][1]

    # Greedy merge: always combine the two rarest symbols first, minimizing total weighted path length
    while len(heap) != 1:
        sym1 = heapq.heappop(heap)  # Rarest symbol/subtree
        sym2 = heapq.heappop(heap)  # Second-rarest symbol/subtree

        # Internal node has no symbol, its frequency is the combined weight of both 
        #! sym1[0] is the first part of the tuple which is the frequency 
        parent = Node(None, sym1[0] + sym2[0])
        parent.left = sym1[1]
        parent.right = sym2[1]

        heapq.heappush(heap, (parent.freq, parent))

    # Single-symbol input never enters the loop — the one node is already the root
    tree = heap[0][1]
    return tree

"""
    tree -> this is the rootNode of the tree
    huffman_bitlengths --> is a list of zeros of length 30 or 286, defined before passing it
    length --> current depth of the tree, passed from function to function by recursion
"""
#* ________________________________________________________________3:traverse tree for huffman lengths_____________________________________________________________
def huffman_lengths(tree, huffman_bitlengths, length):
    if tree is None:
        return

    # Leaf: depth in the tree == bit-length of its code, min 1 handles the single-symbol edge case
    if tree.left is None and tree.right is None:
        #! max(length, 1) is a safty check for is tree is only a single Node, so no recursion calls, then length will be 0 for first time we enter func, so pass 1 not 0
        huffman_bitlengths[tree.symbol] = max(length, 1)
        return

    # Going deeper adds one bit to the code length for everything in that subtree
    huffman_lengths(tree.left, huffman_bitlengths, length + 1)
    huffman_lengths(tree.right, huffman_bitlengths, length + 1)

#* ________________________________________________________________4:huffman lengths to canonical codes array_____________________________________________________________
def canonical_huffman(huffman_bitlengths):
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
    symbol_codes = {}
    code_symbols = {}
    # Symbols are assigned codes in order of their index — this is what makes it canonical
    for sym, length in enumerate(huffman_bitlengths):
        if length != 0:
            # Modified to save the code as a zero-padded binary string to match reference I/O
            symbol_codes[sym] = format(next_available_code[length], f"0{length}b")
            code_symbols[format(next_available_code[length], f"0{length}b")] = sym
            next_available_code[length] += 1
    #! symbol_code is an array of strings, while code_symbols is a hashmap for easy access by key
    return symbol_codes , code_symbols


def encode_with_huffman(events: List[DEFLATEEvent]) -> Tuple[str, List[int], List[int]]:
    # 1. Count frequencies using the event structures
    lit_freq, dist_freq = frequency_counter(events)

    # 2. Build Trees
    lit_tree = tree_builder(lit_freq)
    dist_tree = tree_builder(dist_freq)

    # 3. Extract code lengths
    lit_lengths = [0] * 286
    dist_lengths = [0] * 30
    huffman_lengths(lit_tree, lit_lengths, 0)
    huffman_lengths(dist_tree, dist_lengths, 0)

    # Max depth safety check mandated by the reference I/O format
    max_lit = max(lit_lengths) if lit_lengths else 0
    max_dist = max(dist_lengths) if dist_lengths else 0

    if max_lit > 15 or max_dist > 15:
        #!raise function immediately stops the program's execution flow when a constraint is violated, printing the error message to the terminal
        raise ValueError(
            f"Huffman tree depth exceeded limit of 15 (Lit: {max_lit}, Dist: {max_dist}). "
            "This can happen with extremely large or skewed files. "
            "A length-limited Huffman algorithm is required to support this data."
        )

    # 4. Generate canonical string representations
    lit_codes = canonical_huffman(lit_lengths)[0]
    dist_codes = canonical_huffman(dist_lengths)[0]

    # 5. Assemble payload bit sequence
    payload_bits = []
    for event in events:
        if isinstance(event, LiteralEvent):
            payload_bits.append(lit_codes[event.symbol])
        elif isinstance(event, MatchEvent):
            payload_bits.append(lit_codes[event.length_symbol])
            payload_bits.append(event.length_extra)
            payload_bits.append(dist_codes[event.distance_symbol])
            payload_bits.append(event.distance_extra)
        elif isinstance(event, EndEvent):
            payload_bits.append(lit_codes[event.symbol])

    payload_bits = "".join(payload_bits)

    return payload_bits, lit_lengths, dist_lengths