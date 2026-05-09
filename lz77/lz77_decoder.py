# from list of(literals or matches) ---> original bytes
from .lz77_tokens import *
from .lz77_encoder import *


class LZ77Decoder:
    def decode(self, tokens: List[lz77Token]) -> bytes: # type: ignore
        output = bytearray()
        # bytearray() is an empty mutable byte list

        # 97 98 99 match(3 9)
        # abcabcabc
        for token in tokens:
            if isinstance(token,Literal):
                output.append(token.byte)
            elif isinstance(token,Match):
                # go back from where you are recently in output list of bytes
                start = len(output) - token.distance
                for i in range(token.length):
                    output.append(output[start])
                    start+=1
        
        return output
    

def lz77_decode(tokens: List[lz77Token]) -> bytes: # type: ignore
    # as A wrapper class as i don't want to get any extra info other than the tokens
    return LZ77Decoder().decode(tokens)



# 012 345 678 91011
# abc abc abc abc
# abc[3 9]
#(97)(98)(99)[3 9]