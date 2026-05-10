import heapq

def symbol_counter(symbols):
    literal_dict = {}
    distance_dict = {}
    for  symbol in symbols:
        if isinstance(symbol, int):
            literal_dict[symbol] = literal_dict.get(symbol, 0) + 1
        elif isinstance(symbol, tuple):
            literal_dict[symbol[0]] = literal_dict.get(symbol[0] , 0) + 1
            distance_dict[symbol[2]] = distance_dict.get(symbol[2] , 0) + 1
    return literal_dict, distance_dict
