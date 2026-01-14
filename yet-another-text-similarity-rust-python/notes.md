# Development Notes

This document records the development process, decisions made, problems encountered, and lessons learned during this research project.

## Project Setup

### Initial Structure
Created the project with the following components:
- `src/lib.rs` - Rust implementations with PyO3 bindings
- `python/` - Python implementations (pure, numpy, opensource wrappers)
- `tests/` - Correctness tests using pytest
- `benchmarks/` - Performance measurement and visualization

### Dependency Choices

**Rust Dependencies:**
- `pyo3 = "0.20"` - Python bindings (pinned to 0.20 for stability)
- `unicode-segmentation = "1.10"` - Proper Unicode word segmentation
- `ahash = "0.8"` - Fast hash map implementation

**Python Dependencies:**
- `rapidfuzz` - Fastest Levenshtein implementation (C++ with SIMD)
- `python-Levenshtein` - Alternative C implementation
- `scikit-learn` - For cosine similarity comparison
- `rank-bm25` - Popular BM25 library for comparison

## Technical Decisions

### 1. Chinese Text Tokenization

**Problem:** Initial tokenization using `\w+` regex treated entire Chinese phrases as single tokens, while Rust's `unicode-segmentation` split them into individual characters.

**Solution:** Modified Python tokenizer to handle CJK characters specially:
```python
def tokenize(text: str) -> list[str]:
    tokens = []
    for segment in re.findall(r'[\w]+', text.lower(), re.UNICODE):
        has_cjk = any('\u4e00' <= c <= '\u9fff' for c in segment)
        if has_cjk:
            # Split CJK characters individually
            for c in segment:
                if '\u4e00' <= c <= '\u9fff':
                    tokens.append(c)
                # ... handle non-CJK in segment
        else:
            tokens.append(segment)
    return tokens
```

**Trade-off:** This isn't linguistically accurate Chinese segmentation (would need jieba or similar), but it ensures consistency between Python and Rust implementations for benchmarking purposes.

### 2. PyO3 API Version

**Problem:** Initially used PyO3 0.20 `Bound` API which caused compilation errors:
```rust
// This didn't work in PyO3 0.20
fn text_similarity_rs(m: &Bound<'_, PyModule>) -> PyResult<()>
```

**Solution:** Used the older API style:
```rust
fn text_similarity_rs(_py: Python<'_>, m: &PyModule) -> PyResult<()>
```

**Lesson:** Always check PyO3 version compatibility. The API changed significantly between versions.

### 3. Benchmark Design

**Problem:** Long text Levenshtein distance is O(n*m), making pure Python benchmarks take minutes/hours.

**Solution:**
- Skip pure Python/NumPy Levenshtein for long texts
- Reduce iterations for slow tests
- Use adaptive iteration counts based on algorithm and text length

```python
if algo_name == "levenshtein" and length_name == "long":
    if impl_name in ("Pure Python", "NumPy"):
        print("SKIPPED (too slow)")
        continue
```

### 4. Hash Map Choice in Rust

**Decision:** Used `ahash::AHashMap` instead of `std::collections::HashMap`.

**Reasoning:**
- ahash is significantly faster for small keys (like word strings)
- Reduces overhead in term frequency counting
- Important for overall performance in cosine/BM25 calculations

## Problems Encountered

### 1. Maturin Virtual Environment

**Error:** `maturin develop` required a virtual environment
```
Couldn't find a virtualenv or conda environment
```

**Solution:** Created `.venv` and activated it before building:
```bash
python -m venv .venv
source .venv/bin/activate
maturin develop --release
```

### 2. Missing README.md

**Error:** maturin failed because `pyproject.toml` referenced a non-existent README:
```
Failed to read readme specified in pyproject.toml
```

**Solution:** Created README.md before building Rust extension.

### 3. NumPy Levenshtein Performance

**Observation:** NumPy implementation was actually SLOWER than pure Python for Levenshtein.

**Analysis:**
- Levenshtein requires sequential dependencies (each cell depends on previous)
- NumPy's strength is vectorized operations, not sequential iteration
- Array creation overhead exceeded any potential gains
- Pure Python with simple lists performed better

**Lesson:** NumPy is not a universal performance improvement. The algorithm structure matters.

## Performance Observations

### Surprising Results

1. **Rust Levenshtein slower than rapidfuzz**
   - rapidfuzz uses SIMD instructions (SSE4.2, AVX2)
   - Our Rust implementation is basic scalar code
   - ~60x slower than rapidfuzz on long strings

2. **rank-bm25 unexpectedly slow**
   - Our pure Python BM25 is 15x faster than rank-bm25
   - Rust is 30-55x faster than rank-bm25
   - rank-bm25 has overhead from its general-purpose design

3. **scikit-learn overhead for small texts**
   - For short texts, sklearn's CountVectorizer setup dominates
   - Pure Python is 17x faster for 100-char texts
   - sklearn only becomes competitive for longer texts

### Performance Scaling

| Algorithm | Complexity | Bottleneck |
|-----------|------------|------------|
| Cosine | O(n) | Tokenization |
| Jaccard | O(n) | Set operations |
| BM25 | O(n) | Tokenization + scoring |
| Levenshtein | O(n*m) | Character comparison loop |

## What Worked Well

1. **PyO3 integration** - Clean, easy to use, good performance
2. **maturin** - Simplified build process significantly
3. **Unicode segmentation crate** - Correct handling of multilingual text
4. **ahash** - Noticeable performance boost for hash operations
5. **Test-driven approach** - Caught tokenization mismatch early

## What Could Be Improved

1. **SIMD in Rust** - Could add explicit SIMD for Levenshtein
2. **Parallel processing** - Batch operations could use Rayon
3. **Memory efficiency** - Could optimize string allocations
4. **Real Chinese segmentation** - Use jieba for linguistically correct tokenization

## Lessons Learned

1. **Don't assume NumPy is always faster** - Algorithm structure matters more than language
2. **Specialized libraries can beat general implementations** - rapidfuzz's SIMD beats our Rust
3. **Measure before optimizing** - Our expectations about rank-bm25 were wrong
4. **PyO3 version matters** - API changes can cause confusing compilation errors
5. **Consistent tokenization is crucial** - Small differences cause test failures

## Future Research Ideas

1. Add SIMD to Rust Levenshtein using `std::arch` or `packed_simd`
2. Benchmark batch processing with Rayon parallelization
3. Compare memory usage with `memory_profiler`
4. Test on ARM architecture (M1/M2)
5. Add more algorithms (TF-IDF, Word Mover's Distance)

## Time Log

- Project setup: 30 min
- Python implementations: 45 min
- Rust implementation: 60 min
- Debugging tokenization mismatch: 30 min
- Fixing PyO3 API issue: 15 min
- Benchmark design and execution: 45 min
- Chart generation: 20 min
- Documentation: 30 min

Total: ~4.5 hours
