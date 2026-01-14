"""
NumPy-based implementations of text similarity algorithms.
Leverages NumPy's C backend for vectorized operations.
"""

import numpy as np
from typing import List, Dict
from collections import Counter
import math


def cosine_similarity(text1: str, text2: str) -> float:
    """
    Calculate cosine similarity using NumPy vectorization.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Cosine similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0

    # Build character frequency vectors
    vec1 = Counter(text1)
    vec2 = Counter(text2)

    # Get all unique characters
    all_chars = sorted(set(vec1.keys()) | set(vec2.keys()))

    # Create numpy arrays
    arr1 = np.array([vec1.get(char, 0) for char in all_chars], dtype=np.float64)
    arr2 = np.array([vec2.get(char, 0) for char in all_chars], dtype=np.float64)

    # Vectorized computation
    dot_product = np.dot(arr1, arr2)
    magnitude1 = np.linalg.norm(arr1)
    magnitude2 = np.linalg.norm(arr2)

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return float(dot_product / (magnitude1 * magnitude2))


def levenshtein_distance(text1: str, text2: str) -> int:
    """
    Calculate Levenshtein distance using NumPy arrays.
    Still O(n*m) but with better memory locality.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Minimum number of single-character edits needed
    """
    len1, len2 = len(text1), len(text2)

    if len1 == 0:
        return len2
    if len2 == 0:
        return len1

    # Initialize DP matrix using NumPy
    dp = np.zeros((len1 + 1, len2 + 1), dtype=np.int32)

    # Base cases
    dp[:, 0] = np.arange(len1 + 1)
    dp[0, :] = np.arange(len2 + 1)

    # Fill DP matrix
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            if text1[i - 1] == text2[j - 1]:
                dp[i, j] = dp[i - 1, j - 1]
            else:
                dp[i, j] = 1 + min(
                    dp[i - 1, j],      # deletion
                    dp[i, j - 1],      # insertion
                    dp[i - 1, j - 1]   # substitution
                )

    return int(dp[len1, len2])


def levenshtein_similarity(text1: str, text2: str) -> float:
    """
    Calculate normalized Levenshtein similarity.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Similarity score between 0 and 1
    """
    if not text1 and not text2:
        return 1.0
    if not text1 or not text2:
        return 0.0

    distance = levenshtein_distance(text1, text2)
    max_len = max(len(text1), len(text2))
    return 1.0 - (distance / max_len)


def jaccard_similarity(text1: str, text2: str, n: int = 2) -> float:
    """
    Calculate Jaccard similarity using character n-grams.
    Note: Jaccard is inherently set-based, so NumPy doesn't provide much benefit.

    Args:
        text1: First text string
        text2: Second text string
        n: Size of n-grams (default: 2 for bigrams)

    Returns:
        Jaccard similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0

    def get_ngrams(text: str, n: int) -> set:
        """Extract n-grams from text."""
        if len(text) < n:
            return {text}
        return {text[i:i+n] for i in range(len(text) - n + 1)}

    ngrams1 = get_ngrams(text1, n)
    ngrams2 = get_ngrams(text2, n)

    intersection = len(ngrams1 & ngrams2)
    union = len(ngrams1 | ngrams2)

    if union == 0:
        return 0.0

    return intersection / union


