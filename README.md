# SDFL — A DEFLATE-Inspired Compressor

A simplified file compressor and decompressor built from scratch in Python, inspired by the DEFLATE algorithm. Feed it any file, get back a `.sdfl` compressed file. Feed that back, get your original file — byte for byte.

Built as a final project for the Information Theory course at Alexandria University.

---

## How It Works

Compression runs through three stages, each one preparing the data for the next.

### Stage 1 — LZ77: Finding Repetition

The compressor scans the input as a raw byte stream and looks for repeated sequences. Instead of writing the same bytes twice, it emits a reference:

```
abcabcabcabc
→ Literal(a) Literal(b) Literal(c) Match(length=9, distance=3)
```

That match says *"go back 3 bytes and copy 9 bytes"*. The search uses a hash table keyed on 3-byte sequences to avoid checking every previous position, keeping things efficient.

### Stage 2 — DEFLATE Symbols: Encoding Matches

Raw LZ77 tokens can't be Huffman-coded directly — lengths and distances need to be mapped to a fixed symbol alphabet first, exactly like DEFLATE does it.

- Literal bytes map directly to symbols 0–255.
- Match lengths map to symbols 257–285, with extra bits for the exact value.
- Match distances map to symbols 0–29, with extra bits for the exact value.
- A special end-of-block symbol (256) marks where the stream ends.

For example:
```
Match(length=20, distance=6)
→ LengthSymbol(269) + extra bits "01"
  DistanceSymbol(4) + extra bit "1"
```

### Stage 3 — Canonical Huffman Coding: Compressing the Symbols

Frequent symbols get short codes, rare ones get long codes. The compressor builds two separate Huffman trees — one for literal/length symbols, one for distance symbols — based on how often each appears in the token stream.

Canonical Huffman coding is used, meaning the decompressor only needs the code *lengths* to reconstruct the exact same codes. This is what makes the header compact.

---

## File Format (.sdfl)

The compressed file is a raw bitstream with this layout:

| Field | Size | Description |
|---|---|---|
| `LIT_BW` | 4 bits | Bit-width of each literal/length table entry |
| `DIST_BW` | 4 bits | Bit-width of each distance table entry |
| `LIT_TABLE` | 286 × LIT_BW bits | Code lengths for symbols 0–285 |
| `DIST_TABLE` | 30 × DIST_BW bits | Code lengths for symbols 0–29 |
| `PAYLOAD` | variable | Huffman-coded symbols + raw extra bits |

All bits are written most-significant bit first. The last byte is zero-padded if needed.

---

## Usage

To compress a file:
```bash
python main.py -c filename
```
This produces `filename.sdfl` in the same directory.

To decompress:
```bash
python main.py -d filename.sdfl
```
This recovers the original file.

---

## Correctness Guarantee

```
decompress(compress(data)) == data
```

Byte for byte, for most of the files (for some extremely rare cases it can break).