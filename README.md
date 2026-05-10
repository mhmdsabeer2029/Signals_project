# SDFL — A DEFLATE-Inspired Compressor

A simplified file compressor and decompressor built from scratch in Python, inspired by the DEFLATE algorithm. Feed it any file, get back a `.sdfl` compressed file. Feed that back, get your original file — byte for byte.

Built as a final project for the Information Theory course at Alexandria University.

---

## 🚀 How It Works

Compression runs through three major stages, each one preparing the data for the next.

### Stage 1 — LZ77: Finding Repetition
The compressor scans the input as a raw byte stream and looks for repeated sequences. Instead of writing the same bytes twice, it emits a reference. The search uses a hash table keyed on 3-byte sequences to avoid checking every previous position, keeping things efficient.

```
abcabcabcabc
→ Literal(a) Literal(b) Literal(c) Match(length=9, distance=3)
```

### Stage 2 — DEFLATE Symbols: Encoding Matches
Raw LZ77 tokens are mapped to a fixed symbol alphabet (0–285) following the DEFLATE specification. This maps literals to their byte values and match lengths/distances to symbols with "extra bits" for precision.

### Stage 3 — Canonical Huffman Coding
Frequent symbols get short codes; rare ones get long codes. By using **Canonical Huffman Coding**, the decompressor only needs the code *lengths* to reconstruct the exact same tree, resulting in a very compact header.

---

## 📄 File Format (.sdfl)

The compressed file is a raw bitstream (MSB-first) with this layout:

| Field | Size | Description |
|---|---|---|
| `LIT_BW` | 4 bits | Bit-width of each literal/length table entry |
| `DIST_BW` | 4 bits | Bit-width of each distance table entry |
| `LIT_TABLE` | 286 × LIT_BW bits | Code lengths for symbols 0–285 |
| `DIST_TABLE` | 30 × DIST_BW bits | Code lengths for symbols 0–29 |
| `PAYLOAD` | Variable | Huffman-coded symbols + raw extra bits |

---

## 🛠 Usage

### Basic Commands
```bash
# Compress a file
python main.py -c myfile.txt

# Decompress a file (recovers original name)
python main.py -d myfile.txt.sdfl
```

### Options
- `-v`, `--verbose`: Show detailed compression statistics, debug offsets, and Huffman table summaries.
- `-o`, `--overwrite`: Overwrite existing output files.

---

## 📊 Performance

SDFL is optimized for clarity and educational value but remains highly effective. 

| Data Type | Compression Ratio | Integrity |
| :--- | :--- | :--- |
| **Random Noise** | ~0.0% (Incompressible) | ✅ Pass |
| **Natural Language** | 40% - 60% | ✅ Pass |
| **Repetitive Data** | Up to 99.5% | ✅ Pass |

*Detailed comparative benchmarks against GZIP and XZ can be found in [BENCHMARK.md](./BENCHMARK.md).*

---

## 🛡 Correctness & Safety

- **Bit-Perfect Guarantee:** Every file is verified to ensure `decompress(compress(data)) == data` byte-for-byte.
- **Safety Checks:** The compressor includes a depth-validator to ensure Huffman trees do not exceed the 15-bit limit imposed by the `.sdfl` header format.
- **Robust I/O:** Implements a custom buffered `BitWriter` and `BitReader` to handle bit-level synchronization across the Python/OS boundary.

---

## ⚠️ Limitations
- **Huffman Depth:** Files that result in a Huffman tree deeper than 15 bits will trigger a safety error.
- **Memory:** As a pure-Python implementation using string-based bitstreams, very large files (e.g., >100MB) may experience high memory overhead.
