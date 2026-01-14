"""
Wrappers around popular open-source libraries for text similarity.
These represent the "best in class" implementations we're comparing against.
"""

from typing import List
import Levenshtein
import rapidfuzz.distance.Levenshtein as rf_levenshtein
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine
from rank_bm25 import BM25Okapi
import numpy as np


def cosine_similarity_sklearn(text1: str, text2: str) -> float:
    """
    Calculate cosine similarity using scikit-learn's TF-IDF vectorizer.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Cosine similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0

    # Use character-level TF-IDF for consistency with our implementations
    vectorizer = TfidfVectorizer(analyzer='char', lowercase=False)

    try:
        # Fit and transform both texts
        tfidf_matrix = vectorizer.fit_transform([text1, text2])

        # Calculate cosine similarity
        similarity = sklearn_cosine(tfidf_matrix[0:1], tfidf_matrix[1:2])
        return float(similarity[0][0])
    except ValueError:
        # Handle edge cases where vocabulary is empty
        return 0.0


def levenshtein_distance_python(text1: str, text2: str) -> int:
    """
    Calculate Levenshtein distance using python-Levenshtein (C implementation).

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Minimum number of single-character edits needed
    """
    return Levenshtein.distance(text1, text2)


def levenshtein_similarity_python(text1: str, text2: str) -> float:
    """
    Calculate normalized Levenshtein similarity using python-Levenshtein.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Similarity score between 0 and 1
    """
    return Levenshtein.ratio(text1, text2)


def levenshtein_distance_rapidfuzz(text1: str, text2: str) -> int:
    """
    Calculate Levenshtein distance using rapidfuzz (C++ implementation).

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Minimum number of single-character edits needed
    """
    return rf_levenshtein.distance(text1, text2)


def levenshtein_similarity_rapidfuzz(text1: str, text2: str) -> float:
    """
    Calculate normalized Levenshtein similarity using rapidfuzz.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Similarity score between 0 and 1 (normalized)
    """
    return rf_levenshtein.normalized_similarity(text1, text2)


def jaccard_similarity_rapidfuzz(text1: str, text2: str, n: int = 2) -> float:
    """
    Calculate Jaccard similarity using rapidfuzz.

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

    if not ngrams1 or not ngrams2:
        return 0.0

    intersection = len(ngrams1 & ngrams2)
    union = len(ngrams1 | ngrams2)

    if union == 0:
        return 0.0

    return intersection / union


class BM25RankBM25:
    """
    Wrapper around rank-bm25 library (pure Python implementation).
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

        # Tokenize corpus
        tokenized_corpus = [doc.lower().split() for doc in corpus]

        # Initialize BM25Okapi
        self.bm25 = BM25Okapi(tokenized_corpus, k1=k1, b=b)

    def get_scores(self, query: str) -> np.ndarray:
        """
        Calculate BM25 scores for all documents given a query.

        Args:
            query: Query string

        Returns:
            NumPy array of BM25 scores for each document
        """
        query_tokens = query.lower().split()
        return self.bm25.get_scores(query_tokens)

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


def bm25_similarity_rankbm25(query: str, document: str, k1: float = 1.5, b: float = 0.75) -> float:
    """
    Calculate BM25 similarity between a query and a single document using rank-bm25.

    Args:
        query: Query string
        document: Document string
        k1: Term frequency saturation parameter
        b: Length normalization parameter

    Returns:
        BM25 similarity score
    """
    bm25 = BM25RankBM25([document], k1=k1, b=b)
    scores = bm25.get_scores(query)
    return float(scores[0]) if len(scores) > 0 else 0.0


if __name__ == "__main__":
    # Quick test
    text1 = "hello world"
    text2 = "hello python world"

    print("Open-source library benchmarks:")
    print(f"Cosine Similarity (sklearn): {cosine_similarity_sklearn(text1, text2):.4f}")
    print(f"Levenshtein Distance (python-Levenshtein): {levenshtein_distance_python(text1, text2)}")
    print(f"Levenshtein Similarity (python-Levenshtein): {levenshtein_similarity_python(text1, text2):.4f}")
    print(f"Levenshtein Distance (rapidfuzz): {levenshtein_distance_rapidfuzz(text1, text2)}")
    print(f"Levenshtein Similarity (rapidfuzz): {levenshtein_similarity_rapidfuzz(text1, text2):.4f}")
    print(f"Jaccard Similarity (rapidfuzz): {jaccard_similarity_rapidfuzz(text1, text2):.4f}")
    print(f"BM25 Similarity (rank-bm25): {bm25_similarity_rankbm25(text1, text2):.4f}")
