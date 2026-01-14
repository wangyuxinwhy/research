use pyo3::prelude::*;
use std::collections::{HashMap, HashSet};
use std::cmp::min;

/// Calculate cosine similarity between two texts using character-level vectors.
#[pyfunction]
fn cosine_similarity(text1: &str, text2: &str) -> PyResult<f64> {
    if text1.is_empty() || text2.is_empty() {
        return Ok(0.0);
    }

    // Build character frequency maps
    let mut freq1: HashMap<char, i32> = HashMap::new();
    let mut freq2: HashMap<char, i32> = HashMap::new();

    for ch in text1.chars() {
        *freq1.entry(ch).or_insert(0) += 1;
    }

    for ch in text2.chars() {
        *freq2.entry(ch).or_insert(0) += 1;
    }

    // Get all unique characters
    let all_chars: HashSet<&char> = freq1.keys().chain(freq2.keys()).collect();

    // Calculate dot product and magnitudes
    let mut dot_product = 0.0;
    let mut magnitude1 = 0.0;
    let mut magnitude2 = 0.0;

    for &ch in all_chars {
        let count1 = *freq1.get(&ch).unwrap_or(&0) as f64;
        let count2 = *freq2.get(&ch).unwrap_or(&0) as f64;

        dot_product += count1 * count2;
        magnitude1 += count1 * count1;
        magnitude2 += count2 * count2;
    }

    magnitude1 = magnitude1.sqrt();
    magnitude2 = magnitude2.sqrt();

    if magnitude1 == 0.0 || magnitude2 == 0.0 {
        return Ok(0.0);
    }

    Ok(dot_product / (magnitude1 * magnitude2))
}

/// Calculate Levenshtein edit distance between two texts.
#[pyfunction]
fn levenshtein_distance(text1: &str, text2: &str) -> PyResult<usize> {
    let len1 = text1.chars().count();
    let len2 = text2.chars().count();

    if len1 == 0 {
        return Ok(len2);
    }
    if len2 == 0 {
        return Ok(len1);
    }

    let chars1: Vec<char> = text1.chars().collect();
    let chars2: Vec<char> = text2.chars().collect();

    // Initialize DP matrix
    let mut dp = vec![vec![0usize; len2 + 1]; len1 + 1];

    // Base cases
    for i in 0..=len1 {
        dp[i][0] = i;
    }
    for j in 0..=len2 {
        dp[0][j] = j;
    }

    // Fill DP matrix
    for i in 1..=len1 {
        for j in 1..=len2 {
            if chars1[i - 1] == chars2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1];
            } else {
                dp[i][j] = 1 + min(
                    min(dp[i - 1][j], dp[i][j - 1]),
                    dp[i - 1][j - 1]
                );
            }
        }
    }

    Ok(dp[len1][len2])
}

/// Calculate normalized Levenshtein similarity.
#[pyfunction]
fn levenshtein_similarity(text1: &str, text2: &str) -> PyResult<f64> {
    let len1 = text1.chars().count();
    let len2 = text2.chars().count();

    if len1 == 0 && len2 == 0 {
        return Ok(1.0);
    }
    if len1 == 0 || len2 == 0 {
        return Ok(0.0);
    }

    let distance = levenshtein_distance(text1, text2)?;
    let max_len = std::cmp::max(len1, len2);

    Ok(1.0 - (distance as f64 / max_len as f64))
}

/// Extract n-grams from text.
fn get_ngrams(text: &str, n: usize) -> HashSet<String> {
    let chars: Vec<char> = text.chars().collect();
    let len = chars.len();

    if len < n {
        return vec![text.to_string()].into_iter().collect();
    }

    let mut ngrams = HashSet::new();
    for i in 0..=(len - n) {
        let ngram: String = chars[i..i + n].iter().collect();
        ngrams.insert(ngram);
    }

    ngrams
}

/// Calculate Jaccard similarity using character n-grams.
#[pyfunction]
fn jaccard_similarity(text1: &str, text2: &str, n: Option<usize>) -> PyResult<f64> {
    let n = n.unwrap_or(2);

    if text1.is_empty() || text2.is_empty() {
        return Ok(0.0);
    }

    let ngrams1 = get_ngrams(text1, n);
    let ngrams2 = get_ngrams(text2, n);

    let intersection: HashSet<_> = ngrams1.intersection(&ngrams2).collect();
    let union: HashSet<_> = ngrams1.union(&ngrams2).collect();

    if union.is_empty() {
        return Ok(0.0);
    }

    Ok(intersection.len() as f64 / union.len() as f64)
}

/// BM25 ranking algorithm implementation.
#[pyclass]
struct BM25 {
    corpus: Vec<String>,
    tokenized_corpus: Vec<Vec<String>>,
    doc_lengths: Vec<usize>,
    avg_doc_length: f64,
    vocab: HashMap<String, usize>,
    idf: Vec<f64>,
    k1: f64,
    b: f64,
}

