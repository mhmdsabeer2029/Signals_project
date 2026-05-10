from huffman_node import HuffmanNode

def test_huffman_node():
    # Test leaf node
    leaf = HuffmanNode(10, symbol=65)
    print(f"Leaf symbol: {leaf.symbol}, is_leaf: {leaf.is_leaf()}")
    assert leaf.is_leaf() == True, "Leaf node should be identified as leaf"

    # Test internal node
    left = HuffmanNode(5, symbol=66)
    right = HuffmanNode(5, symbol=67)
    internal = HuffmanNode(10, left=left, right=right)
    print(f"Internal symbol: {internal.symbol}, is_leaf: {internal.is_leaf()}")
    assert internal.is_leaf() == False, "Internal node should NOT be identified as leaf"

if __name__ == "__main__":
    try:
        test_huffman_node()
        print("Test passed!")
    except AssertionError as e:
        print(f"Test failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
