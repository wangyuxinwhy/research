"""
Pure Python implementation of text similarity algorithms.

This module provides baseline implementations without any external dependencies
beyond the Python standard library.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Optional


def tokenize(text: str) -> list[str]:
    """
    Tokenize text into lowercase words.
    Handles both English and Chinese text.

    For English: splits on whitespace and punctuation.
    For Chinese: treats each character as a separate token.
    """
    tokens = []
    text = text.lower()

    # Split into segments (words or Chinese character sequences)
    segments = re.findall(r'[\w]+', text, re.UNICODE)

    for segment in segments:
        # Check if segment contains CJK characters
        has_cjk = any('\u4e00' <= c <= '\u9fff' for c in segment)

        if has_cjk:
            # For CJK text, split into individual characters and non-CJK parts
            i = 0
            current_word = []
            while i < len(segment):
                c = segment[i]
                if '\u4e00' <= c <= '\u9fff':
                    # If we have accumulated non-CJK chars, add them as a word
                    if current_word:
                        tokens.append(''.join(current_word))
                        current_word = []
                    # Add CJK character as individual token
                    tokens.append(c)
                else:
                    current_word.append(c)
                i += 1
            # Add any remaining non-CJK word
            if current_word:
                tokens.append(''.join(current_word))
        else:
            # For non-CJK text, keep as single word
            tokens.append(segment)

    return [t for t in tokens if t]


def cosine_similarity(text1: str, text2: str) -> float:
    """
    Compute cosine similarity between two texts based on term frequency.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Similarity score between 0 and 1, where 1 means identical
    """
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)

    if not tokens1 or not tokens2:
        return 0.0

    freq1 = Counter(tokens1)
    freq2 = Counter(tokens2)

    # Get all unique terms
    all_terms = set(freq1.keys()) | set(freq2.keys())

    # Compute dot product and magnitudes
    dot_product = 0.0
    mag1 = 0.0
    mag2 = 0.0

    for term in all_terms:
        v1 = freq1.get(term, 0)
        v2 = freq2.get(term, 0)
        dot_product += v1 * v2
        mag1 += v1 * v1
        mag2 += v2 * v2

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return dot_product / (math.sqrt(mag1) * math.sqrt(mag2))


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Compute Levenshtein edit distance between two strings.

    Uses the classic dynamic programming approach with O(min(m,n)) space.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Minimum number of edits (insertions, deletions, substitutions)
    """
    # Ensure s1 is the shorter string for space optimization
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    len1, len2 = len(s1), len(s2)

    if len1 == 0:
        return len2
    if len2 == 0:
        return len1

    # Use two rows for space efficiency
    prev_row = list(range(len1 + 1))
    curr_row = [0] * (len1 + 1)

    for j in range(1, len2 + 1):
        curr_row[0] = j

        for i in range(1, len1 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1

            curr_row[i] = min(
                prev_row[i] + 1,      # deletion
                curr_row[i - 1] + 1,  # insertion
                prev_row[i - 1] + cost  # substitution
            )

        prev_row, curr_row = curr_row, prev_row

    return prev_row[len1]


def levenshtein_similarity(s1: str, s2: str) -> float:
    """
    Compute normalized Levenshtein similarity (1 - normalized_distance).

    Args:
        s1: First string
        s2: Second string

    Returns:
        Similarity score between 0 and 1
    """
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))

    if max_len == 0:
        return 1.0

    return 1.0 - (distance / max_len)


def jaccard_similarity(text1: str, text2: str) -> float:
    """
    Compute Jaccard similarity between two texts.

    The Jaccard index is the size of intersection divided by size of union
    of the word sets.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Similarity score between 0 and 1
    """
    tokens1 = set(tokenize(text1))
    tokens2 = set(tokenize(text2))

    if not tokens1 and not tokens2:
        return 1.0

    if not tokens1 or not tokens2:
        return 0.0

    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)

    return intersection / union


def bm25_score(
    query: str,
    document: str,
    k1: float = 1.5,
    b: float = 0.75,
    avg_doc_len: Optional[float] = None
) -> float:
    """
    Compute BM25 score for a single document against a query.

    This is a simplified version that computes term frequency-based scoring
    without corpus-level IDF statistics.

    Args:
        query: Search query text
        document: Document text to score
        k1: Term frequency saturation parameter (default: 1.5)
        b: Length normalization parameter (default: 0.75)
        avg_doc_len: Average document length (defaults to current doc length)

    Returns:
        BM25 score (higher means more relevant)
    """
    query_tokens = tokenize(query)
    doc_tokens = tokenize(document)

    if not query_tokens or not doc_tokens:
        return 0.0

    doc_len = len(doc_tokens)
    avg_len = avg_doc_len if avg_doc_len is not None else doc_len

    doc_freq = Counter(doc_tokens)

    score = 0.0

    for term in query_tokens:
        if term in doc_freq:
            tf = doc_freq[term]
            # BM25 term frequency component
            tf_component = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_len)))
            score += tf_component

    return score


def bm25_rank(
    query: str,
    documents: list[str],
    k1: float = 1.5,
    b: float = 0.75
) -> list[tuple[int, float]]:
    """
    Rank multiple documents against a query using BM25.

    Computes BM25 scores with proper IDF weights computed from the document corpus.

    Args:
        query: Search query text
        documents: List of document texts
        k1: Term frequency saturation parameter
        b: Length normalization parameter

    Returns:
        List of (document_index, score) tuples sorted by score descending
    """
    if not documents:
        return []

    query_tokens = tokenize(query)
    if not query_tokens:
        return [(i, 0.0) for i in range(len(documents))]

    # Precompute document statistics
    doc_tokens_list = [tokenize(doc) for doc in documents]
    doc_freqs = [Counter(tokens) for tokens in doc_tokens_list]
    doc_lens = [len(tokens) for tokens in doc_tokens_list]
    avg_doc_len = sum(doc_lens) / len(doc_lens) if doc_lens else 1.0

    # Compute IDF for query terms
    n = len(documents)
    idf: dict[str, float] = {}

    for term in query_tokens:
        df = sum(1 for freq in doc_freqs if term in freq)
        if df > 0:
            # Standard BM25 IDF formula
            idf_score = math.log((n - df + 0.5) / (df + 0.5) + 1.0)
            idf[term] = max(0.0, idf_score)

    # Score each document
    scores: list[tuple[int, float]] = []

    for i, (doc_freq, doc_len) in enumerate(zip(doc_freqs, doc_lens)):
        score = 0.0

        for term in query_tokens:
            if term in doc_freq and term in idf:
                tf = doc_freq[term]
                tf_component = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_doc_len)))
                score += idf[term] * tf_component

        scores.append((i, score))

    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)

    return scores


def batch_cosine_similarity(query: str, documents: list[str]) -> list[float]:
    """
    Compute cosine similarity between a query and multiple documents.

    Args:
        query: Query text
        documents: List of document texts

    Returns:
        List of similarity scores
    """
    return [cosine_similarity(query, doc) for doc in documents]


def batch_levenshtein_distance(query: str, documents: list[str]) -> list[int]:
    """
    Compute Levenshtein distance between a query and multiple documents.

    Args:
        query: Query text
        documents: List of document texts

    Returns:
        List of distances
    """
    return [levenshtein_distance(query, doc) for doc in documents]


def batch_jaccard_similarity(query: str, documents: list[str]) -> list[float]:
    """
    Compute Jaccard similarity between a query and multiple documents.

    Args:
        query: Query text
        documents: List of document texts

    Returns:
        List of similarity scores
    """
    return [jaccard_similarity(query, doc) for doc in documents]
