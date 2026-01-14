"""
Pure Python implementations of text similarity algorithms.
These serve as the baseline for performance comparisons.
"""

import math
from typing import List, Dict, Set
from collections import Counter


def cosine_similarity(text1: str, text2: str) -> float:
    """
    Calculate cosine similarity between two texts using character-level vectors.

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
    all_chars = set(vec1.keys()) | set(vec2.keys())

    # Calculate dot product and magnitudes
    dot_product = sum(vec1.get(char, 0) * vec2.get(char, 0) for char in all_chars)
    magnitude1 = math.sqrt(sum(count ** 2 for count in vec1.values()))
    magnitude2 = math.sqrt(sum(count ** 2 for count in vec2.values()))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def levenshtein_distance(text1: str, text2: str) -> int:
    """
    Calculate Levenshtein edit distance between two texts.
    Uses dynamic programming with full matrix.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Minimum number of single-character edits needed
    """
    len1, len2 = len(text1), len(text2)

    # Early returns for empty strings
    if len1 == 0:
        return len2
    if len2 == 0:
        return len1

    # Initialize DP matrix
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    # Base cases
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j

    # Fill DP matrix
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            if text1[i - 1] == text2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],      # deletion
                    dp[i][j - 1],      # insertion
                    dp[i - 1][j - 1]   # substitution
                )

    return dp[len1][len2]


def levenshtein_similarity(text1: str, text2: str) -> float:
    """
    Calculate normalized Levenshtein similarity (1 - normalized distance).

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

    Args:
        text1: First text string
        text2: Second text string
        n: Size of n-grams (default: 2 for bigrams)

    Returns:
        Jaccard similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0

    def get_ngrams(text: str, n: int) -> Set[str]:
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
    BM25 ranking algorithm for document retrieval.
    Pure Python implementation.
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

        # Tokenize documents (simple whitespace tokenization)
        self.tokenized_corpus = [doc.lower().split() for doc in corpus]

        # Calculate document lengths and average length
        self.doc_lengths = [len(doc) for doc in self.tokenized_corpus]
        self.avg_doc_length = sum(self.doc_lengths) / self.corpus_size if self.corpus_size > 0 else 0

        # Calculate IDF values
        self.idf = self._calculate_idf()

    def _calculate_idf(self) -> Dict[str, float]:
        """Calculate inverse document frequency for all terms."""
        idf = {}

        # Count documents containing each term
        doc_frequencies = Counter()
        for doc in self.tokenized_corpus:
            unique_terms = set(doc)
            for term in unique_terms:
                doc_frequencies[term] += 1

        # Calculate IDF: log((N - df + 0.5) / (df + 0.5) + 1)
        for term, df in doc_frequencies.items():
            idf[term] = math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)

        return idf

    def get_scores(self, query: str) -> List[float]:
        """
        Calculate BM25 scores for all documents given a query.

        Args:
            query: Query string

        Returns:
            List of BM25 scores for each document
        """
        query_terms = query.lower().split()
        scores = [0.0] * self.corpus_size

        for doc_idx, doc in enumerate(self.tokenized_corpus):
            doc_length = self.doc_lengths[doc_idx]
            term_frequencies = Counter(doc)

            for term in query_terms:
                if term not in self.idf:
                    continue

                tf = term_frequencies.get(term, 0)
                idf = self.idf[term]

                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)

                scores[doc_idx] += idf * (numerator / denominator)

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
        scored_docs = list(enumerate(scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return scored_docs[:n]


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
    return scores[0] if scores else 0.0


if __name__ == "__main__":
    # Quick test
    text1 = "hello world"
    text2 = "hello python world"

    print(f"Cosine Similarity: {cosine_similarity(text1, text2):.4f}")
    print(f"Levenshtein Distance: {levenshtein_distance(text1, text2)}")
    print(f"Levenshtein Similarity: {levenshtein_similarity(text1, text2):.4f}")
    print(f"Jaccard Similarity: {jaccard_similarity(text1, text2):.4f}")
    print(f"BM25 Similarity: {bm25_similarity(text1, text2):.4f}")
