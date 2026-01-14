"""
NumPy-based implementation of text similarity algorithms.

Uses NumPy's vectorized operations for improved performance over pure Python.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Optional

import numpy as np
from numpy.typing import NDArray


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


def cosine_similarity(text1: str, text2: str) -> float:
    """
    Compute cosine similarity using NumPy vectorized operations.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Similarity score between 0 and 1
    """
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)

    if not tokens1 or not tokens2:
        return 0.0

    freq1 = Counter(tokens1)
    freq2 = Counter(tokens2)

    # Create aligned vectors for all terms
    all_terms = list(set(freq1.keys()) | set(freq2.keys()))

    vec1 = np.array([freq1.get(t, 0) for t in all_terms], dtype=np.float64)
    vec2 = np.array([freq2.get(t, 0) for t in all_terms], dtype=np.float64)

    # Compute cosine similarity using NumPy
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Compute Levenshtein distance using NumPy arrays.

    Uses vectorized operations where possible for improved performance.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Minimum number of edits
    """
    len1, len2 = len(s1), len(s2)

    if len1 == 0:
        return len2
    if len2 == 0:
        return len1

    # Create distance matrix using NumPy
    # We use two rows for memory efficiency
    prev_row = np.arange(len2 + 1, dtype=np.int32)
    curr_row = np.zeros(len2 + 1, dtype=np.int32)

    for i in range(1, len1 + 1):
        curr_row[0] = i

        # Vectorize the comparison for this row
        matches = np.array([s1[i - 1] == s2[j - 1] for j in range(1, len2 + 1)], dtype=np.int32)
        costs = 1 - matches  # 0 if match, 1 otherwise

        # Compute all three options
        deletions = prev_row[1:] + 1
        insertions = curr_row[:-1] + 1  # This needs sequential computation
        substitutions = prev_row[:-1] + costs

        # For insertions, we need to compute sequentially
        for j in range(1, len2 + 1):
            curr_row[j] = min(
                prev_row[j] + 1,      # deletion
                curr_row[j - 1] + 1,  # insertion (depends on previous)
                prev_row[j - 1] + (0 if s1[i - 1] == s2[j - 1] else 1)  # substitution
            )

        prev_row, curr_row = curr_row, prev_row

    return int(prev_row[len2])


def levenshtein_similarity(s1: str, s2: str) -> float:
    """
    Compute normalized Levenshtein similarity.

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
    Compute Jaccard similarity using set operations.

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
    Compute BM25 score using NumPy operations.

    Args:
        query: Search query text
        document: Document text to score
        k1: Term frequency saturation parameter
        b: Length normalization parameter
        avg_doc_len: Average document length

    Returns:
        BM25 score
    """
    query_tokens = tokenize(query)
    doc_tokens = tokenize(document)

    if not query_tokens or not doc_tokens:
        return 0.0

    doc_len = len(doc_tokens)
    avg_len = avg_doc_len if avg_doc_len is not None else float(doc_len)

    doc_freq = Counter(doc_tokens)

    # Get term frequencies for query terms that appear in document
    query_terms_in_doc = [t for t in query_tokens if t in doc_freq]
    if not query_terms_in_doc:
        return 0.0

    tfs = np.array([doc_freq[t] for t in query_terms_in_doc], dtype=np.float64)

    # Vectorized BM25 computation
    length_norm = 1 - b + b * (doc_len / avg_len)
    tf_component = (tfs * (k1 + 1)) / (tfs + k1 * length_norm)

    return float(np.sum(tf_component))


def bm25_rank(
    query: str,
    documents: list[str],
    k1: float = 1.5,
    b: float = 0.75
) -> list[tuple[int, float]]:
    """
    Rank documents using BM25 with NumPy vectorization.

    Args:
        query: Search query text
        documents: List of document texts
        k1: Term frequency saturation parameter
        b: Length normalization parameter

    Returns:
        List of (index, score) tuples sorted by score descending
    """
    if not documents:
        return []

    query_tokens = tokenize(query)
    if not query_tokens:
        return [(i, 0.0) for i in range(len(documents))]

    # Precompute document statistics
    doc_tokens_list = [tokenize(doc) for doc in documents]
    doc_freqs = [Counter(tokens) for tokens in doc_tokens_list]
    doc_lens = np.array([len(tokens) for tokens in doc_tokens_list], dtype=np.float64)
    avg_doc_len = float(np.mean(doc_lens)) if len(doc_lens) > 0 else 1.0

    # Compute IDF for query terms
    n = len(documents)
    unique_query_terms = list(set(query_tokens))

    # Document frequency for each query term
    df_counts = np.array([
        sum(1 for freq in doc_freqs if term in freq)
        for term in unique_query_terms
    ], dtype=np.float64)

    # IDF computation (vectorized)
    idf_values = np.log((n - df_counts + 0.5) / (df_counts + 0.5) + 1.0)
    idf_values = np.maximum(idf_values, 0.0)
    idf_dict = dict(zip(unique_query_terms, idf_values))

    # Score each document
    scores = np.zeros(len(documents), dtype=np.float64)

    length_norm = 1 - b + b * (doc_lens / avg_doc_len)

    for i, doc_freq in enumerate(doc_freqs):
        for term in query_tokens:
            if term in doc_freq and term in idf_dict:
                tf = doc_freq[term]
                tf_component = (tf * (k1 + 1)) / (tf + k1 * length_norm[i])
                scores[i] += idf_dict[term] * tf_component

    # Sort by score descending
    sorted_indices = np.argsort(-scores)
    result = [(int(idx), float(scores[idx])) for idx in sorted_indices]

    return result


def batch_cosine_similarity(query: str, documents: list[str]) -> list[float]:
    """
    Compute cosine similarity for multiple documents using vectorized operations.

    Args:
        query: Query text
        documents: List of document texts

    Returns:
        List of similarity scores
    """
    query_tokens = tokenize(query)
    if not query_tokens:
        return [0.0] * len(documents)

    query_freq = Counter(query_tokens)

    results = []
    for doc in documents:
        doc_tokens = tokenize(doc)
        if not doc_tokens:
            results.append(0.0)
            continue

        doc_freq = Counter(doc_tokens)
        all_terms = list(set(query_freq.keys()) | set(doc_freq.keys()))

        vec1 = np.array([query_freq.get(t, 0) for t in all_terms], dtype=np.float64)
        vec2 = np.array([doc_freq.get(t, 0) for t in all_terms], dtype=np.float64)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            results.append(0.0)
        else:
            results.append(float(dot_product / (norm1 * norm2)))

    return results


def batch_levenshtein_distance(query: str, documents: list[str]) -> list[int]:
    """
    Compute Levenshtein distance for multiple documents.

    Args:
        query: Query text
        documents: List of document texts

    Returns:
        List of distances
    """
    return [levenshtein_distance(query, doc) for doc in documents]


def batch_jaccard_similarity(query: str, documents: list[str]) -> list[float]:
    """
    Compute Jaccard similarity for multiple documents.

    Args:
        query: Query text
        documents: List of document texts

    Returns:
        List of similarity scores
    """
    return [jaccard_similarity(query, doc) for doc in documents]
