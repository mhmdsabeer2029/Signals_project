from Huffman import *

def main():
    symbols = [65, 66, 67, (257, 3, 0, 1), 65, 68, (258, 4, 1, 3), 66, (257, 3, 0, 1), 65]
    frequencies = frequency_counter(symbols)
    length_freq = frequencies[0]
    distance_freq = frequencies[1]
    length_tree = tree_builder(length_freq)
    distance_tree = tree_builder(distance_freq)
    length_huffman = [0] * 286
    distance_huffman = [0] * 30
    huffman_lengths(length_tree , length_huffman , 0 )
    huffman_lengths(distance_tree , distance_huffman , 0)
    length_symbols = [-1] * 286
    distance_symbols = [-1] * 30
    canonical_huffman(length_huffman , length_symbols)
    canonical_huffman(distance_huffman , distance_symbols)
    length_dict = {code: sym for sym, code in enumerate(length_symbols) if code != -1}
    distance_dict = {code: sym for sym, code in enumerate(distance_symbols) if code != -1}
    print(length_dict)
    print(distance_dict)
if __name__ == "__main__":
    main()