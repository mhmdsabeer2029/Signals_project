from huffman.encoder import canonical_huffman
from huffman.deflate_constants import LENGTH_EXTRA, DISTANCE_EXTRA
from symbol.deflate_events import MatchEvent, LiteralEvent, EndEvent


def decode_with_huffman(payload_bits, lit_lengths, dist_lengths):
    # Assuming canonical_huffman returns (sym_to_code, code_to_sym)
    # and we want the code_to_sym dict at index [1]
    lit_symbols = canonical_huffman(lit_lengths)[1]
    dist_symbols = canonical_huffman(dist_lengths)[1]

    events_list = []
    flag = True
    i = 0  # Our global bitstream pointer

    while flag and i < len(payload_bits):
        # Scan for a Literal/Length code (try windows of size 1 to 15)
        for length in range(1, 16):
            current_lit_code = payload_bits[i: i + length]
            current_lit_symbol = lit_symbols.get(current_lit_code, -1)

            if current_lit_symbol != -1:
                # We found a valid symbol! Advance past its Huffman code bits
                i += length

                if current_lit_symbol == 256:
                    events_list.append(EndEvent())
                    flag = False
                    break  # Break the inner length loop

                elif current_lit_symbol < 256:
                    events_list.append(LiteralEvent(current_lit_symbol))
                    break  # Break the inner length loop to get next literal

                else:
                    # It's a MATCH! (257 to 285)
                    # 1. Pull the length extra bits
                    num_len_extra = LENGTH_EXTRA[current_lit_symbol - 257]
                    lit_extra = payload_bits[i: i + num_len_extra]
                    i += num_len_extra  # Advance past the extra length bits

                    # 2. IMMEDIATELY start scanning for the distance symbol
                    current_dist_symbol = -1
                    for dist_length in range(1, 16):
                        current_dist_code = payload_bits[i: i + dist_length]
                        current_dist_symbol = dist_symbols.get(current_dist_code, -1)

                        if current_dist_symbol != -1:
                            i += dist_length  # Advance past distance Huffman code bits
                            break

                    # 3. Pull the distance extra bits
                    num_dist_extra = DISTANCE_EXTRA[current_dist_symbol]
                    dist_extra = payload_bits[i: i + num_dist_extra]
                    i += num_dist_extra  # Advance past extra distance bits

                    # 4. Pack and store the MatchEvent
                    events_list.append(MatchEvent(
                        current_lit_symbol,
                        lit_extra,
                        current_dist_symbol,
                        dist_extra
                    ))
                    break  # Break out of the original length loop to start next token

    return events_list