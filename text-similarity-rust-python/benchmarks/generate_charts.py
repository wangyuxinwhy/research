"""
Generate visualization charts from benchmark results.
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

def load_results(filename):
    """Load benchmark results from JSON file."""
    with open(filename, 'r') as f:
        return json.load(f)


def generate_performance_comparison(results, output_path):
    """Generate performance comparison bar chart."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Text Similarity Performance Comparison', fontsize=16, fontweight='bold')

    # Cosine Similarity - Short Texts
    ax = axes[0, 0]
    data = results['short_cosine']['timings']
    implementations = list(data.keys())
    times = [data[impl]['mean_ms'] for impl in implementations]

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
    bars = ax.bar(implementations, times, color=colors)
    ax.set_title('Cosine Similarity (Short Texts ~100 chars)', fontweight='bold')
    ax.set_ylabel('Time (ms)')
    ax.set_xlabel('Implementation')
    ax.tick_params(axis='x', rotation=45)

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}',
                ha='center', va='bottom', fontsize=9)

    # Levenshtein Distance - Short Texts
    ax = axes[0, 1]
    data = results['short_levenshtein']['timings']
    implementations = list(data.keys())
    times = [data[impl]['mean_ms'] for impl in implementations]

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#95E1D3', '#F38181']
    bars = ax.bar(implementations, times, color=colors)
    ax.set_title('Levenshtein Distance (Short Texts ~100 chars)', fontweight='bold')
    ax.set_ylabel('Time (ms)')
    ax.set_xlabel('Implementation')
    ax.tick_params(axis='x', rotation=45)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}',
                ha='center', va='bottom', fontsize=9)

    # Jaccard Similarity - Short Texts
    ax = axes[1, 0]
    data = results['short_jaccard']['timings']
    implementations = list(data.keys())
    times = [data[impl]['mean_ms'] for impl in implementations]

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    bars = ax.bar(implementations, times, color=colors)
    ax.set_title('Jaccard Similarity (Short Texts ~100 chars)', fontweight='bold')
    ax.set_ylabel('Time (ms)')
    ax.set_xlabel('Implementation')
    ax.tick_params(axis='x', rotation=45)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}',
                ha='center', va='bottom', fontsize=9)

    # BM25 - Small Corpus
    ax = axes[1, 1]
    data = results['bm25_small']['timings']
    implementations = list(data.keys())
    times = [data[impl]['mean_ms'] for impl in implementations]

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
    bars = ax.bar(implementations, times, color=colors)
    ax.set_title('BM25 (Small Corpus, 20 docs)', fontweight='bold')
    ax.set_ylabel('Time (ms)')
    ax.set_xlabel('Implementation')
    ax.tick_params(axis='x', rotation=45)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}',
                ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def generate_speedup_comparison(results, output_path):
    """Generate speedup ratio comparison chart."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Speedup Ratio vs Pure Python Baseline', fontsize=16, fontweight='bold')

    # Cosine Similarity Speedups
    ax = axes[0, 0]
    benchmarks = ['short_cosine', 'medium_cosine', 'long_cosine']
    benchmark_labels = ['Short\n(~100 chars)', 'Medium\n(~1000 chars)', 'Long\n(~10000 chars)']

    implementations = ['numpy', 'rust', 'sklearn']
    colors_map = {'numpy': '#4ECDC4', 'rust': '#45B7D1', 'sklearn': '#FFA07A'}

    x = np.arange(len(benchmarks))
    width = 0.25

    for i, impl in enumerate(implementations):
        speedups = [results[bench]['speedups'].get(impl, 0) for bench in benchmarks]
        offset = (i - len(implementations)/2 + 0.5) * width
        bars = ax.bar(x + offset, speedups, width, label=impl, color=colors_map[impl])

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.2f}x',
                        ha='center', va='bottom', fontsize=8)

    ax.set_ylabel('Speedup (times faster)')
    ax.set_title('Cosine Similarity Speedup', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(benchmark_labels)
    ax.legend()
    ax.axhline(y=1, color='r', linestyle='--', alpha=0.3, label='Baseline')

    # Levenshtein Distance Speedups
    ax = axes[0, 1]
    benchmarks = ['short_levenshtein', 'medium_levenshtein', 'long_levenshtein']

    implementations = ['numpy', 'rust', 'python_levenshtein', 'rapidfuzz']
    colors_map = {'numpy': '#4ECDC4', 'rust': '#45B7D1',
                  'python_levenshtein': '#95E1D3', 'rapidfuzz': '#F38181'}

    x = np.arange(len(benchmarks))
    width = 0.2

    for i, impl in enumerate(implementations):
        speedups = [results[bench]['speedups'].get(impl, 0) for bench in benchmarks]
        offset = (i - len(implementations)/2 + 0.5) * width
        bars = ax.bar(x + offset, speedups, width, label=impl, color=colors_map[impl])

        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}x',
                        ha='center', va='bottom', fontsize=7, rotation=0)

    ax.set_ylabel('Speedup (times faster)')
    ax.set_title('Levenshtein Distance Speedup', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(benchmark_labels)
    ax.legend(fontsize=8)
    ax.axhline(y=1, color='r', linestyle='--', alpha=0.3)

    # Jaccard Similarity Speedups
    ax = axes[1, 0]
    benchmarks = ['short_jaccard', 'medium_jaccard', 'long_jaccard']

    implementations = ['numpy', 'rust']
    colors_map = {'numpy': '#4ECDC4', 'rust': '#45B7D1'}

    x = np.arange(len(benchmarks))
    width = 0.3

    for i, impl in enumerate(implementations):
        speedups = [results[bench]['speedups'].get(impl, 0) for bench in benchmarks]
        offset = (i - len(implementations)/2 + 0.5) * width
        bars = ax.bar(x + offset, speedups, width, label=impl, color=colors_map[impl])

        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.2f}x',
                        ha='center', va='bottom', fontsize=8)

    ax.set_ylabel('Speedup (times faster)')
    ax.set_title('Jaccard Similarity Speedup', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(benchmark_labels)
    ax.legend()
    ax.axhline(y=1, color='r', linestyle='--', alpha=0.3)

    # BM25 Speedups
    ax = axes[1, 1]
    benchmarks = ['bm25_small', 'bm25_large']
    benchmark_labels = ['Small\n(20 docs)', 'Large\n(50 docs)']

    implementations = ['numpy', 'rust', 'rank_bm25']
    colors_map = {'numpy': '#4ECDC4', 'rust': '#45B7D1', 'rank_bm25': '#FFA07A'}

    x = np.arange(len(benchmarks))
    width = 0.25

    for i, impl in enumerate(implementations):
        speedups = [results[bench]['speedups'].get(impl, 0) for bench in benchmarks]
        offset = (i - len(implementations)/2 + 0.5) * width
        bars = ax.bar(x + offset, speedups, width, label=impl, color=colors_map[impl])

        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.2f}x',
                        ha='center', va='bottom', fontsize=8)

    ax.set_ylabel('Speedup (times faster)')
    ax.set_title('BM25 Speedup', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(benchmark_labels)
    ax.legend()
    ax.axhline(y=1, color='r', linestyle='--', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def generate_text_length_scaling(results, output_path):
    """Generate chart showing how performance scales with text length."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Performance Scaling with Text Length', fontsize=16, fontweight='bold')

    text_sizes = ['Short (~100)', 'Medium (~1000)', 'Long (~10000)']
    x = np.arange(len(text_sizes))

    # Cosine Similarity
    ax = axes[0, 0]
    benchmarks = ['short_cosine', 'medium_cosine', 'long_cosine']
    implementations = ['pure_python', 'numpy', 'rust']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

    for impl, color in zip(implementations, colors):
        times = [results[bench]['timings'][impl]['mean_ms'] for bench in benchmarks]
        ax.plot(x, times, marker='o', linewidth=2, markersize=8, label=impl, color=color)

    ax.set_yscale('log')
    ax.set_ylabel('Time (ms, log scale)')
    ax.set_title('Cosine Similarity', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(text_sizes)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Levenshtein Distance
    ax = axes[0, 1]
    benchmarks = ['short_levenshtein', 'medium_levenshtein', 'long_levenshtein']
    implementations = ['pure_python', 'numpy', 'rust', 'python_levenshtein', 'rapidfuzz']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#95E1D3', '#F38181']

    for impl, color in zip(implementations, colors):
        times = [results[bench]['timings'][impl]['mean_ms'] for bench in benchmarks]
        ax.plot(x, times, marker='o', linewidth=2, markersize=8, label=impl, color=color)

    ax.set_yscale('log')
    ax.set_ylabel('Time (ms, log scale)')
    ax.set_title('Levenshtein Distance', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(text_sizes)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Jaccard Similarity
    ax = axes[1, 0]
    benchmarks = ['short_jaccard', 'medium_jaccard', 'long_jaccard']
    implementations = ['pure_python', 'numpy', 'rust']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

    for impl, color in zip(implementations, colors):
        times = [results[bench]['timings'][impl]['mean_ms'] for bench in benchmarks]
        ax.plot(x, times, marker='o', linewidth=2, markersize=8, label=impl, color=color)

    ax.set_yscale('log')
    ax.set_ylabel('Time (ms, log scale)')
    ax.set_title('Jaccard Similarity', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(text_sizes)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # BM25
    ax = axes[1, 1]
    corpus_sizes = ['Small (20 docs)', 'Large (50 docs)']
    x = np.arange(len(corpus_sizes))
    benchmarks = ['bm25_small', 'bm25_large']
    implementations = ['pure_python', 'numpy', 'rust', 'rank_bm25']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']

    for impl, color in zip(implementations, colors):
        times = [results[bench]['timings'][impl]['mean_ms'] for bench in benchmarks]
        ax.plot(x, times, marker='o', linewidth=2, markersize=8, label=impl, color=color)

    ax.set_ylabel('Time (ms)')
    ax.set_title('BM25', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(corpus_sizes)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def main():
    """Generate all charts."""
    print("Loading benchmark results...")
    results = load_results('results/benchmark_results.json')

    output_dir = Path('results/charts')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\nGenerating charts...")

    print("1. Performance comparison chart...")
    generate_performance_comparison(
        results,
        output_dir / 'performance_comparison.png'
    )

    print("2. Speedup ratio chart...")
    generate_speedup_comparison(
        results,
        output_dir / 'speedup_ratio.png'
    )

    print("3. Text length scaling chart...")
    generate_text_length_scaling(
        results,
        output_dir / 'text_length_scaling.png'
    )

    print("\n✓ All charts generated successfully!")
    print(f"Charts saved in: {output_dir}")


if __name__ == "__main__":
    main()
