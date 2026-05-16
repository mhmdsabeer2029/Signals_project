from lz77.lz77_tokens import *
from typing import List
from .DEFLATE_Event import *

# 999999 is dummy value added for the special case in looking for the index of base where if index is len(length_base)-1 cuz u are looking for next index first and comparing it with current token.length value
_LENGTH_BASE = [ 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83, 99, 115 , 131 , 163 , 195 , 227 , 258, 99999999 ] 
_LENGTH_EXTRA = [ 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0 ]
_DISTANCE_BASE = [ 1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129 , 193 , 257 , 385 , 513 , 769 , 1025 , 1537 , 2049 , 3073 , 4097 , 6145 , 8193 , 12289 , 16385 , 24577, 99999999 ]
_DISTANCE_EXTRA = [ 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13 ]

class Stage2Translator:
    """
        this class should get a lz77Tokens list when initialized and used just call translate function to get the events list
    """
    def __init__(self, tokens: List[lz77Token]):
        self.tokens = tokens
        self.events: List[deflateEvent] = []

    # Main function that does the formatting using the 3 helper functions below 
    def translate(self) -> List[deflateEvent]:
        for token in self.tokens:
            # for a Literal call the function that would auto append that as a LiteralEvent to the events list
            if isinstance(token, Literal):
                self._process_literal( token )

            # for a Match call both getter function to get the 4 values with which we create new MatchEvent object then append that object into events list
            elif isinstance(token, Match):
                eventLengthBase, lengthExtraBits    = self._get_length_data( token.length)
                eventDistanceBase, distancExtraBits = self._get_distance_data( token.distance)
                
                self.events.append( MatchEvent(eventLengthBase, lengthExtraBits, eventDistanceBase, distancExtraBits) )

            #safty: if event didn't match non then return Node and print invalid
            else :
                print("Invalid Tokens stream passed!!") 
                return None
        # add the EndEvent event to the list after all tokens have been processed
        self.events.append( EndEvent() )
        return self.events
    
    #private helper function 1: Literal to EventLiteral
    def _process_literal(self, token: Literal) -> None:
        ''' Handle pure Literal traslator'''
        self.events.append( LiteralEvent( token.byte ) )

    #private helper function 2: length to tuple of (base, extrabits)
    def _get_length_data(self, length:int ) -> tuple[int, str]:
        # just an extra validation for length 
        if length < 3 or length > 258:
            raise ValueError(f"CRITICAL: Match length {length} violates DEFLATE limits (3-258)")
        # loop throw _LENGTH_BASE array to find base and extra bits
        for i in range(0, len(_LENGTH_BASE)):
            #find index of base for token.length we are dealing with
            if _LENGTH_BASE[i] > length:
                idx = i - 1
                eventLengthBase: int = 257 + idx
                #after finding base, get the extra bits
                extraBits:str = ""  #this is default value for if num of extra bits = 0 since if condition will be false.
                if _LENGTH_EXTRA[idx] > 0:
                    # those 3 lines just transform extra bits value into binary string, <<I don't know the functinos used + don't care>>
                    val = length - _LENGTH_BASE[idx]
                    extraBits = bin(val)[2:].zfill(_LENGTH_EXTRA[idx])
                return eventLengthBase, extraBits
        #just if func didn't return anything till here then we length is greater that all values of _LENGTH_BASE so value of lenght is invalid so
        raise ValueError("Length out of bounds")
    
    #private helper function 3: distance to tuple of (base, extraBits)
    def _get_distance_data(self, distance:int) -> tuple[int, str]:
        # just an extra validation for length 
        if distance < 1 or distance > 32768:
            raise ValueError(f"CRITICAL: Match length {distance} violates DEFLATE limits (1-32768)")
        
        for i in range(0, len(_DISTANCE_BASE)):
            #find index of base for token.distance we are dealing with
            if _DISTANCE_BASE[i] > distance:
                idx = i - 1
                eventDistanceBase:int = idx  
                #after finding base, get extra bits
                extraBits:str = "" #this is default value for if num of extra bits = 0 since if condition will be false.
                if _DISTANCE_EXTRA[idx] > 0:
                    # calc value extra bits will be representing
                    val = distance - _DISTANCE_BASE[idx]
                    # transform extra bits value into binary string, <<I don't know the functinon used + I don't care>> 
                    extraBits = bin(val)[2:].zfill(_DISTANCE_EXTRA[idx])
                return eventDistanceBase, extraBits
        #just if func didn't return anything till here then we distance is greater that all values of _DISTANCE_BASE so value of lenght is invalid so
        raise ValueError("Distance out of bounds")