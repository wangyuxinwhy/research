use ahash::AHashMap;
use std::collections::HashSet;
use unicode_segmentation::UnicodeSegmentation;

#[cfg(feature = "pyo3")]
use pyo3::prelude::*;

// ============================================================================
// Core algorithms (no PyO3 dependency)
// ============================================================================

/// Tokenize text into words (handles both English and Chinese)
pub fn tokenize(text: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    for word in text.unicode_words() {
        let lower = word.to_lowercase();
        if !lower.is_empty() {
            tokens.push(lower);
        }
    }
    tokens
}

/// Build term frequency map from tokens
pub fn build_term_freq(tokens: &[String]) -> AHashMap<String, f64> {
    let mut freq: AHashMap<String, f64> = AHashMap::new();
    for token in tokens {
        *freq.entry(token.clone()).or_insert(0.0) += 1.0;
    }
    freq
}

/// Cosine similarity between two texts (native Rust)
pub fn cosine_similarity_native(text1: &str, text2: &str) -> f64 {
    let tokens1 = tokenize(text1);
    let tokens2 = tokenize(text2);

    if tokens1.is_empty() || tokens2.is_empty() {
        return 0.0;
    }

    let freq1 = build_term_freq(&tokens1);
    let freq2 = build_term_freq(&tokens2);

    let mut dot_product = 0.0;
    let mut mag1 = 0.0;
    let mut mag2 = 0.0;

    let mut all_terms: HashSet<&String> = HashSet::new();
    all_terms.extend(freq1.keys());
    all_terms.extend(freq2.keys());

    for term in all_terms {
        let v1 = freq1.get(term).copied().unwrap_or(0.0);
        let v2 = freq2.get(term).copied().unwrap_or(0.0);
        dot_product += v1 * v2;
        mag1 += v1 * v1;
        mag2 += v2 * v2;
    }

    if mag1 == 0.0 || mag2 == 0.0 {
        return 0.0;
    }

    dot_product / (mag1.sqrt() * mag2.sqrt())
}

/// Levenshtein edit distance between two strings (native Rust)
pub fn levenshtein_distance_native(s1: &str, s2: &str) -> usize {
    let chars1: Vec<char> = s1.chars().collect();
    let chars2: Vec<char> = s2.chars().collect();

    let len1 = chars1.len();
    let len2 = chars2.len();

    if len1 == 0 {
        return len2;
    }
    if len2 == 0 {
        return len1;
    }

    let mut prev_row: Vec<usize> = (0..=len2).collect();
    let mut curr_row: Vec<usize> = vec![0; len2 + 1];

    for i in 1..=len1 {
        curr_row[0] = i;

        for j in 1..=len2 {
            let cost = if chars1[i - 1] == chars2[j - 1] { 0 } else { 1 };

            curr_row[j] = (prev_row[j] + 1)
                .min(curr_row[j - 1] + 1)
                .min(prev_row[j - 1] + cost);
        }

        std::mem::swap(&mut prev_row, &mut curr_row);
    }

    prev_row[len2]
}

/// Levenshtein similarity (normalized to 0-1 range)
pub fn levenshtein_similarity_native(s1: &str, s2: &str) -> f64 {
    let distance = levenshtein_distance_native(s1, s2);
    let max_len = s1.chars().count().max(s2.chars().count());

    if max_len == 0 {
        return 1.0;
    }

    1.0 - (distance as f64 / max_len as f64)
}

/// Jaccard similarity between two texts (native Rust)
pub fn jaccard_similarity_native(text1: &str, text2: &str) -> f64 {
    let tokens1: HashSet<String> = tokenize(text1).into_iter().collect();
    let tokens2: HashSet<String> = tokenize(text2).into_iter().collect();

    if tokens1.is_empty() && tokens2.is_empty() {
        return 1.0;
    }

    if tokens1.is_empty() || tokens2.is_empty() {
        return 0.0;
    }

    let intersection = tokens1.intersection(&tokens2).count();
    let union = tokens1.union(&tokens2).count();

    intersection as f64 / union as f64
}

/// BM25 scoring for a single document (native Rust)
pub fn bm25_score_native(
    query: &str,
    document: &str,
    k1: f64,
    b: f64,
    avg_doc_len: Option<f64>,
) -> f64 {
    let query_tokens = tokenize(query);
    let doc_tokens = tokenize(document);

    if query_tokens.is_empty() || doc_tokens.is_empty() {
        return 0.0;
    }

    let doc_len = doc_tokens.len() as f64;
    let avg_len = avg_doc_len.unwrap_or(doc_len);

    let doc_freq = build_term_freq(&doc_tokens);

    let mut score = 0.0;

    for term in &query_tokens {
        if let Some(&tf) = doc_freq.get(term) {
            let tf_component = (tf * (k1 + 1.0)) / (tf + k1 * (1.0 - b + b * (doc_len / avg_len)));
            score += tf_component;
        }
    }

    score
}

// ============================================================================
// PyO3 bindings (only when feature enabled)
// ============================================================================

#[cfg(feature = "pyo3")]
#[pyfunction]
fn cosine_similarity(text1: &str, text2: &str) -> PyResult<f64> {
    Ok(cosine_similarity_native(text1, text2))
}

#[cfg(feature = "pyo3")]
#[pyfunction]
fn levenshtein_distance(s1: &str, s2: &str) -> PyResult<usize> {
    Ok(levenshtein_distance_native(s1, s2))
}

