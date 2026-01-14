"""
Comprehensive performance benchmarking for text similarity implementations.
Compares Pure Python, NumPy, Rust, and popular open-source libraries.
"""

import json
import time
import sys
import os
from typing import Dict, List, Callable, Any
import statistics

# Add python directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import pure_python
import numpy_impl
import opensource_libs

# Try to import Rust module
try:
    import text_similarity_rust
    HAS_RUST = True
except ImportError:
    HAS_RUST = False
    print("Warning: Rust module not available. Skipping Rust benchmarks.")


def time_function(func: Callable, *args, iterations: int = 100) -> Dict[str, float]:
    """
    Time a function execution.

    Returns:
        Dict with mean, median, min, max times in milliseconds
    """
    times = []

    # Warmup
    for _ in range(min(10, iterations)):
        func(*args)

    # Actual timing
    for _ in range(iterations):
        start = time.perf_counter()
        func(*args)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    return {
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "std_ms": statistics.stdev(times) if len(times) > 1 else 0,
    }


def benchmark_cosine_similarity(texts: List[str], iterations: int = 100) -> Dict:
    """Benchmark cosine similarity implementations."""
    results = {}

    print("  Benchmarking Cosine Similarity...")

    # Use pairs of texts
    pairs = [(texts[i], texts[i + 1]) for i in range(0, len(texts) - 1, 2)]

    # Pure Python
    print("    - Pure Python...")
    results["pure_python"] = time_function(
        lambda: [pure_python.cosine_similarity(t1, t2) for t1, t2 in pairs],
        iterations=iterations
    )

    # NumPy
    print("    - NumPy...")
    results["numpy"] = time_function(
        lambda: [numpy_impl.cosine_similarity(t1, t2) for t1, t2 in pairs],
        iterations=iterations
    )

    # Rust
    if HAS_RUST:
        print("    - Rust...")
        results["rust"] = time_function(
            lambda: [text_similarity_rust.cosine_similarity(t1, t2) for t1, t2 in pairs],
            iterations=iterations
        )

    # scikit-learn
    print("    - scikit-learn...")
    results["sklearn"] = time_function(
        lambda: [opensource_libs.cosine_similarity_sklearn(t1, t2) for t1, t2 in pairs],
        iterations=iterations
    )

    return results


def benchmark_levenshtein_distance(texts: List[str], iterations: int = 100) -> Dict:
    """Benchmark Levenshtein distance implementations."""
    results = {}

    print("  Benchmarking Levenshtein Distance...")

    # Use pairs of texts
    pairs = [(texts[i], texts[i + 1]) for i in range(0, len(texts) - 1, 2)]

    # Pure Python
    print("    - Pure Python...")
    results["pure_python"] = time_function(
        lambda: [pure_python.levenshtein_distance(t1, t2) for t1, t2 in pairs],
        iterations=iterations
    )

    # NumPy
    print("    - NumPy...")
    results["numpy"] = time_function(
        lambda: [numpy_impl.levenshtein_distance(t1, t2) for t1, t2 in pairs],
        iterations=iterations
    )

    # Rust
    if HAS_RUST:
        print("    - Rust...")
        results["rust"] = time_function(
            lambda: [text_similarity_rust.levenshtein_distance(t1, t2) for t1, t2 in pairs],
            iterations=iterations
        )

    # python-Levenshtein
    print("    - python-Levenshtein (C)...")
    results["python_levenshtein"] = time_function(
        lambda: [opensource_libs.levenshtein_distance_python(t1, t2) for t1, t2 in pairs],
        iterations=iterations
    )

    # rapidfuzz
    print("    - rapidfuzz (C++)...")
    results["rapidfuzz"] = time_function(
        lambda: [opensource_libs.levenshtein_distance_rapidfuzz(t1, t2) for t1, t2 in pairs],
        iterations=iterations
    )

    return results


def benchmark_jaccard_similarity(texts: List[str], iterations: int = 100) -> Dict:
    """Benchmark Jaccard similarity implementations."""
    results = {}

    print("  Benchmarking Jaccard Similarity...")

    # Use pairs of texts
    pairs = [(texts[i], texts[i + 1]) for i in range(0, len(texts) - 1, 2)]

    # Pure Python
    print("    - Pure Python...")
    results["pure_python"] = time_function(
        lambda: [pure_python.jaccard_similarity(t1, t2) for t1, t2 in pairs],
        iterations=iterations
    )

    # NumPy (same as pure Python for Jaccard)
    print("    - NumPy...")
    results["numpy"] = time_function(
        lambda: [numpy_impl.jaccard_similarity(t1, t2) for t1, t2 in pairs],
        iterations=iterations
    )

    # Rust
    if HAS_RUST:
        print("    - Rust...")
        results["rust"] = time_function(
            lambda: [text_similarity_rust.jaccard_similarity(t1, t2) for t1, t2 in pairs],
            iterations=iterations
        )

    return results


