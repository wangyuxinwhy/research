#!/usr/bin/env python3
"""
Generate visualization charts from benchmark results.

Creates:
1. Performance comparison bar charts
2. Speedup ratio charts
3. Text length scaling charts
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


def load_results(path: Path) -> dict:
    """Load benchmark results from JSON file."""
    with open(path) as f:
        return json.load(f)


def setup_style():
    """Set up matplotlib style for consistent, publication-quality plots."""
    plt.style.use('seaborn-v0_8-whitegrid')
    sns.set_palette("husl")

    plt.rcParams.update({
        'figure.figsize': (12, 8),
        'figure.dpi': 150,
        'font.size': 11,
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.titlesize': 16
    })


def create_performance_comparison_chart(
    results: dict,
    output_path: Path,
    algorithms: list[str] | None = None
):
    """
    Create bar chart comparing performance across implementations.

    Args:
        results: Benchmark results dict
        output_path: Path to save the chart
        algorithms: Optional list of algorithms to include
    """
    data = results["results"]

    # Filter algorithms if specified
    if algorithms:
        data = [r for r in data if r["algorithm"] in algorithms]

    # Get unique values
    impls = sorted(set(r["implementation"] for r in data))
    algos = sorted(set(r["algorithm"] for r in data))
    lengths = ["short", "medium", "long"]

    # Create figure with subplots for each algorithm
    fig, axes = plt.subplots(len(algos), 1, figsize=(14, 5 * len(algos)))
    if len(algos) == 1:
        axes = [axes]

    colors = sns.color_palette("husl", len(impls))

    for ax, algo in zip(axes, algos):
        algo_data = [r for r in data if r["algorithm"] == algo]

        x = np.arange(len(lengths))
        width = 0.8 / len(impls)

        for i, impl in enumerate(impls):
            impl_data = [r for r in algo_data if r["implementation"] == impl]
            times = []
            for length in lengths:
                matches = [r for r in impl_data if r["text_length"] == length]
                times.append(matches[0]["mean_time_ms"] if matches else 0)

            offset = (i - len(impls) / 2 + 0.5) * width
            bars = ax.bar(x + offset, times, width, label=impl, color=colors[i])

            # Add value labels on bars
            for bar, time in zip(bars, times):
                if time > 0:
                    height = bar.get_height()
                    ax.annotate(f'{time:.2f}',
                               xy=(bar.get_x() + bar.get_width() / 2, height),
                               xytext=(0, 3),
                               textcoords="offset points",
                               ha='center', va='bottom',
                               fontsize=8, rotation=45)

        ax.set_ylabel('Time (ms)')
        ax.set_title(f'{algo.replace("_", " ").title()} Performance')
        ax.set_xticks(x)
        length_chars = {'short': 100, 'medium': 1000, 'long': 10000}
        ax.set_xticklabels([f"{l.capitalize()}\n(~{length_chars[l]} chars)" for l in lengths])
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax.set_yscale('log')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def create_speedup_chart(
    results: dict,
    output_path: Path,
    baseline: str = "Pure Python"
):
    """
    Create chart showing speedup ratios relative to baseline.
    """
    data = results["results"]

    # Get unique values
    impls = sorted(set(r["implementation"] for r in data))
    impls = [i for i in impls if i != baseline]  # Exclude baseline

    algos = sorted(set(r["algorithm"] for r in data))
    lengths = ["short", "medium", "long"]

    # Calculate speedups
    speedups = {}
    for algo in algos:
        speedups[algo] = {}
        for length in lengths:
            baseline_data = [r for r in data
                           if r["algorithm"] == algo
                           and r["text_length"] == length
                           and r["implementation"] == baseline]

            if not baseline_data:
                continue

            baseline_time = baseline_data[0]["mean_time_ms"]

            for impl in impls:
                impl_data = [r for r in data
                            if r["algorithm"] == algo
                            and r["text_length"] == length
                            and r["implementation"] == impl]

                if impl_data and impl_data[0]["mean_time_ms"] > 0:
                    speedup = baseline_time / impl_data[0]["mean_time_ms"]
                    key = f"{algo}_{length}"
                    if impl not in speedups[algo]:
                        speedups[algo][impl] = {}
                    speedups[algo][impl][length] = speedup

    # Create heatmap-style visualization
    fig, axes = plt.subplots(1, len(algos), figsize=(5 * len(algos), 6))
    if len(algos) == 1:
        axes = [axes]

    for ax, algo in zip(axes, algos):
        if algo not in speedups or not speedups[algo]:
            continue

        matrix = []
        impl_names = []
        for impl in impls:
            if impl in speedups[algo]:
                row = [speedups[algo][impl].get(l, 0) for l in lengths]
                matrix.append(row)
                impl_names.append(impl)

        if not matrix:
            continue

        matrix = np.array(matrix)

        im = ax.imshow(matrix, cmap='RdYlGn', aspect='auto',
                      vmin=0, vmax=max(10, np.max(matrix)))

        ax.set_xticks(range(len(lengths)))
        ax.set_xticklabels([l.capitalize() for l in lengths])
        ax.set_yticks(range(len(impl_names)))
        ax.set_yticklabels(impl_names)

        # Add text annotations
        for i in range(len(impl_names)):
            for j in range(len(lengths)):
                value = matrix[i, j]
                color = 'white' if value > np.max(matrix) / 2 else 'black'
                ax.text(j, i, f'{value:.1f}x', ha='center', va='center',
                       color=color, fontsize=10, fontweight='bold')

        ax.set_title(f'{algo.replace("_", " ").title()}\nSpeedup vs {baseline}')

        # Add colorbar
        plt.colorbar(im, ax=ax, label='Speedup factor')

    plt.suptitle(f'Speedup Ratios (relative to {baseline})', fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def create_text_length_scaling_chart(
    results: dict,
    output_path: Path
):
    """
    Create line chart showing how performance scales with text length.
    """
    data = results["results"]

    impls = sorted(set(r["implementation"] for r in data))
    algos = sorted(set(r["algorithm"] for r in data))

    # Map length names to numeric values for plotting
    length_values = {"short": 100, "medium": 1000, "long": 10000}
    lengths = ["short", "medium", "long"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    axes = axes.flatten()

    colors = sns.color_palette("husl", len(impls))
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']

    for idx, algo in enumerate(algos[:4]):  # Max 4 algorithms
        ax = axes[idx]
        algo_data = [r for r in data if r["algorithm"] == algo]

        for i, impl in enumerate(impls):
            impl_data = [r for r in algo_data if r["implementation"] == impl]

            x_vals = []
            y_vals = []
            for length in lengths:
                matches = [r for r in impl_data if r["text_length"] == length]
                if matches:
                    x_vals.append(length_values[length])
                    y_vals.append(matches[0]["mean_time_ms"])

            if x_vals:
                ax.plot(x_vals, y_vals,
                       marker=markers[i % len(markers)],
                       label=impl,
                       color=colors[i],
                       linewidth=2,
                       markersize=8)

        ax.set_xlabel('Text Length (characters)')
        ax.set_ylabel('Time (ms)')
        ax.set_title(f'{algo.replace("_", " ").title()} - Scaling with Text Length')
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.legend(loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)

    # Hide unused subplots
    for idx in range(len(algos), 4):
        axes[idx].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def create_summary_table_chart(
    results: dict,
    output_path: Path
):
    """
    Create a summary table as an image.
    """
    data = results["results"]

    impls = sorted(set(r["implementation"] for r in data))
    algos = sorted(set(r["algorithm"] for r in data))

    fig, ax = plt.subplots(figsize=(16, 10))
    ax.axis('off')

    # Prepare table data
    col_labels = ['Implementation'] + [f"{a}\n(short/med/long ms)" for a in algos]
    table_data = []

    for impl in impls:
        row = [impl]
        for algo in algos:
            times = []
            for length in ["short", "medium", "long"]:
                matches = [r for r in data
                          if r["implementation"] == impl
                          and r["algorithm"] == algo
                          and r["text_length"] == length]
                if matches:
                    times.append(f"{matches[0]['mean_time_ms']:.2f}")
                else:
                    times.append("-")
            row.append(" / ".join(times))
        table_data.append(row)

    table = ax.table(
        cellText=table_data,
        colLabels=col_labels,
        loc='center',
        cellLoc='center'
    )

    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.8)

    # Style the table
    for i in range(len(col_labels)):
        table[(0, i)].set_facecolor('#4472C4')
        table[(0, i)].set_text_props(color='white', fontweight='bold')

    for i in range(1, len(table_data) + 1):
        for j in range(len(col_labels)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#D9E2F3')

    plt.title('Performance Summary (Time in milliseconds)', fontsize=14, pad=20)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def generate_all_charts(
    results_path: Path,
    output_dir: Path
):
    """Generate all charts from benchmark results."""
    setup_style()

    results = load_results(results_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating charts...")

    create_performance_comparison_chart(
        results,
        output_dir / "performance_comparison.png"
    )

    create_speedup_chart(
        results,
        output_dir / "speedup_ratio.png"
    )

    create_text_length_scaling_chart(
        results,
        output_dir / "text_length_scaling.png"
    )

    create_summary_table_chart(
        results,
        output_dir / "summary_table.png"
    )

    print(f"\nAll charts saved to {output_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate benchmark charts")
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=Path(__file__).parent.parent / "results" / "benchmark_results.json",
        help="Path to benchmark results JSON"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path(__file__).parent.parent / "results" / "charts",
        help="Output directory for charts"
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Results file not found: {args.input}")
        print("Run benchmarks first: python benchmarks/run_benchmarks.py")
        exit(1)

    generate_all_charts(args.input, args.output)
