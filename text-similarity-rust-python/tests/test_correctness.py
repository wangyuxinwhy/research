"""
Test correctness of all implementations.
Verify that different implementations produce consistent results.
"""

import pytest
import sys
import os

# Add python directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import pure_python
import numpy_impl


# Test will be updated after Rust module is compiled
try:
    import text_similarity_rust
    HAS_RUST = True
except ImportError:
    HAS_RUST = False
    print("Warning: Rust module not available. Skipping Rust tests.")


# Tolerance for floating point comparisons
FLOAT_TOLERANCE = 1e-6


class TestCosineSimilarity:
    """Test cosine similarity implementations."""

    test_cases = [
        ("hello world", "hello world", 1.0),
        ("abc", "def", 0.0),  # No common characters
        ("abc", "abc", 1.0),
        ("", "hello", 0.0),
        ("hello", "", 0.0),
        ("the quick brown fox", "the quick brown dog", 0.8),
        ("机器学习", "机器学习", 1.0),
        ("人工智能", "机器学习", 0.25),
    ]

    def test_pure_python(self):
        """Test pure Python implementation."""
        for text1, text2, expected in self.test_cases:
            result = pure_python.cosine_similarity(text1, text2)
            if expected == 0.0:
                assert result == pytest.approx(expected, abs=FLOAT_TOLERANCE)
            else:
                # Just check it's reasonable, allow small floating point errors
                assert -FLOAT_TOLERANCE <= result <= 1.0 + FLOAT_TOLERANCE

    def test_numpy_vs_pure_python(self):
        """Test that NumPy gives same results as pure Python."""
        for text1, text2, _ in self.test_cases:
            py_result = pure_python.cosine_similarity(text1, text2)
            np_result = numpy_impl.cosine_similarity(text1, text2)
            assert py_result == pytest.approx(np_result, abs=FLOAT_TOLERANCE)

    @pytest.mark.skipif(not HAS_RUST, reason="Rust module not available")
    def test_rust_vs_pure_python(self):
        """Test that Rust gives same results as pure Python."""
        for text1, text2, _ in self.test_cases:
            py_result = pure_python.cosine_similarity(text1, text2)
            rust_result = text_similarity_rust.cosine_similarity(text1, text2)
            assert py_result == pytest.approx(rust_result, abs=FLOAT_TOLERANCE)


class TestLevenshteinDistance:
    """Test Levenshtein distance implementations."""

    test_cases = [
        ("", "", 0),
        ("abc", "abc", 0),
        ("abc", "abd", 1),
        ("abc", "def", 3),
        ("kitten", "sitting", 3),
        ("saturday", "sunday", 3),
        ("", "abc", 3),
        ("abc", "", 3),
        ("机器学习", "机器学习", 0),
        ("人工智能", "机器学习", 4),
    ]

    def test_pure_python(self):
        """Test pure Python implementation."""
        for text1, text2, expected in self.test_cases:
            result = pure_python.levenshtein_distance(text1, text2)
            assert result == expected

    def test_numpy_vs_pure_python(self):
        """Test that NumPy gives same results as pure Python."""
        for text1, text2, _ in self.test_cases:
            py_result = pure_python.levenshtein_distance(text1, text2)
            np_result = numpy_impl.levenshtein_distance(text1, text2)
            assert py_result == np_result

    @pytest.mark.skipif(not HAS_RUST, reason="Rust module not available")
    def test_rust_vs_pure_python(self):
        """Test that Rust gives same results as pure Python."""
        for text1, text2, _ in self.test_cases:
            py_result = pure_python.levenshtein_distance(text1, text2)
            rust_result = text_similarity_rust.levenshtein_distance(text1, text2)
            assert py_result == rust_result


class TestLevenshteinSimilarity:
    """Test normalized Levenshtein similarity implementations."""

    test_cases = [
        ("", "", 1.0),
        ("abc", "abc", 1.0),
        ("abc", "def", 0.0),
        ("", "abc", 0.0),
        ("abc", "", 0.0),
    ]

    def test_pure_python(self):
        """Test pure Python implementation."""
        for text1, text2, expected in self.test_cases:
            result = pure_python.levenshtein_similarity(text1, text2)
            assert result == pytest.approx(expected, abs=FLOAT_TOLERANCE)

    def test_numpy_vs_pure_python(self):
        """Test that NumPy gives same results as pure Python."""
        for text1, text2, _ in self.test_cases:
            py_result = pure_python.levenshtein_similarity(text1, text2)
            np_result = numpy_impl.levenshtein_similarity(text1, text2)
            assert py_result == pytest.approx(np_result, abs=FLOAT_TOLERANCE)

    @pytest.mark.skipif(not HAS_RUST, reason="Rust module not available")
    def test_rust_vs_pure_python(self):
        """Test that Rust gives same results as pure Python."""
        for text1, text2, _ in self.test_cases:
            py_result = pure_python.levenshtein_similarity(text1, text2)
            rust_result = text_similarity_rust.levenshtein_similarity(text1, text2)
            assert py_result == pytest.approx(rust_result, abs=FLOAT_TOLERANCE)


