#!/usr/bin/env python3
"""
Generate RT60 Octave Band Figure (Figure 3 in paper)

Bar chart showing RT60 by octave band from Aula measurements.

Usage:
    python plot_rt60.py

Author: Bartłomiej Mróz
Date: 2026-01-26
"""

import argparse
import csv
import numpy as np
import matplotlib.pyplot as plt

# Import shared utilities
from analysis_utils import OUTPUT_DIR


def plot_rt60_octave_bands(output_path):
    """
    Figure 3: RT60 by octave band from Aula measurements.

    Bar chart using measured data from metadata.
    """
    # RT60 data from Aula measurements (average of 5 positions)
    octave_bands = ['125 Hz', '250 Hz', '500 Hz', '1 kHz', '2 kHz', '4 kHz', '8 kHz']
    frequencies = [125, 250, 500, 1000, 2000, 4000, 8000]
    rt60_values = [2.28, 2.27, 2.04, 1.90, 1.74, 1.50, 1.06]  # From metadata

    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(octave_bands))
    colors = plt.cm.coolwarm(np.linspace(0.2, 0.8, len(octave_bands)))

    bars = ax.bar(x, rt60_values, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)

    # Add value labels on bars
    for bar, val in zip(bars, rt60_values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f'{val:.2f}', ha='center', va='bottom', fontsize=10)

    ax.set_xlabel('Octave Band Center Frequency', fontsize=12)
    ax.set_ylabel('Reverberation Time T30 (seconds)', fontsize=12)
    # No title for publication (caption in paper)
    ax.set_xticks(x)
    ax.set_xticklabels(octave_bands, fontsize=10)
    ax.set_ylim(0, 2.8)
    ax.grid(True, axis='y', alpha=0.3)

    # Add horizontal line for broadband average
    avg_rt60 = np.mean(rt60_values)
    ax.axhline(avg_rt60, color='red', linestyle='--', alpha=0.7,
               label=f'Broadband average: {avg_rt60:.2f} s')
    ax.legend(loc='upper right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path}")

    # Save CSV with the data
    csv_path = output_path.with_suffix('.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['frequency_hz', 'octave_band', 'rt60_T30_seconds'])
        for freq, band, rt60 in zip(frequencies, octave_bands, rt60_values):
            writer.writerow([freq, band, rt60])
    print(f"  Saved: {csv_path}")


def main():
    print("="*60)
    print("RT60 OCTAVE BAND ANALYSIS")
    print("="*60)

    print("\nGenerating RT60 octave band figure...")
    plot_rt60_octave_bands(OUTPUT_DIR / "pub_fig03_rt60_octave_bands.png")

    print("\n" + "="*60)
    print("DONE")
    print("="*60)


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    main()