def benchmark_bm25(corpus: List[str], queries: List[str], iterations: int = 20) -> Dict:
    """Benchmark BM25 implementations."""
    results = {}

    print("  Benchmarking BM25...")

    # Pure Python
    print("    - Pure Python...")
    py_bm25 = pure_python.BM25(corpus)
    results["pure_python"] = time_function(
        lambda: [py_bm25.get_scores(q) for q in queries],
        iterations=iterations
    )

    # NumPy
    print("    - NumPy...")
    np_bm25 = numpy_impl.BM25(corpus)
    results["numpy"] = time_function(
        lambda: [np_bm25.get_scores(q) for q in queries],
        iterations=iterations
    )

    # Rust
    if HAS_RUST:
        print("    - Rust...")
        rust_bm25 = text_similarity_rust.BM25(corpus)
        results["rust"] = time_function(
            lambda: [rust_bm25.get_scores(q) for q in queries],
            iterations=iterations
        )

    # rank-bm25
    print("    - rank-bm25...")
    rankbm25 = opensource_libs.BM25RankBM25(corpus)
    results["rank_bm25"] = time_function(
        lambda: [rankbm25.get_scores(q) for q in queries],
        iterations=iterations
    )

    return results


def calculate_speedup(results: Dict, baseline: str = "pure_python") -> Dict:
    """Calculate speedup relative to baseline."""
    speedups = {}

    if baseline not in results:
        return speedups

    baseline_time = results[baseline]["mean_ms"]

    for impl, metrics in results.items():
        if impl == baseline:
            speedups[impl] = 1.0
        else:
            speedups[impl] = baseline_time / metrics["mean_ms"]

    return speedups


def run_all_benchmarks(dataset: Dict) -> Dict:
    """Run all benchmarks and return results."""
    all_results = {}

    print("\n" + "=" * 70)
    print("BENCHMARKING SHORT TEXTS (~100 chars)")
    print("=" * 70)

    all_results["short_cosine"] = benchmark_cosine_similarity(
        dataset["short_texts"][:20], iterations=200
    )
    all_results["short_levenshtein"] = benchmark_levenshtein_distance(
        dataset["short_texts"][:20], iterations=200
    )
    all_results["short_jaccard"] = benchmark_jaccard_similarity(
        dataset["short_texts"][:20], iterations=200
    )

    print("\n" + "=" * 70)
    print("BENCHMARKING MEDIUM TEXTS (~1000 chars)")
    print("=" * 70)

    all_results["medium_cosine"] = benchmark_cosine_similarity(
        dataset["medium_texts"][:20], iterations=100
    )
    all_results["medium_levenshtein"] = benchmark_levenshtein_distance(
        dataset["medium_texts"][:20], iterations=50
    )
    all_results["medium_jaccard"] = benchmark_jaccard_similarity(
        dataset["medium_texts"][:20], iterations=100
    )

    print("\n" + "=" * 70)
    print("BENCHMARKING LONG TEXTS (~10000 chars)")
    print("=" * 70)

    all_results["long_cosine"] = benchmark_cosine_similarity(
        dataset["long_texts"][:10], iterations=50
    )
    all_results["long_levenshtein"] = benchmark_levenshtein_distance(
        dataset["long_texts"][:6], iterations=10
    )
    all_results["long_jaccard"] = benchmark_jaccard_similarity(
        dataset["long_texts"][:10], iterations=50
    )

    print("\n" + "=" * 70)
    print("BENCHMARKING BM25")
    print("=" * 70)

    queries = [
        "machine learning algorithms",
        "data science and analysis",
        "artificial intelligence research",
        "computer vision applications",
        "natural language processing"
    ]

    all_results["bm25_small"] = benchmark_bm25(
        dataset["corpus_for_bm25"][:20], queries, iterations=50
    )
    all_results["bm25_large"] = benchmark_bm25(
        dataset["corpus_for_bm25"], queries, iterations=20
    )

    return all_results


def print_results_table(results: Dict):
    """Print formatted results table."""
    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS SUMMARY")
    print("=" * 80)

    for benchmark_name, benchmark_results in results.items():
        print(f"\n{benchmark_name}:")
        print(f"{'Implementation':<25} {'Mean (ms)':<15} {'Std Dev (ms)':<15} {'Speedup':<10}")
        print("-" * 80)

        speedups = calculate_speedup(benchmark_results)

        for impl, metrics in sorted(benchmark_results.items()):
            speedup = speedups.get(impl, 0)
            print(f"{impl:<25} {metrics['mean_ms']:>10.4f}     {metrics['std_ms']:>10.4f}     {speedup:>6.2f}x")


def save_results(results: Dict, filename: str):
    """Save results to JSON file."""
    # Add speedup information
    results_with_speedup = {}

    for benchmark_name, benchmark_results in results.items():
        speedups = calculate_speedup(benchmark_results)
        results_with_speedup[benchmark_name] = {
            "timings": benchmark_results,
            "speedups": speedups
        }

    with open(filename, 'w') as f:
        json.dump(results_with_speedup, f, indent=2)

    print(f"\nResults saved to {filename}")


def main():
    """Run benchmarks and save results."""
    print("Loading test data...")

    # Load dataset
    with open("benchmarks/test_data.json", 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    print(f"Loaded dataset with {len(dataset['short_texts'])} short texts, "
          f"{len(dataset['medium_texts'])} medium texts, "
          f"{len(dataset['long_texts'])} long texts")

    if not HAS_RUST:
        print("\n" + "!" * 70)
        print("WARNING: Rust module not found!")
        print("Run 'maturin develop --release' to build the Rust module")
        print("!" * 70)

    # Run benchmarks
    results = run_all_benchmarks(dataset)

    # Print summary
    print_results_table(results)

    # Save results
    save_results(results, "results/benchmark_results.json")

    print("\n" + "=" * 80)
    print("Benchmarking complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
