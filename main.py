#!/usr/bin/env python3
"""
Main entry point for the SDFL Compressor and Decompressor.
"""

import argparse
import os
import sys
import time

# Import project-specific modules
try:
    from binary.file_writer import file_writer, print_debug_info
    from binary.file_reader import file_reader
    from binary.BitReader import BitReader
    from binary.header_reader import extract_metadata
except ImportError as e:
    print(f"\033[91mInitialization Error:\033[0m Missing project module: {e}")
    sys.exit(1)


def format_size(size: int) -> str:
    """Helper to format byte sizes into human-readable strings."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def compress_file(input_path: str, overwrite: bool, verbose: bool):
    """Handles the compression pipeline and file output."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file '{input_path}' not found.")

    output_path = f"{input_path}.sdfl"
    if not overwrite and os.path.exists(output_path):
        raise FileExistsError(
            f"Output file '{output_path}' already exists. Use --overwrite to replace it."
        )

    with open(input_path, "rb") as f:
        data = f.read()

    if verbose:
        print(f"[*] Reading '{input_path}' ({format_size(len(data))})...")

    start_time = time.time()
    # file_writer handles Stage 1-4 and writes the .sdfl file via BitWriter
    debug_info = file_writer(input_path, data, overwrite=overwrite)
    duration = time.time() - start_time

    if verbose:
        print(f"[+] Compression completed in {duration:.4f} seconds.")
        print_debug_info(debug_info)
        comp_size = os.path.getsize(output_path)
        ratio = (1 - (comp_size / len(data))) * 100 if len(data) > 0 else 0
        print(f"[*] Statistics:")
        print(f"    - Original Size:   {format_size(len(data))}")
        print(f"    - Compressed Size: {format_size(comp_size)}")
        print(f"    - Space Saved:     {ratio:.2f}%")
    else:
        print(f"Successfully compressed '{input_path}' -> '{output_path}'")


def decompress_file(input_path: str, overwrite: bool, verbose: bool):
    """Handles the decompression pipeline and recovers the original file."""
    if not input_path.endswith(".sdfl"):
        raise ValueError(
            "For decompression, the input file must have a .sdfl extension."
        )

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Compressed file '{input_path}' not found.")

    # BitReader/Writer logic uses name without extension
    base_name = input_path[:-5]
    output_path = base_name

    if not overwrite and os.path.exists(output_path):
        raise FileExistsError(
            f"Output file '{output_path}' already exists. Use --overwrite to replace it."
        )

    if verbose:
        print(f"[*] Decompressing '{input_path}'...")

    start_time = time.time()
    with BitReader(base_name) as reader:
        # 1. Extract Huffman tables from header
        metadata = extract_metadata(reader)
        # 2. Pass the reader and metadata to the file_reader to handle the rest
        # This encapsulates bits_to_events -> events_to_tokens -> tokens_to_bytes
        decoded_data = file_reader(reader, metadata)

    with open(output_path, "wb") as f:
        f.write(decoded_data)
    duration = time.time() - start_time

    if verbose:
        print(f"[+] Decompression completed in {duration:.4f} seconds.")
        print(f"[*] Recovered Size: {format_size(len(decoded_data))}")
    else:
        print(f"Successfully decompressed '{input_path}' -> '{output_path}'")


def main():
    # argparse automatically provides -h/--help support
    parser = argparse.ArgumentParser(
        description="SDFL — A Simplified DEFLATE-Inspired Compressor/Decompressor",
        epilog="Example: python main.py -c data.txt --verbose",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-c",
        "--compress",
        metavar="FILE",
        help="Compress the specified file into .sdfl format",
    )
    group.add_argument(
        "-d",
        "--decompress",
        metavar="FILE",
        help="Decompress the specified .sdfl file",
    )
    parser.add_argument(
        "-o", "--overwrite", action="store_true", help="Overwrite existing output files"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed compression statistics and debug info",
    )

    args = parser.parse_args()

    try:
        if args.compress:
            compress_file(args.compress, args.overwrite, args.verbose)
        else:
            decompress_file(args.decompress, args.overwrite, args.verbose)
    except Exception as e:
        # Beautiful error message formatting
        print(f"\n\033[91m\033[1m[!] Error:\033[0m {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