#[cfg(feature = "pyo3")]
#[pyfunction]
fn levenshtein_similarity(s1: &str, s2: &str) -> PyResult<f64> {
    Ok(levenshtein_similarity_native(s1, s2))
}

#[cfg(feature = "pyo3")]
#[pyfunction]
fn jaccard_similarity(text1: &str, text2: &str) -> PyResult<f64> {
    Ok(jaccard_similarity_native(text1, text2))
}

#[cfg(feature = "pyo3")]
#[pyfunction]
#[pyo3(signature = (query, document, k1=1.5, b=0.75, avg_doc_len=None))]
fn bm25_score(
    query: &str,
    document: &str,
    k1: f64,
    b: f64,
    avg_doc_len: Option<f64>,
) -> PyResult<f64> {
    Ok(bm25_score_native(query, document, k1, b, avg_doc_len))
}

#[cfg(feature = "pyo3")]
#[pyfunction]
#[pyo3(signature = (query, documents, k1=1.5, b=0.75))]
fn bm25_rank(
    query: &str,
    documents: Vec<&str>,
    k1: f64,
    b: f64,
) -> PyResult<Vec<(usize, f64)>> {
    if documents.is_empty() {
        return Ok(Vec::new());
    }

    let query_tokens = tokenize(query);
    if query_tokens.is_empty() {
        return Ok(documents.iter().enumerate().map(|(i, _)| (i, 0.0)).collect());
    }

    let doc_tokens: Vec<Vec<String>> = documents.iter().map(|d| tokenize(d)).collect();
    let doc_freqs: Vec<AHashMap<String, f64>> = doc_tokens.iter().map(|t| build_term_freq(t)).collect();
    let doc_lens: Vec<f64> = doc_tokens.iter().map(|t| t.len() as f64).collect();
    let avg_doc_len: f64 = doc_lens.iter().sum::<f64>() / doc_lens.len() as f64;

    let n = documents.len() as f64;
    let mut idf: AHashMap<&String, f64> = AHashMap::new();

    for term in &query_tokens {
        let df = doc_freqs.iter().filter(|freq| freq.contains_key(term)).count() as f64;
        if df > 0.0 {
            let idf_score = ((n - df + 0.5) / (df + 0.5) + 1.0).ln();
            idf.insert(term, idf_score.max(0.0));
        }
    }

    let mut scores: Vec<(usize, f64)> = Vec::with_capacity(documents.len());

    for (i, (doc_freq, doc_len)) in doc_freqs.iter().zip(doc_lens.iter()).enumerate() {
        let mut score = 0.0;

        for term in &query_tokens {
            if let (Some(&tf), Some(&term_idf)) = (doc_freq.get(term), idf.get(term)) {
                let tf_component = (tf * (k1 + 1.0)) / (tf + k1 * (1.0 - b + b * (doc_len / avg_doc_len)));
                score += term_idf * tf_component;
            }
        }

        scores.push((i, score));
    }

    scores.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

    Ok(scores)
}

#[cfg(feature = "pyo3")]
#[pyfunction]
fn batch_cosine_similarity(query: &str, documents: Vec<&str>) -> PyResult<Vec<f64>> {
    let query_tokens = tokenize(query);
    if query_tokens.is_empty() {
        return Ok(vec![0.0; documents.len()]);
    }

    let query_freq = build_term_freq(&query_tokens);
    let query_mag: f64 = query_freq.values().map(|v| v * v).sum::<f64>().sqrt();

    let results: Vec<f64> = documents
        .iter()
        .map(|doc| {
            let doc_tokens = tokenize(doc);
            if doc_tokens.is_empty() {
                return 0.0;
            }

            let doc_freq = build_term_freq(&doc_tokens);

            let mut dot_product = 0.0;
            let mut doc_mag = 0.0;

            for (term, &count) in &doc_freq {
                doc_mag += count * count;
                if let Some(&query_count) = query_freq.get(term) {
                    dot_product += count * query_count;
                }
            }

            let doc_mag = doc_mag.sqrt();

            if doc_mag == 0.0 || query_mag == 0.0 {
                0.0
            } else {
                dot_product / (query_mag * doc_mag)
            }
        })
        .collect();

    Ok(results)
}

#[cfg(feature = "pyo3")]
#[pyfunction]
fn batch_levenshtein_distance(query: &str, documents: Vec<&str>) -> PyResult<Vec<usize>> {
    Ok(documents
        .iter()
        .map(|doc| levenshtein_distance_native(query, doc))
        .collect())
}

#[cfg(feature = "pyo3")]
#[pyfunction]
fn batch_jaccard_similarity(query: &str, documents: Vec<&str>) -> PyResult<Vec<f64>> {
    Ok(documents
        .iter()
        .map(|doc| jaccard_similarity_native(query, doc))
        .collect())
}

#[cfg(feature = "pyo3")]
#[pymodule]
fn text_similarity_rs(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(cosine_similarity, m)?)?;
    m.add_function(wrap_pyfunction!(levenshtein_distance, m)?)?;
    m.add_function(wrap_pyfunction!(levenshtein_similarity, m)?)?;
    m.add_function(wrap_pyfunction!(jaccard_similarity, m)?)?;
    m.add_function(wrap_pyfunction!(bm25_score, m)?)?;
    m.add_function(wrap_pyfunction!(bm25_rank, m)?)?;
    m.add_function(wrap_pyfunction!(batch_cosine_similarity, m)?)?;
    m.add_function(wrap_pyfunction!(batch_levenshtein_distance, m)?)?;
    m.add_function(wrap_pyfunction!(batch_jaccard_similarity, m)?)?;
    Ok(())
}