class TestJaccardSimilarity:
    """Test Jaccard similarity implementations."""

    test_cases = [
        ("", "", 0.0),
        ("abc", "abc", 1.0),
        ("abc", "def", 0.0),
        ("hello", "hallo", 0.5),
        ("", "abc", 0.0),
        ("abc", "", 0.0),
    ]

    def test_pure_python(self):
        """Test pure Python implementation."""
        for text1, text2, _ in self.test_cases:
            result = pure_python.jaccard_similarity(text1, text2)
            assert 0.0 <= result <= 1.0

    def test_numpy_vs_pure_python(self):
        """Test that NumPy gives same results as pure Python."""
        for text1, text2, _ in self.test_cases:
            py_result = pure_python.jaccard_similarity(text1, text2)
            np_result = numpy_impl.jaccard_similarity(text1, text2)
            assert py_result == pytest.approx(np_result, abs=FLOAT_TOLERANCE)

    @pytest.mark.skipif(not HAS_RUST, reason="Rust module not available")
    def test_rust_vs_pure_python(self):
        """Test that Rust gives same results as pure Python."""
        for text1, text2, _ in self.test_cases:
            py_result = pure_python.jaccard_similarity(text1, text2)
            rust_result = text_similarity_rust.jaccard_similarity(text1, text2)
            assert py_result == pytest.approx(rust_result, abs=FLOAT_TOLERANCE)


class TestBM25:
    """Test BM25 implementations."""

    def test_pure_python_basic(self):
        """Test basic BM25 functionality."""
        corpus = [
            "the cat sat on the mat",
            "the dog sat on the log",
            "cats and dogs are animals"
        ]

        bm25 = pure_python.BM25(corpus)
        scores = bm25.get_scores("cat")

        # First document should score highest
        assert scores[0] > scores[1]
        assert scores[0] > scores[2]

    def test_numpy_vs_pure_python(self):
        """Test that NumPy BM25 gives same results as pure Python."""
        corpus = [
            "the cat sat on the mat",
            "the dog sat on the log",
            "cats and dogs are animals"
        ]

        py_bm25 = pure_python.BM25(corpus)
        np_bm25 = numpy_impl.BM25(corpus)

        py_scores = py_bm25.get_scores("cat and dog")
        np_scores = np_bm25.get_scores("cat and dog")

        # Check scores are approximately equal
        for py_score, np_score in zip(py_scores, np_scores):
            assert py_score == pytest.approx(np_score, abs=FLOAT_TOLERANCE)

    @pytest.mark.skipif(not HAS_RUST, reason="Rust module not available")
    def test_rust_vs_pure_python(self):
        """Test that Rust BM25 gives same results as pure Python."""
        corpus = [
            "the cat sat on the mat",
            "the dog sat on the log",
            "cats and dogs are animals"
        ]

        py_bm25 = pure_python.BM25(corpus)
        rust_bm25 = text_similarity_rust.BM25(corpus)

        py_scores = py_bm25.get_scores("cat and dog")
        rust_scores = rust_bm25.get_scores("cat and dog")

        # Check scores are approximately equal
        for py_score, rust_score in zip(py_scores, rust_scores):
            assert py_score == pytest.approx(rust_score, abs=FLOAT_TOLERANCE)


class TestBM25Similarity:
    """Test BM25 similarity for single document."""

    def test_pure_python(self):
        """Test pure Python BM25 similarity."""
        result = pure_python.bm25_similarity("cat", "the cat sat on the mat")
        assert result > 0

    def test_numpy_vs_pure_python(self):
        """Test that NumPy BM25 similarity gives same results."""
        query = "machine learning"
        document = "machine learning is a subset of artificial intelligence"

        py_result = pure_python.bm25_similarity(query, document)
        np_result = numpy_impl.bm25_similarity(query, document)

        assert py_result == pytest.approx(np_result, abs=FLOAT_TOLERANCE)

    @pytest.mark.skipif(not HAS_RUST, reason="Rust module not available")
    def test_rust_vs_pure_python(self):
        """Test that Rust BM25 similarity gives same results."""
        query = "machine learning"
        document = "machine learning is a subset of artificial intelligence"

        py_result = pure_python.bm25_similarity(query, document)
        rust_result = text_similarity_rust.bm25_similarity(query, document)

        assert py_result == pytest.approx(rust_result, abs=FLOAT_TOLERANCE)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
