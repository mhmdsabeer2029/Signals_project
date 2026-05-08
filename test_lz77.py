"""
Comprehensive Unit Tests for LZ77 Encoder and Decoder

This test suite covers:
- Basic functionality
- Edge cases
- Boundary conditions
- Real-world scenarios
- Round-trip verification
"""

import unittest
from lz77_tokens import Literal, Match
from lz77_encoder import lz77_encode, WINDOW_SIZE, MIN_MATCH, MAX_MATCH
from lz77_decoder import lz77_decode


class TestLZ77BasicFunctionality(unittest.TestCase):
    """Test basic encoding and decoding functionality"""
    
    def test_single_literal(self):
        """Test encoding a single byte"""
        data = b"a"
        tokens = lz77_encode(data)
        self.assertEqual(tokens, [Literal(97)])
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_two_literals(self):
        """Test encoding two bytes (less than MIN_MATCH)"""
        data = b"ab"
        tokens = lz77_encode(data)
        self.assertEqual(tokens, [Literal(97), Literal(98)])
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_three_different_bytes(self):
        """Test exactly MIN_MATCH bytes with no repetition"""
        data = b"abc"
        tokens = lz77_encode(data)
        self.assertEqual(tokens, [Literal(97), Literal(98), Literal(99)])
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_project_example(self):
        """Test the main example from project spec: 'abcabcabcabc'"""
        data = b"abcabcabcabc"
        tokens = lz77_encode(data)
        
        # Should be: Literal(a), Literal(b), Literal(c), Match(9, 3)
        self.assertEqual(len(tokens), 4)
        self.assertIsInstance(tokens[0], Literal)
        self.assertIsInstance(tokens[1], Literal)
        self.assertIsInstance(tokens[2], Literal)
        self.assertIsInstance(tokens[3], Match)
        
        self.assertEqual(tokens[0].byte, 97)  # 'a'
        self.assertEqual(tokens[1].byte, 98)  # 'b'
        self.assertEqual(tokens[2].byte, 99)  # 'c'
        self.assertEqual(tokens[3].length, 9)
        self.assertEqual(tokens[3].distance, 3)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_overlapping_match(self):
        """Test overlapping match: 'aaaaaaaaaa'"""
        data = b"aaaaaaaaaa"
        tokens = lz77_encode(data)
        
        # Should be: Literal(a), Match(9, 1)
        self.assertEqual(len(tokens), 2)
        self.assertIsInstance(tokens[0], Literal)
        self.assertIsInstance(tokens[1], Match)
        
        self.assertEqual(tokens[0].byte, 97)
        self.assertEqual(tokens[1].length, 9)
        self.assertEqual(tokens[1].distance, 1)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)


class TestLZ77EdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def test_empty_input(self):
        """Test empty byte string"""
        data = b""
        tokens = lz77_encode(data)
        self.assertEqual(tokens, [])
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_minimum_match_length(self):
        """Test exact MIN_MATCH length match"""
        data = b"xyzxyz"
        tokens = lz77_encode(data)
        
        # Should have a match of exactly 3 bytes
        has_match = any(isinstance(t, Match) and t.length == 3 for t in tokens)
        self.assertTrue(has_match)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_maximum_match_length(self):
        """Test MAX_MATCH length (258 bytes)"""
        # Create data with 258+ repeating bytes
        data = b"a" * 300
        tokens = lz77_encode(data)
        
        # Should have at least one match with length <= MAX_MATCH
        max_length = max(t.length for t in tokens if isinstance(t, Match))
        self.assertLessEqual(max_length, MAX_MATCH)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_exact_max_match_258(self):
        """Test exactly 258 byte match"""
        # First 3 literals, then 258 matching bytes
        data = b"abc" + b"x" * 261
        tokens = lz77_encode(data)
        
        # Check if we get a 258-length match
        has_258_match = any(isinstance(t, Match) and t.length == 258 for t in tokens)
        self.assertTrue(has_258_match)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_no_matches_all_unique(self):
        """Test data with no repetition (all literals)"""
        data = b"abcdefghijklmnopqrstuvwxyz0123456789"
        tokens = lz77_encode(data)
        
        # All should be literals
        all_literals = all(isinstance(t, Literal) for t in tokens)
        self.assertTrue(all_literals)
        self.assertEqual(len(tokens), len(data))
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_match_at_window_boundary(self):
        """Test match at exactly WINDOW_SIZE distance"""
        # Create data where a pattern repeats at WINDOW_SIZE distance
        pattern = b"test"
        filler = b"x" * (WINDOW_SIZE - len(pattern))
        data = pattern + filler + pattern
        
        tokens = lz77_encode(data)
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_match_beyond_window(self):
        """Test that matches beyond WINDOW_SIZE are not found"""
        # Create pattern, then more than WINDOW_SIZE bytes, then pattern again
        pattern = b"test"
        filler = b"x" * (WINDOW_SIZE + 100)
        data = pattern + filler + pattern
        
        tokens = lz77_encode(data)
        
        # The second occurrence of "test" should be literals (no match possible)
        # because the first occurrence is beyond WINDOW_SIZE
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)


