# Huffman Coding - Stage 3 Implementation
## Information Theory Final Project - DEFLATE Compressor

---

## 📚 Table of Contents
1. [Project Overview](#project-overview)
2. [File Structure](#file-structure)
3. [Detailed Code Explanation](#detailed-code-explanation)
   - [deflate_constants.py](#deflate_constantspy)
   - [encoder.py](#encoderpy)
   - [decoder.py](#decoderpy)
4. [How Canonical Huffman Coding Works](#how-canonical-huffman-coding-works)
5. [Running the Stage](#running-the-stage)
6. [Integration with Other Stages](#integration-with-other-stages)
7. [Constants and Configuration](#constants-and-configuration)
8. [Examples and Use Cases](#examples-and-use-cases)

---

## 🎯 Project Overview

This is **Stage 3** of the 4-stage simplified DEFLATE compressor project. The full pipeline is:

```
Input Bytes → [Stage 1: LZ77 Tokens] → [Stage 2: DEFLATE Events]
            → [Stage 3: Huffman Coding] → [Stage 4: Binary Output]
```

### Stage 3 (This Implementation)
**Purpose:** Replace the fixed-width DEFLATE event symbols with variable-length Huffman codes — short codes for frequent symbols, long codes for rare ones — so the resulting bitstream is as short as possible.

**Input:** A `List[DEFLATEEvent]` produced by Stage 2 (a mix of `LiteralEvent`, `MatchEvent`, and one trailing `EndEvent`).

**Output:** Three things, ready for Stage 4 to serialize:
- A `payload_bits` string — every event re-encoded as `"0"`/`"1"` characters using the canonical Huffman codes.
- A `lit_lengths` array (length 286) — the code length, in bits, for every literal/length symbol (`0`–`285`).
- A `dist_lengths` array (length 30) — the code length, in bits, for every distance symbol (`0`–`29`).

**Key Idea:** Two canonical Huffman trees are built — one over the literal/length alphabet, one over the distance alphabet. Because the trees are *canonical*, the decoder only needs the **code lengths** to rebuild them, which is exactly what we hand to Stage 4.

---

## 📁 File Structure

```
huffman/
│
├── deflate_constants.py   # RFC 1951 length/distance base & extra-bit tables
├── encoder.py             # Frequency counting, tree building, canonical codes, payload assembly
└── decoder.py             # Re-builds the canonical codes and walks the bitstream back to events
```

**File Dependencies:**
```
deflate_constants.py   (no internal dependencies)
        ↓
encoder.py             (imports symbol.deflate_events)
        ↓
decoder.py             (imports encoder.canonical_huffman,
                        deflate_constants, symbol.deflate_events)
```

The Stage 2 module `symbol/deflate_events.py` defines the three event dataclasses used everywhere here:
```python
LiteralEvent(symbol)
MatchEvent(length_symbol, length_extra, distance_symbol, distance_extra)
EndEvent(symbol=256)
DEFLATEEvent = Union[LiteralEvent, MatchEvent, EndEvent]
```

---

## 🔍 Detailed Code Explanation

### `deflate_constants.py`

This file holds the static **lookup tables** from the DEFLATE spec (RFC 1951). They are referenced by the Huffman encoder/decoder (and optionally by the Symbol stage) whenever a length/distance symbol needs to be paired with the right number of *extra bits*.

```python
"""
Length and distance base / extra-bit tables from the DEFLATE spec.
These are shared by the Huffman encoder/decoder and,
optionally, the Symbol stage.
"""
```
**Line-by-line:**
- Module-level docstring describing what the file is and who consumes it.
- The Huffman encoder doesn't directly read length values, but the decoder needs `LENGTH_EXTRA` / `DISTANCE_EXTRA` to know how many raw bits follow each Huffman code in the payload.

```python
LENGTH_BASE = [
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    13,
    15,
    17,
    19,
    23,
    27,
    31,
    35,
    43,
    51,
    59,
    67,
    83,
    99,
    115,
    131,
    163,
    195,
    227,
    258,
]
```
**What is `LENGTH_BASE`?**
- Indexed by `length_symbol - 257`, i.e. symbols `257`–`285` of the literal/length alphabet.
- Gives the **minimum match length** represented by that symbol.
- The actual length is `LENGTH_BASE[i] + (value of length_extra bits)`.

**Examples:**
- Symbol `257` → base `3`, extra `0` bits → length is exactly `3`.
- Symbol `265` → base `11`, extra `1` bit → length is `11` or `12`.
- Symbol `285` → base `258`, extra `0` bits → maximum length `258`.

```python
LENGTH_EXTRA = [
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    1,
    1,
    1,
    1,
    2,
    2,
    2,
    2,
    3,
    3,
    3,
    3,
    4,
    4,
    4,
    4,
    5,
    5,
    5,
    5,
    0,
]
```
**What is `LENGTH_EXTRA`?**
- Parallel to `LENGTH_BASE`: for symbol `257 + i`, it tells how many *extra* raw (non-Huffman) bits follow.
- Why extra bits? 29 length symbols cannot cover 256 distinct lengths (`3`–`258`) exactly, so DEFLATE assigns each symbol a small *range* and uses extra bits to pinpoint the exact length inside that range.
- The decoder uses `LENGTH_EXTRA[symbol - 257]` to know how many bits to consume right after the length code.

```python
DISTANCE_BASE = [
    1,
    2,
    3,
    4,
    5,
    7,
    9,
    13,
    17,
    25,
    33,
    49,
    65,
    97,
    129,
    193,
    257,
    385,
    513,
    769,
    1025,
    1537,
    2049,
    3073,
    4097,
    6145,
    8193,
    12289,
    16385,
    24577,
]
```
**What is `DISTANCE_BASE`?**
- Indexed by distance symbol `0`–`29`.
- Gives the **minimum backward distance** the symbol represents.
- Actual distance = `DISTANCE_BASE[sym] + (value of distance_extra bits)`.
- Distances span `1`–`32768` (the LZ77 sliding window), encoded compactly through 30 buckets.

```python
DISTANCE_EXTRA = [
    0,
    0,
    0,
    0,
    1,
    1,
    2,
    2,
    3,
    3,
    4,
    4,
    5,
    5,
    6,
    6,
    7,
    7,
    8,
    8,
    9,
    9,
    10,
    10,
    11,
    11,
    12,
    12,
    13,
    13,
]
```
**What is `DISTANCE_EXTRA`?**
- Parallel to `DISTANCE_BASE`. For distance symbol `i`, it tells how many extra raw bits follow.
- The decoder uses `DISTANCE_EXTRA[symbol]` to know how many bits to consume right after the distance Huffman code.
- The exponential growth (`0, 0, 0, 0, 1, 1, 2, 2, ...`) is what lets 30 symbols cover all the way out to `32768`.

---

### `encoder.py`

This file implements the Huffman compression logic: counting symbol frequencies, building two Huffman trees, deriving canonical codes, and assembling the final payload bitstring.

```python
import heapq
from typing import List, Tuple
from symbol.deflate_events import DEFLATEEvent, LiteralEvent, MatchEvent, EndEvent
```
**Line-by-line:**
- `heapq` — Python's binary min-heap implementation; used to repeatedly pop the two least-frequent nodes when building the Huffman tree.
- `List`, `Tuple` — type hints used in function signatures.
- The three event dataclasses + the `DEFLATEEvent` union alias come from Stage 2. The encoder dispatches on the event type with `isinstance(...)`.

```python
#todo: this class must be modified extending the __lt__ function and adding self.minSymbol to the branches
class Node:
    def __init__(self, symbol, freq, left=None, right=None):
        self.symbol = symbol  # None for internal nodes, 0-285 for literals/lengths, 0-29 for distances
        self.freq = freq  # Occurrence count of this symbol in the input data
        self.left = left  # 0-bit branch
        self.right = right  # 1-bit branch
```
**What is `Node`?**
- A node in the Huffman tree.
- `symbol`: the integer alphabet symbol (or `None` for internal nodes that are just structural merges).
- `freq`: total frequency carried by this node — a leaf's own count, or the sum of two children for internal nodes.
- `left`/`right`: child references, where convention assigns `left = bit 0` and `right = bit 1` during traversal.

```python
        # THE TIE-BREAKER FIX: Track the absolute smallest symbol in this subtree
        if symbol is not None:
            self.min_symbol = symbol
        else:
            # Safely grab the smallest symbol from the children to prevent collisions
            left_min = left.min_symbol if left is not None else float('inf')
            right_min = right.min_symbol if right is not None else float('inf')
            self.min_symbol = min(left_min, right_min)
```
**Why `min_symbol`?**
- When two heap entries have the **exact same frequency**, Python's `heapq` needs *some* deterministic ordering between them or it crashes trying to compare `Node` objects.
- For leaves we cache the symbol itself; for internal nodes we cache the smallest symbol anywhere in the subtree.
- This gives a stable, reproducible tie-breaker that yields the same tree every run — essential because the decoder relies on identical canonical codes.

```python
    # heapq only reaches this function if the tuple frequencies are an exact match
    def __lt__(self, other):
        # Break the tie directly using the smallest symbol in the subtree
        return self.min_symbol < other.min_symbol
```
**`__lt__` (less-than) operator:**
- `heapq` pushes tuples shaped as `(freq, Node)`. Python compares tuples element-by-element.
- If two `freq` values are equal, Python falls through and compares the `Node` objects — at which point this `__lt__` runs.
- Returning a strict comparison on `min_symbol` guarantees there is always a clear winner and avoids `TypeError: '<' not supported between instances of 'Node' and 'Node'`.

```python
#* ________________________________________________________________1:freq arrays_____________________________________________________________
def frequency_counter(events: List[DEFLATEEvent]):
    # DEFLATE spec: 0-255 = raw bytes, 256 = end-of-block, 257-285 = length codes
    literal_freq = [0] * 286
    # DEFLATE spec: 30 distance codes representing backwards distances in the sliding window
    distance_freq = [0] * 30
```
**Step 1 — count how often each symbol appears:**
- `literal_freq[s]` will hold the count of literal/length symbol `s` (alphabet size 286).
- `distance_freq[s]` will hold the count of distance symbol `s` (alphabet size 30).
- Two separate alphabets means two separate Huffman trees later on.

```python
    for event in events:
        if isinstance(event, LiteralEvent):
            literal_freq[event.symbol] += 1
        elif isinstance(event, MatchEvent):
            literal_freq[event.length_symbol] += 1
            distance_freq[event.distance_symbol] += 1
        elif isinstance(event, EndEvent):
            literal_freq[event.symbol] += 1

    return literal_freq, distance_freq
```
**Dispatch on event type:**
- `LiteralEvent` — just one literal symbol (`0`–`255`).
- `MatchEvent` — contributes one length symbol (`257`–`285`) **and** one distance symbol (`0`–`29`).
- `EndEvent` — contributes the end-of-block marker `256`. Every block has exactly one of these and it must appear in the tree so the decoder can find a code for it.
- Returns both tables for the next pipeline step.

```python
#* ________________________________________________________________2:Build the tree_____________________________________________________________
def tree_builder(freq_array):
    heap = []
```
**Step 2 — build a Huffman tree from a frequency array:**
- This function is called twice — once for `lit_freq`, once for `dist_freq`.
- `heap` starts empty and will grow into a min-heap of `(freq, Node)` tuples.

```python
    #!In Python, enumerate() is a built-in function that takes a list (or any iterable) and loops over it, but instead of just handing you the
    #! items one by one, it hands you a tuple containing both the index and the item.
    # Only symbols that actually appear in the data get nodes — zero-frequency symbols are excluded
    for sym, freq in enumerate(freq_array):
        if freq > 0:
            #! we are pushing a tuple of frequency and Node not just Nodes
            #? why did u add freq to the tuple when we have the __lt__ function in the Node?
            heapq.heappush(heap, (freq, Node(sym, freq)))
```
**Seeding the heap:**
- Walk every alphabet position with `enumerate`, giving `(index, value)` = `(symbol, frequency)`.
- Skip symbols with frequency `0` — assigning them a code would waste bits and bloat the tree.
- Push `(freq, Node(sym, freq))` so `heapq` orders primarily by frequency. The `Node` is only compared when there's a tie, which is exactly when `__lt__` from above kicks in.

```python
    if len(heap) == 0:
        return None
    if len(heap) == 1:
        return heap[0][1]
```
**Degenerate cases:**
- `len == 0` → no symbol appears (e.g. an empty distance stream when the block had no matches). Return `None`; downstream code interprets that as "this alphabet contributed nothing".
- `len == 1` → only one distinct symbol. There's nothing to merge, so the lone leaf *is* the root. Code length will be patched up to `1` in `huffman_lengths` because a zero-bit code is meaningless.

```python
    # Greedy merge: always combine the two rarest symbols first, minimizing total weighted path length
    while len(heap) != 1:
        sym1 = heapq.heappop(heap)  # Rarest symbol/subtree
        sym2 = heapq.heappop(heap)  # Second-rarest symbol/subtree
```
**The classic Huffman loop:**
- Pop the two cheapest items. `sym1` and `sym2` are full `(freq, Node)` tuples.
- The greedy property of Huffman's algorithm guarantees that merging rarest pairs first minimizes total weighted depth (i.e. the expected bit length per symbol).

```python
        # Internal node has no symbol, its frequency is the combined weight of both
        #! sym1[0] is the first part of the tuple which is the frequency
        parent = Node(None, sym1[0] + sym2[0])
        parent.left = sym1[1]
        parent.right = sym2[1]

        heapq.heappush(heap, (parent.freq, parent))
```
**Merging two subtrees:**
- Create a new internal `Node(symbol=None)` whose `freq` is the sum of its two children's frequencies.
- `sym1[0]` is the popped tuple's frequency; `sym1[1]` is the actual `Node` object.
- Convention here: the rarer of the two becomes the **left** child, the next-rarer becomes the **right** child. (Because of canonical Huffman in the next step, this left/right convention does not affect the final codes — only the resulting bit-lengths matter.)
- Push the new parent back into the heap; it will compete with the remaining nodes on its combined frequency.

```python
    # Single-symbol input never enters the loop — the one node is already the root
    tree = heap[0][1]
    return tree
```
**Wrap-up:**
- After the loop, the heap holds exactly one entry: the root.
- Comment is a reminder that the `len == 1` early return above already covers the edge case so this line is safe.

```python
"""
    tree -> this is the rootNode of the tree
    huffman_bitlengths --> is a list of zeros of length 30 or 286, defined before passing it
    length --> current depth of the tree, passed from function to function by recursion
"""
#* ________________________________________________________________3:traverse tree for huffman lengths_____________________________________________________________
def huffman_lengths(tree, huffman_bitlengths, length):
    if tree is None:
        return
```
**Step 3 — collect code lengths via DFS:**
- This is the bridge between "Huffman tree" and "canonical Huffman codes": we record *how deep* each leaf is, then forget the tree.
- `huffman_bitlengths` is a pre-allocated array of zeros that we mutate in place.
- `length` is the current depth (starts at `0` for the root, grows by `1` each recursive call).
- `tree is None` guard handles the empty-alphabet case where `tree_builder` returned `None`.

```python
    # Leaf: depth in the tree == bit-length of its code, min 1 handles the single-symbol edge case
    if tree.left is None and tree.right is None:
        #! max(length, 1) is a safty check for is tree is only a single Node, so no recursion calls, then length will be 0 for first time we enter func, so pass 1 not 0
        huffman_bitlengths[tree.symbol] = max(length, 1)
        return
```
**Leaf handling:**
- A leaf has no children; its **depth in the tree equals its Huffman code length in bits**.
- `max(length, 1)` patches the degenerate "only one symbol in the alphabet" case: depth would be `0`, but a code length of `0` traditionally means "symbol unused", so we bump it to `1`. The decoder then has a real one-bit code for that single symbol.

```python
    # Going deeper adds one bit to the code length for everything in that subtree
    huffman_lengths(tree.left, huffman_bitlengths, length + 1)
    huffman_lengths(tree.right, huffman_bitlengths, length + 1)
```
**Recursion:**
- Internal node — recurse into both children with `length + 1`, because moving down one edge appends one bit to the code.
- The mutation of `huffman_bitlengths` happens at the leaves, so both subtrees can safely share the same list.

```python
#* ________________________________________________________________4:huffman lengths to canonical codes array_____________________________________________________________
def canonical_huffman(huffman_bitlengths):
    # How many symbols share each code length — drives the starting code calculation
    count = [0] * 16
    for length in huffman_bitlengths:
        count[length] += 1
```
**Step 4 — turn a code-length vector into the canonical codes (RFC 1951 §3.2.2):**
- Why canonical? Because the decoder only receives the lengths (not the trees), and two parties can deterministically reproduce the same codes purely from the lengths.
- `count[k]` = how many symbols have code length `k`.
- Size `16` because the DEFLATE format limits code lengths to `15` bits; this gives us indices `0..15`.

```python
    # Length-0 means unused symbol, must not influence starting code calculations
    count[0] = 0
```
**Zero out `count[0]`:**
- A length of `0` means the symbol isn't in the alphabet/tree at all.
- We must not let those phantom symbols shift the next available code, so we wipe them.

```python
    # RFC 1951 algorithm: shift previous length's count up, add to running code
    # This guarantees all codes of the same length are numerically consecutive
    code = 0
    next_available_code = [0] * 16
    for bits in range(1, 16):
        code = (code + count[bits - 1]) << 1
        next_available_code[bits] = code
```
**Computing the starting code for every length:**
- This is verbatim the algorithm from RFC 1951.
- For each length `bits`, take the previous length's count, add it to the running code, then shift left by one bit (equivalent to `* 2`).
- `next_available_code[bits]` is the first numeric value that will be handed out for any symbol of that length.
- Effect: within one length all assigned codes are consecutive integers; across lengths the bit-prefix property is preserved.

```python
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
```
**Assigning codes:**
- Walk symbols in numeric order (`enumerate` of the bit-length array).
- Skip symbols whose length is `0` (they're unused).
- `format(value, f"0{length}b")` turns the integer into a zero-padded binary string — e.g. `format(5, "04b")` → `"0101"`. The zero-padding is critical so a code like `001` is not confused with `01`.
- Build two dictionaries:
  - `symbol_codes[sym] = "010..."` for **encoding** (look up the bitstring for a given symbol).
  - `code_symbols["010..."] = sym` for **decoding** (look up the symbol for a given bitstring).
- `next_available_code[length] += 1` makes sure the next symbol of the same length gets the consecutive integer.
- Comment on the return line is a slight misnomer — both returned values are dictionaries (`{sym: code}` and `{code: sym}`), not arrays.

```python
def encode_with_huffman(events: List[DEFLATEEvent]) -> Tuple[str, List[int], List[int]]:
    # 1. Count frequencies using the event structures
    lit_freq, dist_freq = frequency_counter(events)
```
**The public driver — `encode_with_huffman`:**
- Takes the Stage 2 event list, returns `(payload_bits, lit_lengths, dist_lengths)` ready to be serialized by Stage 4.
- Step 1: build both frequency arrays.

```python
    # 2. Build Trees
    lit_tree = tree_builder(lit_freq)
    dist_tree = tree_builder(dist_freq)
```
- Step 2: build two independent Huffman trees, one per alphabet.

```python
    # 3. Extract code lengths
    lit_lengths = [0] * 286
    dist_lengths = [0] * 30
    huffman_lengths(lit_tree, lit_lengths, 0)
    huffman_lengths(dist_tree, dist_lengths, 0)
```
- Step 3: pre-allocate length vectors and fill them by walking each tree. Unused symbols keep their `0`.

```python
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
```
**Depth guard (`> 15`):**
- The `.sdfl` file format uses at most 4 bits to store each entry's bit-length — so the maximum representable length is `15`.
- Highly skewed distributions (e.g. one symbol with frequency `1` and another with frequency `10⁶`) can produce trees deeper than that.
- Raising early gives a clean error message instead of silently corrupting the bitstream. A length-limited Huffman variant (Package-Merge, Boundary Package-Merge, etc.) would be needed to support such inputs.

```python
    # 4. Generate canonical string representations
    lit_codes = canonical_huffman(lit_lengths)[0]
    dist_codes = canonical_huffman(dist_lengths)[0]
```
- Step 4: derive canonical codes for each alphabet. We only need the encoding direction here (`[0]` = the `symbol → code` dict). The decoder will recompute the other direction (`[1]`) from the same lengths.

```python
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
```
**Step 5 — write the payload:**
- Loop over the original event stream **in order** (order matters for decoding).
- `LiteralEvent` → one Huffman code (the literal's symbol code).
- `MatchEvent` → four chunks back-to-back: `[length_code][length_extra][distance_code][distance_extra]`. The `length_extra` and `distance_extra` are raw, *non-Huffman* bits already prepared by Stage 2.
- `EndEvent` → one Huffman code for the `256` end-of-block marker.
- Strings are accumulated in a list and joined at the end — much faster than repeated string concatenation.
- Return tuple: payload bitstring + both length vectors. Stage 4 will pack `lit_lengths` + `dist_lengths` into the header and `payload_bits` into the body.

---

### `decoder.py`

This file reverses the encoder: given the same length vectors (recovered from the header) plus the payload bits, it walks the stream and rebuilds the original event list.

```python
from huffman.encoder import canonical_huffman
from huffman.deflate_constants import LENGTH_EXTRA, DISTANCE_EXTRA
from symbol.deflate_events import MatchEvent, LiteralEvent, EndEvent
```
**Line-by-line:**
- Reuses `canonical_huffman` from the encoder — it's deterministic, so rebuilding it from the same lengths yields the exact same codes.
- Pulls `LENGTH_EXTRA` / `DISTANCE_EXTRA` so the decoder knows how many raw bits follow each Huffman code.
- Imports the three event classes to reconstruct the stream.

```python
def decode_with_huffman(payload_bits, lit_lengths, dist_lengths):
    # Assuming canonical_huffman returns (sym_to_code, code_to_sym)
    # and we want the code_to_sym dict at index [1]
    lit_symbols = canonical_huffman(lit_lengths)[1]
    dist_symbols = canonical_huffman(dist_lengths)[1]
```
**Setup:**
- `payload_bits` is the raw bit-string written by `encode_with_huffman` — a flat sequence of `'0'`/`'1'` characters.
- Index `[1]` gives the `{bitstring → symbol}` dictionary, which is what we'll be looking up on each match.
- Two lookup tables, one per alphabet.

```python
    events_list = []
    flag = True
    i = 0  # Our global bitstream pointer
```
- `events_list` collects the reconstructed events in order.
- `flag` is the loop sentinel: stays `True` until we hit the end-of-block code (`256`).
- `i` is the current bit index into `payload_bits`. It only ever moves forward.

```python
    while flag and i < len(payload_bits):
        # Scan for a Literal/Length code (try windows of size 1 to 15)
        for length in range(1, 16):
            current_lit_code = payload_bits[i: i + length]
            current_lit_symbol = lit_symbols.get(current_lit_code, -1)
```
**Greedy prefix scan — outer loop:**
- We don't know the next code's length, so we try lengths `1`, `2`, `3`, ... up to `15`.
- Slice `payload_bits[i : i+length]` to get the candidate code.
- `.get(code, -1)` either returns the symbol or `-1` if this exact bit-pattern isn't a valid code at this length. (Canonical Huffman codes are *prefix-free*, so at most one length will match.)

```python
            if current_lit_symbol != -1:
                # We found a valid symbol! Advance past its Huffman code bits
                i += length
```
- A `!= -1` means we matched a real symbol; advance the bit pointer past the consumed code.

```python
                if current_lit_symbol == 256:
                    events_list.append(EndEvent())
                    flag = False
                    break  # Break the inner length loop
```
**End-of-block:**
- Symbol `256` is the special "stop" marker.
- Append an `EndEvent()` (defaults `symbol=256`), set `flag = False` so the `while` exits, then `break` out of the inner `for`.

```python
                elif current_lit_symbol < 256:
                    events_list.append(LiteralEvent(current_lit_symbol))
                    break  # Break the inner length loop to get next literal
```
**Literal byte:**
- Symbols `0`–`255` are raw literal bytes, with no extra bits.
- Wrap in `LiteralEvent` and move on.

```python
                else:
                    # It's a MATCH! (257 to 285)
                    # 1. Pull the length extra bits
                    num_len_extra = LENGTH_EXTRA[current_lit_symbol - 257]
                    lit_extra = payload_bits[i: i + num_len_extra]
                    i += num_len_extra  # Advance past the extra length bits
```
**Match decoding — part 1, length extra bits:**
- Symbols `257`–`285` are length codes. Right after the Huffman code comes some number of raw extra bits.
- `LENGTH_EXTRA[symbol - 257]` says exactly how many.
- Slice those raw bits and keep them as a string so they can be repackaged into a `MatchEvent` later (the Symbol stage knows how to combine `LENGTH_BASE` + this extra value to recover the true length).

```python
                    # 2. IMMEDIATELY start scanning for the distance symbol
                    current_dist_symbol = -1
                    for dist_length in range(1, 16):
                        current_dist_code = payload_bits[i: i + dist_length]
                        current_dist_symbol = dist_symbols.get(current_dist_code, -1)

                        if current_dist_symbol != -1:
                            i += dist_length  # Advance past distance Huffman code bits
                            break
```
**Match decoding — part 2, distance Huffman code:**
- Mirror of the outer scan, but using the **distance** code table.
- Try every length from `1` to `15` against `dist_symbols`; first hit wins.
- Advance `i` past the matched bits and break the inner loop.

```python
                    # 3. Pull the distance extra bits
                    num_dist_extra = DISTANCE_EXTRA[current_dist_symbol]
                    dist_extra = payload_bits[i: i + num_dist_extra]
                    i += num_dist_extra  # Advance past extra distance bits
```
**Match decoding — part 3, distance extra bits:**
- Look up `DISTANCE_EXTRA[dist_symbol]` to find how many raw bits follow.
- Slice them and advance.

```python
                    # 4. Pack and store the MatchEvent
                    events_list.append(MatchEvent(
                        current_lit_symbol,
                        lit_extra,
                        current_dist_symbol,
                        dist_extra
                    ))
                    break  # Break out of the original length loop to start next token
```
**Match decoding — part 4, assemble the event:**
- Reconstruct the original `MatchEvent` with the same four fields the encoder consumed: `length_symbol`, `length_extra`, `distance_symbol`, `distance_extra`.
- `break` out of the outer length-scan to start the next iteration of the `while` for the next event.

```python
    return events_list
```
- The final list mirrors what Stage 2 produced — Stage 2 can then turn these events back into LZ77 tokens, and Stage 1 reconstructs the original bytes from there.

---

## 🧬 How Canonical Huffman Coding Works

The encoder/decoder pair above leans on three classical ideas. Here's the intuition behind each.

### 1. Huffman's greedy tree build
Given a frequency table, repeatedly merge the **two lowest-frequency** nodes into a parent whose frequency is their sum, until one node remains. The resulting tree minimizes the expected number of bits per symbol — that is the formal optimality theorem for prefix codes.

Why a min-heap? Because we always need the two smallest items quickly; `heapq` makes that an `O(log n)` operation per merge.

### 2. Code-length-only representation
Instead of shipping the tree, we ship the **length** of every symbol's code. Why is that enough? Two reasons:
1. Every binary tree where leaves only ever live at depths `0..15` is fully described by counting how many leaves sit at each depth (that's exactly the `count` array in `canonical_huffman`).
2. There is a unique mapping from *that count vector* to a canonical set of codes — both encoder and decoder agree to "sort symbols ascending by code length, ties broken by symbol number".

So the decoder only needs `lit_lengths` + `dist_lengths` to rebuild bit-identical codebooks.

### 3. The canonical recurrence
Inside `canonical_huffman`, the key line is:

```python
code = (code + count[bits - 1]) << 1
```

This is the RFC 1951 recurrence. It says: "the first code of length `b` is the previous length's first code, plus the number of codes of length `b-1`, shifted left by one." That shift moves us one level deeper in the tree, and the addition skips past all codes already assigned at the shallower depth.

Combined with assigning codes to symbols in numeric order, every implementation that follows this recipe ends up with identical bitstrings — which is exactly the property the decoder relies on.

### 4. Why we still need extra bits
Huffman codes alone can't efficiently represent 256 distinct match lengths or 32768 distinct distances — the alphabet would be huge and most symbols rare. DEFLATE collapses those big ranges into a small symbol set (29 length codes, 30 distance codes) and appends raw "extra bits" to pinpoint the exact value within each bucket. That's why the decoder consults `LENGTH_EXTRA[symbol - 257]` and `DISTANCE_EXTRA[symbol]` after every Huffman code for a match.

---

## ▶️ Running the Stage

This folder is a library — there are no `__main__` blocks here. To exercise it end-to-end, drive it through the top-level pipeline:

```bash
# Run the full pipeline round-trip validation (Stages 1 → 4)
python3 interface.py

# Compress / decompress a real file (uses this module under the hood)
python3 main.py -c README.md
python3 main.py -d README.md.sdfl
```

To exercise it directly in a Python session:

```python
from symbol.deflate_events import LiteralEvent, MatchEvent, EndEvent
from huffman.encoder import encode_with_huffman
from huffman.decoder import decode_with_huffman

events = [
    LiteralEvent(97),                  # 'a'
    LiteralEvent(98),                  # 'b'
    LiteralEvent(99),                  # 'c'
    MatchEvent(258, "0", 2, ""),       # length=9 region, distance=3 region (example shape)
    EndEvent(),                        # end-of-block (symbol 256)
]

payload, lit_lengths, dist_lengths = encode_with_huffman(events)
recovered = decode_with_huffman(payload, lit_lengths, dist_lengths)

assert recovered == events
```

(The exact `MatchEvent` arguments depend on what Stage 2 produces for that particular length/distance — the round-trip property is what's important here.)

---

## 🔗 Integration with Other Stages

### Stage 2 → Stage 3: Symbols become bits

**Stage 3 Input:** `List[DEFLATEEvent]` — `LiteralEvent`, `MatchEvent`, `EndEvent`.
**Stage 3 Output:** `(payload_bits: str, lit_lengths: List[int], dist_lengths: List[int])`.

The translation between the two is purely string-level: Stage 2 already produced the `length_extra` / `distance_extra` *as bitstrings*. Stage 3 only adds Huffman codes for the symbols and concatenates everything.

### Stage 3 → Stage 4: Bits become bytes

**Stage 4 Input:** the three values above.
**Stage 4 Output:** a `.sdfl` file laid out as:

```
[4 bits: LIT_BW]  [4 bits: DIST_BW]
[286 × LIT_BW bits: literal/length code lengths]
[30 × DIST_BW bits: distance code lengths]
[Variable: Huffman-coded payload]
[Padding to byte boundary]
```

Where `LIT_BW = ceil(log2(max(lit_lengths) + 1))` and similarly for `DIST_BW`, so the header itself shrinks when codes happen to be short. The depth guard inside `encode_with_huffman` is what guarantees both fit in 4 bits (max value `15`).

### Decompression flow

Stage 4 reads the header, recovers `lit_lengths` and `dist_lengths`, then peels off `payload_bits` and hands all three to `decode_with_huffman`. From there the chain reverses naturally:

```
.sdfl bytes → [Stage 4: bits + lengths]
            → [Stage 3: decode_with_huffman → events]
            → [Stage 2: events → LZ77 tokens]
            → [Stage 1: tokens → original bytes]
```

### Integration Checklist

- [x] Stage 3 consumes `List[DEFLATEEvent]`.
- [x] Stage 3 produces `(payload_bits, lit_lengths, dist_lengths)`.
- [x] Stage 3 enforces the 15-bit depth limit (`ValueError` if exceeded).
- [x] `canonical_huffman` returns both `{sym → code}` and `{code → sym}` — encoder uses the first, decoder the second.
- [x] Verify round-trip: `decode_with_huffman(*encode_with_huffman(events)) == events`.

---

## ⚙️ Constants and Configuration

### Hard constraints (do not change without touching the file format)

| Constant | Value | Where | Purpose |
|---|---|---|---|
| Literal/length alphabet size | `286` | `encoder.py` (`[0] * 286`) | DEFLATE: `0–255` raw bytes + `256` end-of-block + `257–285` length codes |
| Distance alphabet size | `30` | `encoder.py` (`[0] * 30`) | DEFLATE: distance codes `0–29` |
| Max code length | `15` | `encoder.py` (depth guard, `range(1, 16)`) | `.sdfl` header stores lengths in 4 bits → max value 15 |
| `LENGTH_BASE` / `LENGTH_EXTRA` | 29 entries each | `deflate_constants.py` | Encode/decode lengths `3–258` |
| `DISTANCE_BASE` / `DISTANCE_EXTRA` | 30 entries each | `deflate_constants.py` | Encode/decode distances `1–32768` |

### Things you *can* tune

- **Length-limited Huffman.** If you hit the `> 15` `ValueError` on real data, swap `tree_builder` for a Package-Merge implementation. The rest of the pipeline keeps working because `canonical_huffman` only cares about the resulting length vector.
- **Single-symbol bump.** The `max(length, 1)` patch in `huffman_lengths` is the simplest fix for degenerate alphabets. If you want a more elaborate convention (e.g. emit nothing at all when only one symbol exists and store the symbol value separately), this is the place to do it.
- **Heap tie-breaking.** `min_symbol` produces a deterministic, smallest-symbol-wins tie-break. If you'd prefer largest-symbol-wins or insertion-order, change `__lt__` accordingly — but be sure encoder and decoder agree (the decoder calls the same `canonical_huffman`, so they will).

---

## 📊 Examples and Use Cases

### Example 1: Highly repetitive input

```python
from symbol.deflate_events import LiteralEvent, EndEvent
from huffman.encoder import encode_with_huffman

# 1000 copies of the byte 'a' -> 1 literal symbol dominates the frequency table
events = [LiteralEvent(ord('a'))] * 1000 + [EndEvent()]
payload, lit_lengths, dist_lengths = encode_with_huffman(events)

print(f"Distinct lit symbols used : {sum(1 for l in lit_lengths if l > 0)}")  # 2 ('a' and 256)
print(f"Max lit code length       : {max(lit_lengths)}")                       # 1
print(f"Payload bits              : {len(payload)}")                           # ~1001 bits
```

Both `'a'` and `EndEvent` get a 1-bit code, and the entire payload is essentially `1001` bits long — close to the theoretical entropy lower bound for this distribution.

### Example 2: Symmetric distribution (worst-case tree depth)

```python
from symbol.deflate_events import LiteralEvent, EndEvent
from huffman.encoder import encode_with_huffman

# Two equally frequent symbols + end marker -> balanced tree
events = (
    [LiteralEvent(0)] * 100 +
    [LiteralEvent(1)] * 100 +
    [EndEvent()]
)
payload, lit_lengths, _ = encode_with_huffman(events)
print(lit_lengths[0], lit_lengths[1], lit_lengths[256])   # 1, 2, 2  (or 2, 2, 1 — order depends on freq)
```

The `min_symbol` tie-breaker is what makes the resulting lengths reproducible across runs.

### Example 3: Round-trip sanity check

```python
from symbol.deflate_events import LiteralEvent, MatchEvent, EndEvent
from huffman.encoder import encode_with_huffman
from huffman.decoder import decode_with_huffman

events = [
    LiteralEvent(72),   # 'H'
    LiteralEvent(105),  # 'i'
    LiteralEvent(33),   # '!'
    EndEvent(),
]
payload, lit_lengths, dist_lengths = encode_with_huffman(events)
assert decode_with_huffman(payload, lit_lengths, dist_lengths) == events
```

### Example 4: Catching the depth guard

```python
from symbol.deflate_events import LiteralEvent, EndEvent
from huffman.encoder import encode_with_huffman

# Fibonacci-style frequencies are notorious for producing tall Huffman trees.
freqs = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597]

events = []
for sym, f in enumerate(freqs):
    events += [LiteralEvent(sym)] * f
events.append(EndEvent())

try:
    encode_with_huffman(events)
except ValueError as e:
    print("Depth guard triggered:", e)
```

When the natural Huffman tree exceeds 15 levels, the encoder refuses to corrupt the bitstream and surfaces a descriptive error instead.

---