#[pymethods]
impl BM25 {
    /// Create a new BM25 instance with a corpus of documents.
    #[new]
    fn new(corpus: Vec<String>, k1: Option<f64>, b: Option<f64>) -> Self {
        let k1 = k1.unwrap_or(1.5);
        let b = b.unwrap_or(0.75);

        // Tokenize corpus
        let tokenized_corpus: Vec<Vec<String>> = corpus
            .iter()
            .map(|doc| {
                doc.to_lowercase()
                    .split_whitespace()
                    .map(String::from)
                    .collect()
            })
            .collect();

        // Calculate document lengths
        let doc_lengths: Vec<usize> = tokenized_corpus.iter().map(|doc| doc.len()).collect();
        let avg_doc_length = if !doc_lengths.is_empty() {
            doc_lengths.iter().sum::<usize>() as f64 / doc_lengths.len() as f64
        } else {
            0.0
        };

        // Build vocabulary and calculate IDF
        let mut vocab: HashMap<String, usize> = HashMap::new();
        let mut doc_frequencies: HashMap<String, usize> = HashMap::new();

        for doc in &tokenized_corpus {
            let unique_terms: HashSet<_> = doc.iter().collect();
            for term in unique_terms {
                *doc_frequencies.entry(term.clone()).or_insert(0) += 1;
            }
        }

        let mut vocab_list: Vec<String> = doc_frequencies.keys().cloned().collect();
        vocab_list.sort();

        for (idx, term) in vocab_list.iter().enumerate() {
            vocab.insert(term.clone(), idx);
        }

        // Calculate IDF values
        let corpus_size = corpus.len() as f64;
        let mut idf = vec![0.0; vocab.len()];

        for (term, idx) in &vocab {
            let df = *doc_frequencies.get(term).unwrap_or(&0) as f64;
            idf[*idx] = ((corpus_size - df + 0.5) / (df + 0.5) + 1.0).ln();
        }

        BM25 {
            corpus,
            tokenized_corpus,
            doc_lengths,
            avg_doc_length,
            vocab,
            idf,
            k1,
            b,
        }
    }

    /// Calculate BM25 scores for all documents given a query.
    fn get_scores(&self, query: &str) -> PyResult<Vec<f64>> {
        let query_terms: Vec<String> = query
            .to_lowercase()
            .split_whitespace()
            .map(String::from)
            .collect();

        let mut scores = vec![0.0; self.corpus.len()];

        for (doc_idx, doc) in self.tokenized_corpus.iter().enumerate() {
            let doc_length = self.doc_lengths[doc_idx] as f64;
            let mut term_frequencies: HashMap<&String, usize> = HashMap::new();

            for term in doc {
                *term_frequencies.entry(term).or_insert(0) += 1;
            }

            for query_term in &query_terms {
                if let Some(&term_idx) = self.vocab.get(query_term) {
                    let tf = *term_frequencies.get(&query_term).unwrap_or(&0) as f64;
                    let idf = self.idf[term_idx];

                    // BM25 formula
                    let numerator = tf * (self.k1 + 1.0);
                    let denominator = tf + self.k1 * (1.0 - self.b + self.b * doc_length / self.avg_doc_length);

                    scores[doc_idx] += idf * (numerator / denominator);
                }
            }
        }

        Ok(scores)
    }

    /// Get top N documents for a query.
    fn get_top_n(&self, query: &str, n: Option<usize>) -> PyResult<Vec<(usize, f64)>> {
        let n = n.unwrap_or(10);
        let scores = self.get_scores(query)?;

        let mut scored_docs: Vec<(usize, f64)> = scores
            .into_iter()
            .enumerate()
            .collect();

        scored_docs.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());

        Ok(scored_docs.into_iter().take(n).collect())
    }
}

/// Calculate BM25 similarity between a query and a single document.
#[pyfunction]
fn bm25_similarity(query: &str, document: &str, k1: Option<f64>, b: Option<f64>) -> PyResult<f64> {
    let bm25 = BM25::new(vec![document.to_string()], k1, b);
    let scores = bm25.get_scores(query)?;
    Ok(scores.get(0).copied().unwrap_or(0.0))
}

/// Python module definition.
#[pymodule]
fn text_similarity_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(cosine_similarity, m)?)?;
    m.add_function(wrap_pyfunction!(levenshtein_distance, m)?)?;
    m.add_function(wrap_pyfunction!(levenshtein_similarity, m)?)?;
    m.add_function(wrap_pyfunction!(jaccard_similarity, m)?)?;
    m.add_function(wrap_pyfunction!(bm25_similarity, m)?)?;
    m.add_class::<BM25>()?;
    Ok(())
}
