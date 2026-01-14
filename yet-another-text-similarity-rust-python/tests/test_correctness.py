"""
Tests for verifying correctness and consistency across implementations.

Ensures all implementations produce numerically consistent results
(within floating-point tolerance).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python import pure_python, numpy_impl, opensource_libs

# Test tolerance for floating-point comparisons
FLOAT_TOLERANCE = 1e-6


class TestCosineSimlarity:
    """Tests for cosine similarity implementations."""

    @pytest.fixture
    def test_cases(self) -> list[tuple[str, str]]:
        return [
            ("hello world", "hello world"),  # Identical
            ("hello world", "goodbye world"),  # Partial overlap
            ("the quick brown fox", "lazy dog sleeps"),  # No overlap
            ("", "hello"),  # Empty string
            ("hello", ""),  # Empty string
            ("", ""),  # Both empty
            # Chinese text
            ("你好世界", "你好世界"),
            ("人工智能机器学习", "深度学习神经网络"),
            # Mixed
            ("AI人工智能", "AI人工智能技术"),
        ]

    def test_pure_python_vs_numpy(self, test_cases):
        """Verify pure Python and NumPy implementations match."""
        for text1, text2 in test_cases:
            py_result = pure_python.cosine_similarity(text1, text2)
            np_result = numpy_impl.cosine_similarity(text1, text2)
            assert abs(py_result - np_result) < FLOAT_TOLERANCE, \
                f"Mismatch for ({text1!r}, {text2!r}): {py_result} vs {np_result}"

    def test_range(self, test_cases):
        """Verify results are in valid range [0, 1]."""
        for text1, text2 in test_cases:
            result = pure_python.cosine_similarity(text1, text2)
            assert 0 <= result <= 1, f"Out of range: {result}"

    def test_symmetry(self, test_cases):
        """Verify cosine similarity is symmetric."""
        for text1, text2 in test_cases:
            result1 = pure_python.cosine_similarity(text1, text2)
            result2 = pure_python.cosine_similarity(text2, text1)
            assert abs(result1 - result2) < FLOAT_TOLERANCE, \
                f"Not symmetric for ({text1!r}, {text2!r}): {result1} vs {result2}"

    def test_identity(self):
        """Verify identical texts have similarity 1.0."""
        texts = ["hello world", "你好世界", "AI人工智能"]
        for text in texts:
            result = pure_python.cosine_similarity(text, text)
            assert abs(result - 1.0) < FLOAT_TOLERANCE, \
                f"Identity failed for {text!r}: {result}"


class TestLevenshteinDistance:
    """Tests for Levenshtein distance implementations."""

    @pytest.fixture
    def test_cases(self) -> list[tuple[str, str, int]]:
        """Test cases with expected distances."""
        return [
            ("", "", 0),
            ("a", "", 1),
            ("", "a", 1),
            ("abc", "abc", 0),
            ("abc", "abd", 1),  # substitution
            ("abc", "ab", 1),   # deletion
            ("abc", "abcd", 1),  # insertion
            ("kitten", "sitting", 3),
            ("saturday", "sunday", 3),
            # Chinese
            ("你好", "你好", 0),
            ("你好", "你们好", 1),
        ]

    def test_pure_python(self, test_cases):
        """Verify pure Python implementation against known values."""
        for s1, s2, expected in test_cases:
            result = pure_python.levenshtein_distance(s1, s2)
            assert result == expected, \
                f"Expected {expected} for ({s1!r}, {s2!r}), got {result}"

    def test_pure_python_vs_numpy(self, test_cases):
        """Verify pure Python and NumPy implementations match."""
        for s1, s2, _ in test_cases:
            py_result = pure_python.levenshtein_distance(s1, s2)
            np_result = numpy_impl.levenshtein_distance(s1, s2)
            assert py_result == np_result, \
                f"Mismatch for ({s1!r}, {s2!r}): {py_result} vs {np_result}"

    def test_vs_rapidfuzz(self, test_cases):
        """Verify against rapidfuzz library."""
        for s1, s2, expected in test_cases:
            py_result = pure_python.levenshtein_distance(s1, s2)
            rf_result = opensource_libs.levenshtein_distance_rapidfuzz(s1, s2)
            assert py_result == rf_result == expected, \
                f"Mismatch for ({s1!r}, {s2!r}): py={py_result}, rf={rf_result}, expected={expected}"

    def test_symmetry(self, test_cases):
        """Verify Levenshtein distance is symmetric."""
        for s1, s2, _ in test_cases:
            result1 = pure_python.levenshtein_distance(s1, s2)
            result2 = pure_python.levenshtein_distance(s2, s1)
            assert result1 == result2, \
                f"Not symmetric for ({s1!r}, {s2!r}): {result1} vs {result2}"

    def test_non_negative(self, test_cases):
        """Verify distances are non-negative."""
        for s1, s2, _ in test_cases:
            result = pure_python.levenshtein_distance(s1, s2)
            assert result >= 0, f"Negative distance: {result}"


class TestJaccardSimilarity:
    """Tests for Jaccard similarity implementations."""

    @pytest.fixture
    def test_cases(self) -> list[tuple[str, str]]:
        return [
            ("hello world", "hello world"),
            ("hello world", "world hello"),  # Same words, different order
            ("a b c", "b c d"),  # Partial overlap
            ("the quick brown", "lazy sleeping dog"),  # No overlap
            ("", "hello"),
            ("hello", ""),
            ("", ""),
            # Chinese
            ("机器 学习", "机器 学习"),
            ("人工 智能", "机器 学习"),
        ]

    def test_pure_python_vs_numpy(self, test_cases):
        """Verify pure Python and NumPy implementations match."""
        for text1, text2 in test_cases:
            py_result = pure_python.jaccard_similarity(text1, text2)
            np_result = numpy_impl.jaccard_similarity(text1, text2)
            assert abs(py_result - np_result) < FLOAT_TOLERANCE, \
                f"Mismatch for ({text1!r}, {text2!r}): {py_result} vs {np_result}"

    def test_range(self, test_cases):
        """Verify results are in valid range [0, 1]."""
        for text1, text2 in test_cases:
            result = pure_python.jaccard_similarity(text1, text2)
            assert 0 <= result <= 1, f"Out of range: {result}"

    def test_symmetry(self, test_cases):
        """Verify Jaccard similarity is symmetric."""
        for text1, text2 in test_cases:
            result1 = pure_python.jaccard_similarity(text1, text2)
            result2 = pure_python.jaccard_similarity(text2, text1)
            assert abs(result1 - result2) < FLOAT_TOLERANCE, \
                f"Not symmetric for ({text1!r}, {text2!r}): {result1} vs {result2}"

    def test_same_words_different_order(self):
        """Verify word order doesn't affect Jaccard similarity."""
        text1 = "hello world"
        text2 = "world hello"
        result = pure_python.jaccard_similarity(text1, text2)
        assert abs(result - 1.0) < FLOAT_TOLERANCE, \
            f"Same words should have similarity 1.0, got {result}"


