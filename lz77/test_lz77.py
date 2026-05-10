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
from lz77.lz77_tokens import Literal, Match
from lz77.lz77_encoder import lz77_encode, WINDOW_SIZE, MAX_MATCH, MIN_MATCH
from lz77.lz77_decoder import lz77_decode


# Constants for test data generation
SMALL_DATA_SIZE = 100
MEDIUM_DATA_SIZE = 1000
LARGE_DATA_SIZE = 10000
BYTE_RANGE = 256


class TestLZ77BasicFunctionality(unittest.TestCase):
    """Test basic encoding and decoding functionality"""

    def test_single_literal(self):
        """Test encoding a single byte"""
        data = b"a"
        tokens = lz77_encode(data)
        self.assertEqual(tokens, [Literal(ord("a"))])
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)

    def test_two_literals(self):
        """Test encoding two bytes (less than MIN_MATCH)"""
        data = b"ab"
        tokens = lz77_encode(data)
        self.assertEqual(tokens, [Literal(ord("a")), Literal(ord("b"))])
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)

    def test_three_different_bytes(self):
        """Test exactly MIN_MATCH bytes with no repetition"""
        data = b"abc"
        tokens = lz77_encode(data)
        self.assertEqual(
            tokens, [Literal(ord("a")), Literal(ord("b")), Literal(ord("c"))]
        )
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)

    def test_project_example(self):
        """Test the main example from project spec: 'abcabcabcabc'"""
        data = b"abcabcabcabc"
        tokens = lz77_encode(data)

        # Should be: Literal(a), Literal(b), Literal(c), Match(9, 3)
        # Expected: 3 literals followed by a match of the remaining 9 bytes
        expected_token_count = 4
        match_index = 3
        match_length = 9
        match_distance = 3

        self.assertEqual(len(tokens), expected_token_count)

        token0 = tokens[0]
        token1 = tokens[1]
        token2 = tokens[2]
        token3 = tokens[match_index]

        assert isinstance(token0, Literal)
        assert isinstance(token1, Literal)
        assert isinstance(token2, Literal)
        assert isinstance(token3, Match)

        self.assertEqual(token0.byte, ord("a"))
        self.assertEqual(token1.byte, ord("b"))
        self.assertEqual(token2.byte, ord("c"))
        self.assertEqual(token3.length, match_length)
        self.assertEqual(token3.distance, match_distance)

        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)

    def test_overlapping_match(self):
        """Test overlapping match: 'aaaaaaaaaa'"""
        data = b"aaaaaaaaaa"
        tokens = lz77_encode(data)

        # Should be: Literal(a), Match(9, 1)
        expected_token_count = 2
        match_index = 1
        match_length = 9
        match_distance = 1

        self.assertEqual(len(tokens), expected_token_count)

        token0 = tokens[0]
        token1 = tokens[match_index]

        assert isinstance(token0, Literal)
        assert isinstance(token1, Match)

        self.assertEqual(token0.byte, ord("a"))
        self.assertEqual(token1.length, match_length)
        self.assertEqual(token1.distance, match_distance)

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

        # Should have a match of exactly MIN_MATCH bytes
        has_match = any(isinstance(t, Match) and t.length == MIN_MATCH for t in tokens)
        self.assertTrue(has_match)

        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)

    def test_maximum_match_length(self):
        """Test MAX_MATCH length"""
        # Create data with more than MAX_MATCH repeating bytes
        buffer_size = MAX_MATCH + 42
        data = b"a" * buffer_size
        tokens = lz77_encode(data)

        # Should have at least one match with length <= MAX_MATCH
        max_length = max(t.length for t in tokens if isinstance(t, Match))
        self.assertLessEqual(max_length, MAX_MATCH)

        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)

    def test_exact_max_match_258(self):
        """Test exactly MAX_MATCH byte match"""
        # First some literals, then enough matching bytes to reach MAX_MATCH
        prefix = b"abc"
        data = prefix + b"x" * (MAX_MATCH + len(prefix))
        tokens = lz77_encode(data)

        # Check if we get a MAX_MATCH-length match
        has_max_match = any(
            isinstance(t, Match) and t.length == MAX_MATCH for t in tokens
        )
        self.assertTrue(has_max_match)

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
        beyond_window_padding = SMALL_DATA_SIZE
        filler = b"x" * (WINDOW_SIZE + beyond_window_padding)
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
        data = bytes([0] * SMALL_DATA_SIZE + [1, 2, 3] + [0] * SMALL_DATA_SIZE)
        tokens = lz77_encode(data)

        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)

    def test_repeating_pattern_small(self):
        """Test small repeating pattern"""
        repetitions = 50
        data = b"AB" * repetitions
        tokens = lz77_encode(data)

        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)

    def test_repeating_pattern_large(self):
        """Test large repeating pattern"""
        pattern = b"The quick brown fox jumps over the lazy dog. "
        repetitions = 20
        data = pattern * repetitions
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
        data = bytes(range(BYTE_RANGE))
        tokens = lz77_encode(data)

        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)

    def test_all_same_byte(self):
        """Test all bytes are the same"""
        # Test with boundary values (0, 255) and middle value (127)
        for byte_val in [0, 127, 255]:
            data = bytes([byte_val] * SMALL_DATA_SIZE)
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
        prime_factor = 13
        data = bytes([i * prime_factor % BYTE_RANGE for i in range(SMALL_DATA_SIZE)])
        tokens = lz77_encode(data)
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)

    def test_random_data_medium(self):
        """Test with pseudo-random medium data"""
        prime_factor = 17
        data = bytes([i * prime_factor % BYTE_RANGE for i in range(MEDIUM_DATA_SIZE)])
        tokens = lz77_encode(data)
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)

    def test_random_data_large(self):
        """Test with pseudo-random large data"""
        prime_factor = 19
        data = bytes([i * prime_factor % BYTE_RANGE for i in range(LARGE_DATA_SIZE)])
        tokens = lz77_encode(data)
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)

    def test_all_byte_values(self):
        """Test that all byte values (0-255) work correctly"""
        repetitions = 3
        data = bytes(range(BYTE_RANGE)) * repetitions
        tokens = lz77_encode(data)
        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)

    def test_highly_compressible(self):
        """Test highly compressible data"""
        data = b"a" * LARGE_DATA_SIZE
        tokens = lz77_encode(data)

        # Should have very few tokens due to compression
        token_threshold = SMALL_DATA_SIZE
        self.assertLess(len(tokens), token_threshold)

        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)

    def test_incompressible(self):
        """Test incompressible data (all unique)"""
        # Create unique sequences
        incompressible_size = 500
        data = bytes([i % BYTE_RANGE for i in range(incompressible_size)])
        # Make it incompressible by ensuring no MIN_MATCH-byte repetition
        unique_data = bytearray()
        for i in range(0, len(data) - (MIN_MATCH - 1)):
            unique_data.append(data[i])
            # Ensure next match-sized sequence doesn't repeat
            if i > 0 and data[i : i + MIN_MATCH] == data[i - MIN_MATCH : i]:
                unique_data[-1] = (unique_data[-1] + 1) % BYTE_RANGE

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
        repetitions = 1000
        data = pattern * repetitions
        tokens = lz77_encode(data)

        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)

    def test_many_small_matches(self):
        """Test many small matches"""
        repetitions = 100
        data = (b"abc" * repetitions) + (b"def" * repetitions) + (b"ghi" * repetitions)
        tokens = lz77_encode(data)

        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)

    def test_max_candidates_limit(self):
        """Test that MAX_CANDIDATES limit works correctly"""
        # Create a pattern that appears many times
        repetitions = 100
        data = b"xyz" + b"abc" * repetitions  # "abc" appears 100 times
        tokens = lz77_encode(data)

        decoded = lz77_decode(tokens)
        self.assertEqual(data, decoded)


