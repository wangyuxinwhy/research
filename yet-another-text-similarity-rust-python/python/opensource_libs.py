"""
Wrapper implementations using popular open-source libraries.

This module provides standardized interfaces to:
- rapidfuzz (C++ backend for string similarity)
- python-Levenshtein (C implementation)
- scikit-learn (for cosine similarity)
- rank-bm25 (BM25 implementation)
"""

from __future__ import annotations

import re
from typing import Optional

import numpy as np


def tokenize(text: str) -> list[str]:
    """
    Tokenize text into lowercase words.
    Handles both English and Chinese text.
    """
    tokens = []
    text = text.lower()
    segments = re.findall(r'[\w]+', text, re.UNICODE)

    for segment in segments:
        has_cjk = any('\u4e00' <= c <= '\u9fff' for c in segment)
        if has_cjk:
            i = 0
            current_word = []
            while i < len(segment):
                c = segment[i]
                if '\u4e00' <= c <= '\u9fff':
                    if current_word:
                        tokens.append(''.join(current_word))
                        current_word = []
                    tokens.append(c)
                else:
                    current_word.append(c)
                i += 1
            if current_word:
                tokens.append(''.join(current_word))
        else:
            tokens.append(segment)

    return [t for t in tokens if t]


# ============================================================================
# Cosine Similarity using scikit-learn
# ============================================================================

def cosine_similarity_sklearn(text1: str, text2: str) -> float:
    """
    Compute cosine similarity using scikit-learn's TF-IDF vectorizer.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Similarity score between 0 and 1
    """
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine

    if not text1.strip() or not text2.strip():
        return 0.0

    try:
        vectorizer = CountVectorizer(token_pattern=r'[\w]+')
        vectors = vectorizer.fit_transform([text1, text2])
        similarity = sklearn_cosine(vectors[0:1], vectors[1:2])[0, 0]
        return float(similarity)
    except ValueError:
        # Handle case where no features are extracted
        return 0.0


def batch_cosine_similarity_sklearn(query: str, documents: list[str]) -> list[float]:
    """
    Compute cosine similarity for multiple documents using sklearn.

    Args:
        query: Query text
        documents: List of document texts

    Returns:
        List of similarity scores
    """
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine

    if not query.strip() or not documents:
        return [0.0] * len(documents)

    try:
        all_texts = [query] + documents
        vectorizer = CountVectorizer(token_pattern=r'[\w]+')
        vectors = vectorizer.fit_transform(all_texts)
        query_vec = vectors[0:1]
        doc_vecs = vectors[1:]
        similarities = sklearn_cosine(query_vec, doc_vecs)[0]
        return similarities.tolist()
    except ValueError:
        return [0.0] * len(documents)


# ============================================================================
# Levenshtein Distance using rapidfuzz and python-Levenshtein
# ============================================================================

def levenshtein_distance_rapidfuzz(s1: str, s2: str) -> int:
    """
    Compute Levenshtein distance using rapidfuzz (C++ backend).

    Args:
        s1: First string
        s2: Second string

    Returns:
        Edit distance
    """
    from rapidfuzz.distance import Levenshtein
    return Levenshtein.distance(s1, s2)


def levenshtein_similarity_rapidfuzz(s1: str, s2: str) -> float:
    """
    Compute normalized Levenshtein similarity using rapidfuzz.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Similarity score between 0 and 1
    """
    from rapidfuzz.distance import Levenshtein
    return Levenshtein.normalized_similarity(s1, s2)


def levenshtein_distance_pylev(s1: str, s2: str) -> int:
    """
    Compute Levenshtein distance using python-Levenshtein (C backend).

    Args:
        s1: First string
        s2: Second string

    Returns:
        Edit distance
    """
    import Levenshtein as pylev
    return pylev.distance(s1, s2)


def levenshtein_similarity_pylev(s1: str, s2: str) -> float:
    """
    Compute normalized Levenshtein similarity using python-Levenshtein.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Similarity score between 0 and 1
    """
    import Levenshtein as pylev
    return pylev.ratio(s1, s2)


def batch_levenshtein_distance_rapidfuzz(query: str, documents: list[str]) -> list[int]:
    """
    Batch Levenshtein distance using rapidfuzz.

    Args:
        query: Query string
        documents: List of document strings

    Returns:
        List of distances
    """
    from rapidfuzz.distance import Levenshtein
    return [Levenshtein.distance(query, doc) for doc in documents]


# ============================================================================
# Jaccard Similarity
# ============================================================================

def jaccard_similarity_sklearn(text1: str, text2: str) -> float:
    """
    Compute Jaccard similarity using set operations (no sklearn needed).
    Included for API consistency.

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


# ============================================================================
# BM25 using rank-bm25
# ============================================================================

def bm25_score_rankbm25(
    query: str,
    document: str,
    k1: float = 1.5,
    b: float = 0.75,
    avg_doc_len: Optional[float] = None
) -> float:
    """
    Compute BM25 score using rank-bm25 library.

    Note: rank-bm25 is designed for corpus-level ranking, so for single
    document scoring we create a single-document corpus.

    Args:
        query: Search query text
        document: Document text to score
        k1: Term frequency saturation parameter
        b: Length normalization parameter
        avg_doc_len: Not used (rank-bm25 computes internally)

    Returns:
        BM25 score
    """
    from rank_bm25 import BM25Okapi

    query_tokens = tokenize(query)
    doc_tokens = tokenize(document)

    if not query_tokens or not doc_tokens:
        return 0.0

    # Create BM25 index with single document
    bm25 = BM25Okapi([doc_tokens], k1=k1, b=b)
    scores = bm25.get_scores(query_tokens)

    return float(scores[0])


def bm25_rank_rankbm25(
    query: str,
    documents: list[str],
    k1: float = 1.5,
    b: float = 0.75
) -> list[tuple[int, float]]:
    """
    Rank documents using rank-bm25 library.

    Args:
        query: Search query text
        documents: List of document texts
        k1: Term frequency saturation parameter
        b: Length normalization parameter

    Returns:
        List of (index, score) tuples sorted by score descending
    """
    from rank_bm25 import BM25Okapi

    if not documents:
        return []

    query_tokens = tokenize(query)
    if not query_tokens:
        return [(i, 0.0) for i in range(len(documents))]

    # Tokenize all documents
    doc_tokens_list = [tokenize(doc) for doc in documents]

    # Create BM25 index
    bm25 = BM25Okapi(doc_tokens_list, k1=k1, b=b)
    scores = bm25.get_scores(query_tokens)

    # Create sorted list of (index, score) tuples
    indexed_scores = list(enumerate(scores))
    indexed_scores.sort(key=lambda x: x[1], reverse=True)

    return [(int(idx), float(score)) for idx, score in indexed_scores]


# ============================================================================
# Convenience aliases for consistent API
# ============================================================================

# Use rapidfuzz as the default "opensource" Levenshtein implementation
levenshtein_distance = levenshtein_distance_rapidfuzz
levenshtein_similarity = levenshtein_similarity_rapidfuzz
batch_levenshtein_distance = batch_levenshtein_distance_rapidfuzz

# Use sklearn for cosine similarity
cosine_similarity = cosine_similarity_sklearn
batch_cosine_similarity = batch_cosine_similarity_sklearn

# Use native set operations for Jaccard (most efficient)
jaccard_similarity = jaccard_similarity_sklearn

# Use rank-bm25 for BM25
bm25_score = bm25_score_rankbm25
bm25_rank = bm25_rank_rankbm25
