#!/usr/bin/env python3
"""
Compare Native Rust vs PyO3 binding overhead.

Parses Criterion benchmark results and compares with PyO3 Python benchmarks.
"""

import json
import re
import subprocess
from pathlib import Path

# Native Rust results from Criterion (in microseconds)
# Extracted from: cargo bench --no-default-features
NATIVE_RUST_RESULTS = {
    "cosine": {
        "short": 10.95,   # µs
        "medium": 105.34,
        "long": 655.60,
    },
    "levenshtein": {
        "short": 57.27,
        "medium": 1667.1,
        # long: skipped (too slow)
    },
    "jaccard": {
        "short": 7.21,
        "medium": 66.34,
        "long": 567.75,
    },
    "bm25_score": {
        "short": 7.08,
        "medium": 62.73,
        "long": 578.08,
    },
}


def load_pyo3_results(path: Path) -> dict:
    """Load PyO3 benchmark results."""
    with open(path) as f:
        data = json.load(f)

    results = {}
    for r in data["results"]:
        if r["implementation"] == "Rust (PyO3)":
            algo = r["algorithm"]
            length = r["text_length"]
            if algo not in results:
                results[algo] = {}
            # Convert ms to µs for comparison
            results[algo][length] = r["mean_time_ms"] * 1000
    return results


def compare_overhead():
    """Compare Native Rust vs PyO3 overhead."""
    # Load PyO3 results
    pyo3_path = Path(__file__).parent.parent / "results" / "benchmark_results.json"
    pyo3_results = load_pyo3_results(pyo3_path)

    print("=" * 80)
    print("Native Rust vs PyO3 Binding Overhead Analysis")
    print("=" * 80)
    print()
    print("All times in microseconds (µs)")
    print()

    algorithms = ["cosine", "jaccard", "bm25_score", "levenshtein"]
    lengths = ["short", "medium", "long"]

    # Summary data for chart generation
    summary = {
        "algorithms": algorithms,
        "lengths": lengths,
        "native_rust": NATIVE_RUST_RESULTS,
        "pyo3": pyo3_results,
        "overhead": {}
    }

    for algo in algorithms:
        print(f"\n{algo.upper()}")
        print("-" * 60)
        print(f"{'Length':<12} {'Native Rust':>12} {'PyO3':>12} {'Overhead':>12}")
        print("-" * 60)

        summary["overhead"][algo] = {}

        for length in lengths:
            native = NATIVE_RUST_RESULTS.get(algo, {}).get(length)
            pyo3 = pyo3_results.get(algo, {}).get(length)

            if native and pyo3:
                overhead = pyo3 / native
                overhead_pct = (pyo3 - native) / native * 100
                summary["overhead"][algo][length] = overhead

                print(f"{length:<12} {native:>12.2f} {pyo3:>12.2f} {overhead:>10.2f}x ({overhead_pct:+.0f}%)")
            elif native:
                print(f"{length:<12} {native:>12.2f} {'N/A':>12} {'N/A':>12}")
            elif pyo3:
                print(f"{length:<12} {'N/A':>12} {pyo3:>12.2f} {'N/A':>12}")

    # Calculate average overhead
    print("\n" + "=" * 80)
    print("SUMMARY: Average PyO3 Overhead")
    print("=" * 80)

    all_overheads = []
    for algo, lengths_data in summary["overhead"].items():
        for length, overhead in lengths_data.items():
            all_overheads.append((algo, length, overhead))

    for algo, length, overhead in sorted(all_overheads, key=lambda x: x[2], reverse=True):
        print(f"  {algo:>12} ({length:>6}): {overhead:.2f}x overhead")

    avg_overhead = sum(o for _, _, o in all_overheads) / len(all_overheads)
    print(f"\n  Average overhead: {avg_overhead:.2f}x")
    print(f"  Overhead range: {min(o for _, _, o in all_overheads):.2f}x - {max(o for _, _, o in all_overheads):.2f}x")

    # Save summary
    summary_path = Path(__file__).parent.parent / "results" / "pyo3_overhead.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults saved to {summary_path}")

    return summary


def generate_overhead_chart(summary: dict):
    """Generate chart comparing Native Rust vs PyO3."""
    import matplotlib.pyplot as plt
    import numpy as np

    algorithms = ["cosine", "jaccard", "bm25_score"]
    lengths = ["short", "medium", "long"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for idx, length in enumerate(lengths):
        ax = axes[idx]

        native_times = []
        pyo3_times = []
        algo_names = []

        for algo in algorithms:
            native = summary["native_rust"].get(algo, {}).get(length)
            pyo3 = summary["pyo3"].get(algo, {}).get(length)
            if native and pyo3:
                native_times.append(native)
                pyo3_times.append(pyo3)
                algo_names.append(algo.replace("_", "\n"))

        x = np.arange(len(algo_names))
        width = 0.35

        bars1 = ax.bar(x - width/2, native_times, width, label='Native Rust', color='#2ecc71')
        bars2 = ax.bar(x + width/2, pyo3_times, width, label='PyO3 Binding', color='#3498db')

        # Add overhead labels
        for i, (n, p) in enumerate(zip(native_times, pyo3_times)):
            overhead = p / n
            ax.annotate(f'{overhead:.1f}x',
                       xy=(i + width/2, p),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', fontsize=9, color='red')

        ax.set_ylabel('Time (µs)')
        length_chars = {"short": 100, "medium": 1000, "long": 10000}
        ax.set_title(f'{length.capitalize()} Text (~{length_chars[length]} chars)')
        ax.set_xticks(x)
        ax.set_xticklabels(algo_names)
        ax.legend()

        if length == "long":
            ax.set_yscale('log')

    plt.suptitle('Native Rust vs PyO3 Binding Performance', fontsize=14, y=1.02)
    plt.tight_layout()

    chart_path = Path(__file__).parent.parent / "results" / "charts" / "pyo3_overhead.png"
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Chart saved to {chart_path}")


if __name__ == "__main__":
    summary = compare_overhead()

    try:
        generate_overhead_chart(summary)
    except ImportError:
        print("\nNote: matplotlib not available, skipping chart generation")
