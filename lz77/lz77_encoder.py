#get tokens
from lz77.lz77_tokens import lz77Token
from typing import List,Dict
# Constants for LZ77 encoding
WINDOW_SIZE=32768
MIN_MATCH=3
MAX_MATCH=258
MAX_CANDIDATES=64
class LZ77Encoder:
    # using Sliding Window

    #constructor for the LZ77Encoder class
    def __init__(self):
        #dictionary has key(bytes) and value(list of positions where the byte occurs in the input data)
        # as HashMap<key,value>
        self.table: Dict[bytes, List[int]] = {}

    def encode(self, data: bytes) -> List[lz77Token]:
        # convert the input bytes to a list of literals or matches
        tokens=[]
        i=0
        n=len(data)
        while i<n:
            # abcdef
            # do we have 2 bytes or less left? YES --> append in list as Literal ,as the window isn't completed
            if n-i < MIN_MATCH:
                tokens.append(Literal(data[i]))
                i+=1
                continue
            #O.W 3 bytes or more remaining
            #constructing the 3-chunk bytes for our sliding window
            key=data[i:i+3]
            #### emit a Match if key is found in table ####

            # abcabcabcabc --> [0,3,6,9] b"abc"
            # 0 2
            # selecting the best lenght and distance by comparing while keeping the longest match, Draw--> select smaller distance 
            best_Match_length=0
            best_Match_distance=0
            if key in self.table:
                candidates = self.table[key]
                checked_Candidates=0
                # checking form newest to oldest to get the most recent occurenence for smaller distance :)
                for candidate in reversed(candidates): # [9,6,3,0]
                    if checked_Candidates >= MAX_CANDIDATES:
                        break
                    distance = i-candidate
                    if distance>WINDOW_SIZE: 
                        break # actually older candidates will very far 
                    match_len=0
                    # the window is restricted to the max match (32768) and n-i (the last few bytes)  
                    max_match_length=min(MAX_MATCH,n-i)
                
                    while (match_len<max_match_length) and (data[i+match_len]==data[candidate+match_len]):
                        # while -> a b c   a b c
                        #          | | |   | | |
                        #          0 1 2   7 8 9  comparing for each , if true --> jump to next
                        match_len+=1
                    # keeping the longest match
                    if (match_len>best_Match_length) or ( match_len==best_Match_length and distance<best_Match_distance ):
                        best_Match_length = match_len
                        best_Match_distance=distance
                    checked_Candidates+=1
                    # abcabcabcabc
                # after getting the best candidate and the length of the window is considerable --> append a match to the table
                if best_Match_length >=MIN_MATCH:
                    tokens.append(Match(best_Match_length,best_Match_distance))
                    # insert all the positions covered by the match
                    for pos in range(i, i+best_Match_length):
                        if pos+3 <= n:
                            self.insert_position(data,pos)
                    i+=best_Match_length
                else:  # KEY EXISTS BUT NO GOOD MATCH
                    tokens.append(Literal(data[i]))
                    self.insert_position(data, i)
                    i += 1
            ### emit a Literal if key is not found in the table
            else:
                tokens.append(Literal(data[i]))
                self.insert_position(data,i)
                i+=1
        return tokens
    
    def insert_position(self,data:bytes,pos:int):
        if pos+ 3 <=len(data):
            key = data[pos:pos+3]
            if key not in self.table:
                self.table[key] = []
            self.table[key].append(pos)

def lz77_encode(data: bytes) -> List[lz77Token]:
    return LZ77Encoder().encode(data)