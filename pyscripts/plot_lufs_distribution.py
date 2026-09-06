#!/usr/bin/env python3
"""
Per-file LUFS-I bar chart of every rendered file, flagging anomalies.

Not a manuscript figure (the corpus histogram of Fig. 6 is rendered by
render_ieee_figures.py); writes plots/lufs_per_file.png.

Usage:
    python plot_lufs_distribution.py

Author: Bartłomiej Mróz
Date: 2026-01-26
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt

# Import shared utilities
from analysis_utils import (
    OUTPUT_DIR, load_lufs_from_csv, load_metadata_files, extract_lufs_from_metadata
)


def plot_lufs_distribution(lufs_data, output_path):
    """
    Figure 3: LUFS distribution across all rendered files.

    Bar chart showing LUFS-I values, flagging anomalies.
    """
    if not lufs_data:
        print("  No LUFS data available")
        return

    # Sort by LUFS value
    sorted_data = sorted(lufs_data, key=lambda x: x['lufs_i'], reverse=True)

    # Prepare data for plotting
    labels = [f"{d['filename'][:30]}..." if len(d['filename']) > 30 else d['filename']
              for d in sorted_data]
    values = [d['lufs_i'] for d in sorted_data]

    # Color based on anomaly (< -35 LUFS is suspicious)
    colors = ['#d62728' if v < -35 else '#1f77b4' for v in values]

    fig, ax = plt.subplots(figsize=(14, max(8, len(labels) * 0.25)))

    y_pos = np.arange(len(labels))
    ax.barh(y_pos, values, color=colors, alpha=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel('LUFS-I (Integrated Loudness)', fontsize=12)
    ax.set_xlim(min(values) - 5, max(values) + 5)
    ax.axvline(-23, color='green', linestyle='--', alpha=0.7, label='EBU R128 target (-23 LUFS)')
    ax.axvline(-35, color='red', linestyle='--', alpha=0.5, label='Anomaly threshold')
    ax.legend(loc='lower right')
    ax.grid(True, axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path}")


def main():
    print("="*60)
    print("LUFS DISTRIBUTION ANALYSIS")
    print("="*60)

    # Load LUFS data - prefer CSV from parse_render_stats.py
    print("\nLoading LUFS data...")
    lufs_data = load_lufs_from_csv()
    if not lufs_data:
        print("  Falling back to metadata extraction...")
        metadata = load_metadata_files()
        lufs_data = extract_lufs_from_metadata(metadata)

    print(f"  Found {len(lufs_data)} LUFS values")

    # Generate figure
    print("\nGenerating LUFS distribution figure...")
    plot_lufs_distribution(lufs_data, OUTPUT_DIR / "lufs_per_file.png")

    # Print summary
    if lufs_data:
        values = [d['lufs_i'] for d in lufs_data]
        print(f"\n  Range: {min(values):.1f} to {max(values):.1f} LUFS")
        print(f"  Mean: {np.mean(values):.1f} LUFS")

        anomalies = [d for d in lufs_data if d['lufs_i'] < -35]
        if anomalies:
            print("\n  Anomalies (< -35 LUFS):")
            for a in anomalies:
                print(f"    - {a['filename']}: {a['lufs_i']:.1f} LUFS")

    print("\n" + "="*60)
    print("DONE")
    print("="*60)


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    main()
