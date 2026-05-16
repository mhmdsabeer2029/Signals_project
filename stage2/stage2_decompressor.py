from lz77.lz77_tokens import *
from stage2.DEFLATE_Event import *
from typing import List

_LENGTH_BASE = [ 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83, 99, 115 , 131 , 163 , 195 , 227 , 258, 99999999 ] 
_DISTANCE_BASE = [ 1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129 , 193 , 257 , 385 , 513 , 769 , 1025 , 1537 , 2049 , 3073 , 4097 , 6145 , 8193 , 12289 , 16385 , 24577, 99999999 ]
class s2Decompressor:
    def __init__(self, events: deflateEvent ):
        self.events = events
        self.tokens: List[lz77Token] = []


    #Main function translates event stream into tokens stream
    def decopress(self) -> List[lz77Token]:
        #loop throgh events array
        for event in self.events:
            # if current event is a literal
            if isinstance(event, LiteralEvent):
                self.tokens.append( Literal(event.symbol) )
            
            #if current event is a matchEvent
            elif isinstance(event, MatchEvent):
                #evaluate matchToken distance and lenght values
                    #step1: get extra bits values
                        #! int(ValueString, BaseOfValueString) reverts the string from string rep binary to int rep decimal value
                        if len(event.lengthExtraBits) ==0  : lengthExtraBitsValue = 0
                        else: lengthExtraBitsValue   = int(event.lengthExtraBits, 2)
                        if len(event.distanceExtraBits) ==0: distanceExtraBitsValue =0
                        else: distanceExtraBitsValue = int(event.distanceExtraBits, 2)
                    #step2: get index of base value in the bases arrays
                        lengthBaseIdx   = event.length - 257
                        distacneBaseIdx = event.distance - 0
                    #step3: get actual values of bases from bases arrays
                        lengthBaseValue  = _LENGTH_BASE[lengthBaseIdx]
                        distacneBaseVale = _DISTANCE_BASE[distacneBaseIdx]
                    #step4: calculate final value of matchtoken length and distance
                        tokenLengthValue   = lengthBaseValue  + lengthExtraBitsValue
                        tokenDisatnceValue = distacneBaseVale + distanceExtraBitsValue
                #Append the MatchToekn object into tokens List
                        self.tokens.append( Match(tokenLengthValue, tokenDisatnceValue) )
            
            #if current event is End event then we reached the end
            elif isinstance(event, EndEvent):
                return self.tokens
            
            #safty: if event didn't match non then return Node and print invalid
            else :
                print("Invalid Events stream passed!!") 
                return None

        #*NOTE: this line if for case of empty events stream passed so the program won't break
        #*also this is the only case we go down here cuz if stream is corrupted we catch that in the for loop
        return self.tokens