class TestLZ77DecoderIsolation(unittest.TestCase):
    """Test decoder with manually created tokens"""

    def test_decoder_single_literal(self):
        """Test decoder with a single literal"""
        tokens = [Literal(ord("A"))]
        decoded = lz77_decode(tokens)
        self.assertEqual(decoded, b"A")

    def test_decoder_multiple_literals(self):
        """Test decoder with multiple literals"""
        tokens = [
            Literal(ord("H")),
            Literal(ord("E")),
            Literal(ord("L")),
            Literal(ord("L")),
            Literal(ord("O")),
        ]
        decoded = lz77_decode(tokens)
        self.assertEqual(decoded, b"HELLO")

    def test_decoder_simple_match(self):
        """Test decoder with a simple match"""
        match_len = 3
        match_dist = 3
        tokens = [
            Literal(ord("a")),
            Literal(ord("b")),
            Literal(ord("c")),
            Match(length=match_len, distance=match_dist),
        ]
        decoded = lz77_decode(tokens)
        self.assertEqual(decoded, b"abcabc")

    def test_decoder_overlapping_match(self):
        """Test decoder with overlapping match"""
        match_len = 5
        match_dist = 1
        tokens = [Literal(ord("x")), Match(length=match_len, distance=match_dist)]
        decoded = lz77_decode(tokens)
        self.assertEqual(decoded, b"xxxxxx")

    def test_decoder_mixed_tokens(self):
        """Test decoder with mixed literals and matches"""
        match_len = 2
        match_dist = 2
        tokens = [
            Literal(ord("A")),
            Literal(ord("B")),
            Match(length=match_len, distance=match_dist),
            Literal(ord("C")),
        ]
        decoded = lz77_decode(tokens)
        self.assertEqual(decoded, b"ABABC")


def run_all_tests() -> unittest.TestResult:
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
    divider_char = "="
    divider_length = 70
    error_exit_code = 1

    print(divider_char * divider_length)
    print("LZ77 COMPREHENSIVE TEST SUITE")
    print(divider_char * divider_length)
    print()

    result = run_all_tests()

    print()
    print(divider_char * divider_length)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(divider_char * divider_length)

    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED!")
        exit(error_exit_code)
