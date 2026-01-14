#!/usr/bin/env python3
"""
Performance benchmark suite for text similarity implementations.

Measures execution time, throughput, and memory usage across all implementations.
"""

from __future__ import annotations

import gc
import json
import statistics
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.generate_data import generate_text, QUICK_TEST_SAMPLES
from python import pure_python, numpy_impl, opensource_libs


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    implementation: str
    algorithm: str
    text_length: str
    iterations: int
    total_time_ms: float
    mean_time_ms: float
    std_time_ms: float
    min_time_ms: float
    max_time_ms: float
    throughput_ops_per_sec: float


@dataclass
class BenchmarkSuite:
    """Collection of benchmark results."""
    results: list[BenchmarkResult]
    metadata: dict

    def to_dict(self) -> dict:
        return {
            "metadata": self.metadata,
            "results": [asdict(r) for r in self.results]
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


def benchmark_function(
    func: Callable,
    args: tuple,
    iterations: int = 100,
    warmup: int = 5
) -> BenchmarkResult:
    """
    Benchmark a function with given arguments.

    Args:
        func: Function to benchmark
        args: Arguments to pass to the function
        iterations: Number of iterations to run
        warmup: Number of warmup iterations

    Returns:
        BenchmarkResult with timing statistics
    """
    # Warmup runs
    for _ in range(warmup):
        func(*args)

    # Timed runs
    gc.disable()
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        func(*args)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    gc.enable()

    return BenchmarkResult(
        implementation="",  # Set by caller
        algorithm="",       # Set by caller
        text_length="",     # Set by caller
        iterations=iterations,
        total_time_ms=sum(times),
        mean_time_ms=statistics.mean(times),
        std_time_ms=statistics.stdev(times) if len(times) > 1 else 0,
        min_time_ms=min(times),
        max_time_ms=max(times),
        throughput_ops_per_sec=1000 / statistics.mean(times)
    )


def run_all_benchmarks(
    iterations: int = 100,
    verbose: bool = True
) -> BenchmarkSuite:
    """
    Run complete benchmark suite across all implementations and text lengths.
    """
    results: list[BenchmarkResult] = []

    # Text length configurations
    text_configs = {
        "short": 100,
        "medium": 1000,
        "long": 10000
    }

    # Generate test texts
    test_texts = {}
    for length_name, length_val in text_configs.items():
        test_texts[length_name] = (
            generate_text(length_val, mixed=True),
            generate_text(length_val, mixed=True)
        )

    # Implementations to test
    implementations = {
        "Pure Python": {
            "cosine": pure_python.cosine_similarity,
            "levenshtein": pure_python.levenshtein_distance,
            "jaccard": pure_python.jaccard_similarity,
            "bm25_score": pure_python.bm25_score,
        },
        "NumPy": {
            "cosine": numpy_impl.cosine_similarity,
            "levenshtein": numpy_impl.levenshtein_distance,
            "jaccard": numpy_impl.jaccard_similarity,
            "bm25_score": numpy_impl.bm25_score,
        },
        "rapidfuzz": {
            "levenshtein": opensource_libs.levenshtein_distance_rapidfuzz,
        },
        "python-Levenshtein": {
            "levenshtein": opensource_libs.levenshtein_distance_pylev,
        },
        "scikit-learn": {
            "cosine": opensource_libs.cosine_similarity_sklearn,
        },
        "rank-bm25": {
            "bm25_score": opensource_libs.bm25_score_rankbm25,
        },
    }

    # Try to import Rust implementation
    try:
        import text_similarity_rs
        implementations["Rust (PyO3)"] = {
            "cosine": text_similarity_rs.cosine_similarity,
            "levenshtein": text_similarity_rs.levenshtein_distance,
            "jaccard": text_similarity_rs.jaccard_similarity,
            "bm25_score": text_similarity_rs.bm25_score,
        }
        if verbose:
            print("✓ Rust module loaded successfully")
    except ImportError:
        if verbose:
            print("⚠ Rust module not available. Run 'maturin develop --release' to build it.")

    # Run benchmarks
    total_benchmarks = sum(
        len(algos) * len(text_configs)
        for algos in implementations.values()
    )
    current = 0

    for impl_name, algorithms in implementations.items():
        for algo_name, func in algorithms.items():
            for length_name, (text1, text2) in test_texts.items():
                current += 1

                if verbose:
                    print(f"[{current}/{total_benchmarks}] {impl_name} - {algo_name} - {length_name}...", end=" ", flush=True)

                try:
                    # Adjust iterations based on algorithm and text length
                    iters = iterations

                    # Levenshtein is O(n*m), extremely slow for long text
                    if algo_name == "levenshtein":
                        if length_name == "long":
                            # Skip pure Python/NumPy Levenshtein for long text (too slow)
                            if impl_name in ("Pure Python", "NumPy"):
                                if verbose:
                                    print("SKIPPED (too slow)")
                                continue
                            iters = max(5, iterations // 20)
                        elif length_name == "medium":
                            if impl_name in ("Pure Python", "NumPy"):
                                iters = max(5, iterations // 20)
                            else:
                                iters = max(10, iterations // 10)
                    elif length_name == "long":
                        iters = max(10, iterations // 10)

                    result = benchmark_function(func, (text1, text2), iterations=iters)
                    result.implementation = impl_name
                    result.algorithm = algo_name
                    result.text_length = length_name
                    results.append(result)

                    if verbose:
                        print(f"{result.mean_time_ms:.3f} ms")

                except Exception as e:
                    if verbose:
                        print(f"ERROR: {e}")

    # Collect metadata
    import platform
    metadata = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "iterations": iterations,
        "text_lengths": text_configs,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    return BenchmarkSuite(results=results, metadata=metadata)


def run_batch_benchmarks(
    iterations: int = 50,
    num_documents: int = 100,
    verbose: bool = True
) -> BenchmarkSuite:
    """
    Run batch operation benchmarks (one query vs multiple documents).
    """
    results: list[BenchmarkResult] = []

    text_configs = {
        "short": 100,
        "medium": 1000,
    }

    # Generate test data
    test_data = {}
    for length_name, length_val in text_configs.items():
        query = generate_text(length_val // 2, mixed=True)
        documents = [generate_text(length_val, mixed=True) for _ in range(num_documents)]
        test_data[length_name] = (query, documents)

    implementations = {
        "Pure Python": {
            "batch_cosine": pure_python.batch_cosine_similarity,
            "batch_levenshtein": pure_python.batch_levenshtein_distance,
            "batch_jaccard": pure_python.batch_jaccard_similarity,
            "bm25_rank": pure_python.bm25_rank,
        },
        "NumPy": {
            "batch_cosine": numpy_impl.batch_cosine_similarity,
            "batch_levenshtein": numpy_impl.batch_levenshtein_distance,
            "batch_jaccard": numpy_impl.batch_jaccard_similarity,
            "bm25_rank": numpy_impl.bm25_rank,
        },
        "scikit-learn": {
            "batch_cosine": opensource_libs.batch_cosine_similarity_sklearn,
        },
        "rapidfuzz": {
            "batch_levenshtein": opensource_libs.batch_levenshtein_distance_rapidfuzz,
        },
        "rank-bm25": {
            "bm25_rank": opensource_libs.bm25_rank_rankbm25,
        },
    }

    try:
        import text_similarity_rs
        implementations["Rust (PyO3)"] = {
            "batch_cosine": text_similarity_rs.batch_cosine_similarity,
            "batch_levenshtein": text_similarity_rs.batch_levenshtein_distance,
            "batch_jaccard": text_similarity_rs.batch_jaccard_similarity,
            "bm25_rank": text_similarity_rs.bm25_rank,
        }
    except ImportError:
        pass

    for impl_name, algorithms in implementations.items():
        for algo_name, func in algorithms.items():
            for length_name, (query, documents) in test_data.items():
                if verbose:
                    print(f"{impl_name} - {algo_name} - {length_name} (batch)...", end=" ", flush=True)

                try:
                    result = benchmark_function(func, (query, documents), iterations=iterations)
                    result.implementation = impl_name
                    result.algorithm = algo_name
                    result.text_length = length_name
                    results.append(result)

                    if verbose:
                        print(f"{result.mean_time_ms:.3f} ms")

                except Exception as e:
                    if verbose:
                        print(f"ERROR: {e}")

    import platform
    metadata = {
        "type": "batch_benchmarks",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "num_documents": num_documents,
        "iterations": iterations,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    return BenchmarkSuite(results=results, metadata=metadata)


def print_summary(suite: BenchmarkSuite) -> None:
    """Print a formatted summary of benchmark results."""
    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)

    # Group by algorithm and text length
    from collections import defaultdict
    grouped = defaultdict(list)

    for r in suite.results:
        key = (r.algorithm, r.text_length)
        grouped[key].append(r)

    for (algo, length), results in sorted(grouped.items()):
        print(f"\n{algo.upper()} ({length} text)")
        print("-" * 60)

        # Sort by mean time
        results.sort(key=lambda x: x.mean_time_ms)

        baseline = results[-1].mean_time_ms  # Slowest as baseline

        for r in results:
            speedup = baseline / r.mean_time_ms if r.mean_time_ms > 0 else 0
            print(f"  {r.implementation:20s}: {r.mean_time_ms:10.3f} ms  "
                  f"(±{r.std_time_ms:6.3f})  [{speedup:5.1f}x]")


def compute_speedup_table(suite: BenchmarkSuite) -> dict:
    """Compute speedup ratios relative to Pure Python baseline."""
    from collections import defaultdict

    speedups = defaultdict(dict)

    for r in suite.results:
        key = (r.algorithm, r.text_length)
        speedups[key][r.implementation] = r.mean_time_ms

    result = {}
    for (algo, length), times in speedups.items():
        baseline = times.get("Pure Python", 1)
        result[f"{algo}_{length}"] = {
            impl: baseline / t if t > 0 else 0
            for impl, t in times.items()
        }

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run text similarity benchmarks")
    parser.add_argument("--iterations", "-n", type=int, default=100,
                       help="Number of iterations per benchmark")
    parser.add_argument("--output", "-o", type=Path,
                       default=Path(__file__).parent.parent / "results" / "benchmark_results.json",
                       help="Output path for results")
    parser.add_argument("--batch", action="store_true",
                       help="Also run batch benchmarks")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Suppress progress output")

    args = parser.parse_args()

    print("Running single-operation benchmarks...")
    suite = run_all_benchmarks(iterations=args.iterations, verbose=not args.quiet)
    suite.save(args.output)

    if args.batch:
        print("\nRunning batch benchmarks...")
        batch_suite = run_batch_benchmarks(iterations=args.iterations // 2, verbose=not args.quiet)
        batch_output = args.output.parent / "batch_benchmark_results.json"
        batch_suite.save(batch_output)

    print_summary(suite)

    # Save speedup table
    speedups = compute_speedup_table(suite)
    speedup_path = args.output.parent / "speedup_table.json"
    with open(speedup_path, 'w') as f:
        json.dump(speedups, f, indent=2)

    print(f"\nResults saved to {args.output}")
    print(f"Speedup table saved to {speedup_path}")