class TestLZ77MatchSelection(unittest.TestCase):
    """Test match selection rules"""
    
    def test_longest_match_preferred(self):
        """Test that longest match is selected"""
        data = b"abcabcdabcde"
        tokens = lz77_encode(data)
        
        # Should prefer longer matches over shorter ones
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_smaller_distance_on_tie(self):
        """Test that smaller distance is chosen when lengths are equal"""
        # Create scenario where same pattern appears twice at different distances
        data = b"xyzABCxyzABCxyzABC"
        tokens = lz77_encode(data)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_greedy_matching(self):
        """Test greedy matching behavior"""
        data = b"ababababab"
        tokens = lz77_encode(data)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)


class TestLZ77RealWorldScenarios(unittest.TestCase):
    """Test real-world data patterns"""
    
    def test_repeated_word(self):
        """Test text with repeated words"""
        data = b"hello world hello world hello world"
        tokens = lz77_encode(data)
        
        # Should find matches for "hello world"
        has_matches = any(isinstance(t, Match) for t in tokens)
        self.assertTrue(has_matches)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_json_like_structure(self):
        """Test JSON-like repeated structure"""
        data = b'{"name":"John","age":30},{"name":"Jane","age":25},{"name":"Bob","age":35}'
        tokens = lz77_encode(data)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_binary_data_zeros(self):
        """Test binary data with many zeros"""
        data = bytes([0] * 100 + [1, 2, 3] + [0] * 100)
        tokens = lz77_encode(data)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_repeating_pattern_small(self):
        """Test small repeating pattern"""
        data = (b"AB" * 50)
        tokens = lz77_encode(data)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_repeating_pattern_large(self):
        """Test large repeating pattern"""
        pattern = b"The quick brown fox jumps over the lazy dog. "
        data = pattern * 20
        tokens = lz77_encode(data)
        
        # Should find significant compression
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_mixed_content(self):
        """Test mixed compressible and incompressible content"""
        data = b"aaaaaaaaaa" + b"abcdefghij" + b"bbbbbbbbbb" + b"klmnopqrst"
        tokens = lz77_encode(data)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)


class TestLZ77SpecialPatterns(unittest.TestCase):
    """Test special patterns and corner cases"""
    
    def test_alternating_bytes(self):
        """Test alternating byte pattern"""
        data = b"ababababababababab"
        tokens = lz77_encode(data)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_incrementing_bytes(self):
        """Test incrementing byte sequence"""
        data = bytes(range(256))
        tokens = lz77_encode(data)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_all_same_byte(self):
        """Test all bytes are the same"""
        for byte_val in [0, 127, 255]:
            data = bytes([byte_val] * 100)
            tokens = lz77_encode(data)
            decoded = lz77_decode(tokens)
            self.assertEqual(data, decoded)
    
    def test_nested_repetition(self):
        """Test nested repetition pattern"""
        data = b"((()))((()))((()))"
        tokens = lz77_encode(data)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_partial_overlap(self):
        """Test partial overlapping patterns"""
        data = b"abcdefabcxyzabc"
        tokens = lz77_encode(data)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)


