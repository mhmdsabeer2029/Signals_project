from __future__ import annotations
from lz77.lz77_tokens import Literal, Match, lz77Token


class LZ77Decoder:
    """Decodes a list of LZ77 tokens back into the original byte sequence."""

    def decode(self, tokens: list[lz77Token]) -> bytearray:
        output = bytearray()
        # bytearray() is an empty mutable byte list

        for token in tokens:
            if isinstance(token, Literal):
                output.append(token.byte)

            elif isinstance(token, Match):
                # go back from where you are recently in output list of bytes
                start = len(output) - token.distance
                for _ in range(token.length):
                    output.append(output[start])
                    start += 1
            
            else:
                # This case should be unreachable with correct typing
                raise TypeError(f"Unknown token type: {type(token)}")

        return output


def lz77_decode(tokens: list[lz77Token]) -> bytearray:
    """Wrapper function to decode a list of LZ77 tokens."""
    return LZ77Decoder().decode(tokens)