class TestBM25:
    """Tests for BM25 implementations."""

    @pytest.fixture
    def documents(self) -> list[str]:
        return [
            "The quick brown fox jumps over the lazy dog",
            "A quick brown dog outpaces a fox",
            "The fox is quick and brown",
            "Dogs are lazy animals",
            "Foxes and dogs are both animals",
        ]

    def test_pure_python_vs_numpy_rank(self, documents):
        """Verify ranking order is consistent."""
        query = "quick brown fox"

        py_rank = pure_python.bm25_rank(query, documents)
        np_rank = numpy_impl.bm25_rank(query, documents)

        # Check ranking order (top 3)
        py_order = [r[0] for r in py_rank[:3]]
        np_order = [r[0] for r in np_rank[:3]]

        assert py_order == np_order, \
            f"Ranking order mismatch: {py_order} vs {np_order}"

    def test_vs_rankbm25(self, documents):
        """Verify against rank-bm25 library."""
        query = "quick brown fox"

        py_rank = pure_python.bm25_rank(query, documents)
        rb_rank = opensource_libs.bm25_rank_rankbm25(query, documents)

        # Check top document matches
        py_top = py_rank[0][0]
        rb_top = rb_rank[0][0]

        assert py_top == rb_top, \
            f"Top document mismatch: {py_top} vs {rb_top}"

    def test_relevant_document_ranked_higher(self, documents):
        """Verify that relevant documents are ranked higher."""
        query = "lazy dog"
        rank = pure_python.bm25_rank(query, documents)

        # Document 0 and 3 contain "lazy" and/or "dog"
        top_3_indices = {r[0] for r in rank[:3]}
        assert 0 in top_3_indices or 3 in top_3_indices, \
            f"Relevant documents not in top 3: {rank[:3]}"


class TestRustImplementation:
    """Tests for Rust implementation (when available)."""

    @pytest.fixture
    def rust_module(self):
        """Try to import Rust module, skip if not available."""
        try:
            import text_similarity_rs
            return text_similarity_rs
        except ImportError:
            pytest.skip("Rust module not built. Run 'maturin develop' first.")

    def test_cosine_similarity(self, rust_module):
        """Verify Rust cosine similarity matches Python."""
        test_cases = [
            ("hello world", "hello world"),
            ("hello world", "goodbye world"),
            ("AI人工智能", "AI人工智能技术"),
        ]

        for text1, text2 in test_cases:
            py_result = pure_python.cosine_similarity(text1, text2)
            rs_result = rust_module.cosine_similarity(text1, text2)
            assert abs(py_result - rs_result) < FLOAT_TOLERANCE, \
                f"Mismatch for ({text1!r}, {text2!r}): py={py_result}, rs={rs_result}"

    def test_levenshtein_distance(self, rust_module):
        """Verify Rust Levenshtein distance matches Python."""
        test_cases = [
            ("", ""),
            ("abc", "abc"),
            ("kitten", "sitting"),
            ("你好", "你们好"),
        ]

        for s1, s2 in test_cases:
            py_result = pure_python.levenshtein_distance(s1, s2)
            rs_result = rust_module.levenshtein_distance(s1, s2)
            assert py_result == rs_result, \
                f"Mismatch for ({s1!r}, {s2!r}): py={py_result}, rs={rs_result}"

    def test_jaccard_similarity(self, rust_module):
        """Verify Rust Jaccard similarity matches Python."""
        test_cases = [
            ("hello world", "hello world"),
            ("a b c", "b c d"),
            ("机器 学习", "机器 学习"),
        ]

        for text1, text2 in test_cases:
            py_result = pure_python.jaccard_similarity(text1, text2)
            rs_result = rust_module.jaccard_similarity(text1, text2)
            assert abs(py_result - rs_result) < FLOAT_TOLERANCE, \
                f"Mismatch for ({text1!r}, {text2!r}): py={py_result}, rs={rs_result}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