class BM25:
    """
    BM25 ranking algorithm with NumPy vectorization.
    """

    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 with a corpus of documents.

        Args:
            corpus: List of document strings
            k1: Term frequency saturation parameter (default: 1.5)
            b: Length normalization parameter (default: 0.75)
        """
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)

        # Tokenize documents
        self.tokenized_corpus = [doc.lower().split() for doc in corpus]

        # Calculate document lengths and average length
        self.doc_lengths = np.array([len(doc) for doc in self.tokenized_corpus], dtype=np.float64)
        self.avg_doc_length = np.mean(self.doc_lengths) if self.corpus_size > 0 else 0

        # Build vocabulary and calculate IDF
        self.vocab, self.idf = self._calculate_idf()

        # Build term frequency matrix
        self._build_tf_matrix()

    def _calculate_idf(self) -> tuple:
        """Calculate inverse document frequency for all terms."""
        # Build vocabulary
        vocab = set()
        for doc in self.tokenized_corpus:
            vocab.update(doc)
        vocab = sorted(vocab)
        vocab_dict = {term: idx for idx, term in enumerate(vocab)}

        # Count documents containing each term
        doc_frequencies = np.zeros(len(vocab), dtype=np.int32)
        for doc in self.tokenized_corpus:
            unique_terms = set(doc)
            for term in unique_terms:
                if term in vocab_dict:
                    doc_frequencies[vocab_dict[term]] += 1

        # Calculate IDF using NumPy vectorization
        idf = np.log((self.corpus_size - doc_frequencies + 0.5) / (doc_frequencies + 0.5) + 1.0)

        return vocab_dict, idf

    def _build_tf_matrix(self):
        """Build term frequency matrix for all documents."""
        self.tf_matrix = np.zeros((self.corpus_size, len(self.vocab)), dtype=np.int32)

        for doc_idx, doc in enumerate(self.tokenized_corpus):
            term_counts = Counter(doc)
            for term, count in term_counts.items():
                if term in self.vocab:
                    term_idx = self.vocab[term]
                    self.tf_matrix[doc_idx, term_idx] = count

    def get_scores(self, query: str) -> np.ndarray:
        """
        Calculate BM25 scores for all documents given a query.

        Args:
            query: Query string

        Returns:
            NumPy array of BM25 scores for each document
        """
        query_terms = query.lower().split()

        # Build query vector
        query_vec = np.zeros(len(self.vocab), dtype=np.int32)
        for term in query_terms:
            if term in self.vocab:
                query_vec[self.vocab[term]] = 1

        # Vectorized BM25 calculation
        # Shape: (corpus_size, vocab_size)
        tf = self.tf_matrix.astype(np.float64)

        # Calculate length normalization factor
        # Shape: (corpus_size, 1)
        length_norm = (1 - self.b + self.b * (self.doc_lengths / self.avg_doc_length)).reshape(-1, 1)

        # BM25 formula (vectorized)
        # numerator: tf * (k1 + 1)
        numerator = tf * (self.k1 + 1)

        # denominator: tf + k1 * length_norm
        denominator = tf + self.k1 * length_norm

        # Avoid division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            bm25_weights = np.where(denominator != 0, numerator / denominator, 0)

        # Multiply by IDF
        bm25_weights *= self.idf

        # Multiply by query vector and sum
        scores = np.sum(bm25_weights * query_vec, axis=1)

        return scores

    def get_top_n(self, query: str, n: int = 10) -> List[tuple]:
        """
        Get top N documents for a query.

        Args:
            query: Query string
            n: Number of top documents to return

        Returns:
            List of (doc_index, score) tuples sorted by score
        """
        scores = self.get_scores(query)
        top_indices = np.argsort(scores)[::-1][:n]
        return [(int(idx), float(scores[idx])) for idx in top_indices]


def bm25_similarity(query: str, document: str, k1: float = 1.5, b: float = 0.75) -> float:
    """
    Calculate BM25 similarity between a query and a single document.

    Args:
        query: Query string
        document: Document string
        k1: Term frequency saturation parameter
        b: Length normalization parameter

    Returns:
        BM25 similarity score
    """
    bm25 = BM25([document], k1=k1, b=b)
    scores = bm25.get_scores(query)
    return float(scores[0]) if len(scores) > 0 else 0.0


if __name__ == "__main__":
    # Quick test
    text1 = "hello world"
    text2 = "hello python world"

    print(f"Cosine Similarity: {cosine_similarity(text1, text2):.4f}")
    print(f"Levenshtein Distance: {levenshtein_distance(text1, text2)}")
    print(f"Levenshtein Similarity: {levenshtein_similarity(text1, text2):.4f}")
    print(f"Jaccard Similarity: {jaccard_similarity(text1, text2):.4f}")
    print(f"BM25 Similarity: {bm25_similarity(text1, text2):.4f}")