class TestLZ77DataIntegrity(unittest.TestCase):
    """Test data integrity and round-trip conversion"""
    
    def test_random_data_small(self):
        """Test with pseudo-random small data"""
        # Use a deterministic sequence for reproducibility
        data = bytes([i * 13 % 256 for i in range(100)])
        tokens = lz77_encode(data)
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_random_data_medium(self):
        """Test with pseudo-random medium data"""
        data = bytes([i * 17 % 256 for i in range(1000)])
        tokens = lz77_encode(data)
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_random_data_large(self):
        """Test with pseudo-random large data"""
        data = bytes([i * 19 % 256 for i in range(10000)])
        tokens = lz77_encode(data)
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_all_byte_values(self):
        """Test that all byte values (0-255) work correctly"""
        data = bytes(range(256)) * 3
        tokens = lz77_encode(data)
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_highly_compressible(self):
        """Test highly compressible data"""
        data = b"a" * 10000
        tokens = lz77_encode(data)
        
        # Should have very few tokens due to compression
        self.assertLess(len(tokens), 100)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_incompressible(self):
        """Test incompressible data (all unique)"""
        # Create unique sequences
        data = bytes([i % 256 for i in range(500)])
        # Make it incompressible by ensuring no 3-byte repetition
        unique_data = bytearray()
        for i in range(0, len(data) - 2):
            unique_data.append(data[i])
            # Ensure next 3 bytes don't repeat
            if i > 0 and data[i:i+3] == data[i-3:i]:
                unique_data[-1] = (unique_data[-1] + 1) % 256
        
        data = bytes(unique_data)
        tokens = lz77_encode(data)
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)


class TestLZ77Performance(unittest.TestCase):
    """Test performance-related aspects"""
    
    def test_long_match_sequence(self):
        """Test very long sequence of matches"""
        # Pattern that repeats many times
        pattern = b"pattern"
        data = pattern * 1000
        tokens = lz77_encode(data)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_many_small_matches(self):
        """Test many small matches"""
        data = (b"abc" * 100) + (b"def" * 100) + (b"ghi" * 100)
        tokens = lz77_encode(data)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)
    
    def test_max_candidates_limit(self):
        """Test that MAX_CANDIDATES limit works correctly"""
        # Create a pattern that appears many times
        data = b"xyz" + b"abc" * 100  # "abc" appears 100 times
        tokens = lz77_encode(data)
        
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)


class TestLZ77DecoderIsolation(unittest.TestCase):
    """Test decoder with manually created tokens"""
    
    def test_decoder_single_literal(self):
        """Test decoder with a single literal"""
        tokens = [Literal(65)]
        decoded = lz77_decode(tokens)
        self.assertEqual(decoded, b"A")
    
    def test_decoder_multiple_literals(self):
        """Test decoder with multiple literals"""
        tokens = [Literal(72), Literal(69), Literal(76), Literal(76), Literal(79)]
        decoded = lz77_decode(tokens)
        self.assertEqual(decoded, b"HELLO")
    
    def test_decoder_simple_match(self):
        """Test decoder with a simple match"""
        tokens = [Literal(97), Literal(98), Literal(99), Match(length=3, distance=3)]
        decoded = lz77_decode(tokens)
        self.assertEqual(decoded, b"abcabc")
    
    def test_decoder_overlapping_match(self):
        """Test decoder with overlapping match"""
        tokens = [Literal(120), Match(length=5, distance=1)]
        decoded = lz77_decode(tokens)
        self.assertEqual(decoded, b"xxxxxx")
    
    def test_decoder_mixed_tokens(self):
        """Test decoder with mixed literals and matches"""
        tokens = [
            Literal(65),  # 'A'
            Literal(66),  # 'B'
            Match(length=2, distance=2),  # Copy "AB"
            Literal(67),  # 'C'
        ]
        decoded = lz77_decode(tokens)
        self.assertEqual(decoded, b"ABABC")


def run_all_tests():
    """Run all test suites"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestLZ77BasicFunctionality))
    suite.addTests(loader.loadTestsFromTestCase(TestLZ77EdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestLZ77MatchSelection))
    suite.addTests(loader.loadTestsFromTestCase(TestLZ77RealWorldScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestLZ77SpecialPatterns))
    suite.addTests(loader.loadTestsFromTestCase(TestLZ77DataIntegrity))
    suite.addTests(loader.loadTestsFromTestCase(TestLZ77Performance))
    suite.addTests(loader.loadTestsFromTestCase(TestLZ77DecoderIsolation))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    print("="*70)
    print("LZ77 COMPREHENSIVE TEST SUITE")
    print("="*70)
    print()
    
    result = run_all_tests()
    
    print()
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED!")
        exit(1)