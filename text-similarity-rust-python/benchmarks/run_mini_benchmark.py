"""
Minimal benchmark - only essential tests with real data.
"""

import json
import time
import sys
import os
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import pure_python
import numpy_impl
import opensource_libs

try:
    import text_similarity_rust
    HAS_RUST = True
except ImportError:
    HAS_RUST = False

def time_it(func, iterations=10):
    """Quick timing."""
    times = []
    for _ in range(3):  # Warmup
        func()
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        times.append((time.perf_counter() - start) * 1000)
    return {
        "mean_ms": statistics.mean(times),
        "min_ms": min(times),
        "max_ms": max(times),
    }

def main():
    """Run minimal benchmarks."""
    with open("benchmarks/test_data.json", 'r') as f:
        dataset = json.load(f)

    results = {}

    # Short text tests
    print("Testing SHORT texts...")
    t1, t2 = dataset["short_texts"][0], dataset["short_texts"][1]

    print("  Cosine...")
    results["short_cosine"] = {
        "timings": {
            "pure_python": time_it(lambda: pure_python.cosine_similarity(t1, t2)),
            "numpy": time_it(lambda: numpy_impl.cosine_similarity(t1, t2)),
            "rust": time_it(lambda: text_similarity_rust.cosine_similarity(t1, t2)) if HAS_RUST else None,
        }
    }

    print("  Levenshtein...")
    results["short_lev"] = {
        "timings": {
            "pure_python": time_it(lambda: pure_python.levenshtein_distance(t1, t2)),
            "rust": time_it(lambda: text_similarity_rust.levenshtein_distance(t1, t2)) if HAS_RUST else None,
            "rapidfuzz": time_it(lambda: opensource_libs.levenshtein_distance_rapidfuzz(t1, t2)),
        }
    }

    # Medium text tests
    print("Testing MEDIUM texts...")
    t1, t2 = dataset["medium_texts"][0], dataset["medium_texts"][1]

    print("  Cosine...")
    results["medium_cosine"] = {
        "timings": {
            "pure_python": time_it(lambda: pure_python.cosine_similarity(t1, t2)),
            "numpy": time_it(lambda: numpy_impl.cosine_similarity(t1, t2)),
            "rust": time_it(lambda: text_similarity_rust.cosine_similarity(t1, t2)) if HAS_RUST else None,
        }
    }

    print("  Levenshtein...")
    results["medium_lev"] = {
        "timings": {
            "pure_python": time_it(lambda: pure_python.levenshtein_distance(t1, t2), iterations=5),
            "rust": time_it(lambda: text_similarity_rust.levenshtein_distance(t1, t2), iterations=5) if HAS_RUST else None,
            "rapidfuzz": time_it(lambda: opensource_libs.levenshtein_distance_rapidfuzz(t1, t2), iterations=5),
        }
    }

    # BM25
    print("Testing BM25...")
    corpus = dataset["corpus_for_bm25"][:10]
    query = "machine learning"

    py_bm25 = pure_python.BM25(corpus)
    np_bm25 = numpy_impl.BM25(corpus)
    rust_bm25 = text_similarity_rust.BM25(corpus) if HAS_RUST else None

    results["bm25"] = {
        "timings": {
            "pure_python": time_it(lambda: py_bm25.get_scores(query)),
            "numpy": time_it(lambda: np_bm25.get_scores(query)),
            "rust": time_it(lambda: rust_bm25.get_scores(query)) if HAS_RUST else None,
        }
    }

    # Calculate speedups
    for key in results:
        baseline = results[key]["timings"]["pure_python"]["mean_ms"]
        results[key]["speedups"] = {}
        for impl, timing in results[key]["timings"].items():
            if timing:
                results[key]["speedups"][impl] = baseline / timing["mean_ms"]

    # Save
    with open("results/mini_benchmark_results.json", 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("\n" + "="*60)
    print("MINI BENCHMARK RESULTS")
    print("="*60)
    for test_name, data in results.items():
        print(f"\n{test_name}:")
        for impl, timing in data["timings"].items():
            if timing:
                speedup = data["speedups"][impl]
                print(f"  {impl:20s}: {timing['mean_ms']:8.4f} ms  ({speedup:.2f}x)")

    print("\n✓ Complete!")

if __name__ == "__main__":
    main()
