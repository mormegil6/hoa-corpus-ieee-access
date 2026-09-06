#!/usr/bin/env python3
"""
Generate Spectral Comparison Figure (Figure 7 in paper)

Compares frequency response of the same passage captured by different microphones
from the 2024.08.15 microphone comparison session.

Usage:
    python plot_spectral_comparison.py [--full] [--excerpt]

Options:
    --full      Generate full piece analysis (pub_fig07_spectral_comparison.png)
    --excerpt   Generate 10-second excerpt analysis (fig_spectral_comparison_excerpt.png, not in paper)
    (no args)   Generate both

Author: Bartłomiej Mróz
Date: 2026-01-26
"""

import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt

# Import shared utilities
from analysis_utils import (
    MIC_FILES, MIC_COLORS, MIC_COMPARISON_SESSION, OUTPUT_DIR,
    compute_spectral_average
)


def plot_spectral_comparison(output_path, use_full_piece=False):
    """
    Figure 2: Spectral comparison across microphones.

    Compares frequency response of same passage captured by different mics.
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    excerpt_duration = None if use_full_piece else 10  # 10 second excerpt or full

    # Line styles to distinguish overlapping curves
    # Order: Saramonic (1OA), ZM-1 (3OA), Spcmic (3OA), Spcmic (5OA)
    # Plot in this order so higher-order mics are on top
    plot_order = ["Saramonic (1OA)", "ZM-1 (3OA)", "Spcmic (3OA)", "Spcmic (5OA)"]
    line_styles = {
        "Saramonic (1OA)": {'linewidth': 2.0, 'linestyle': '-', 'alpha': 0.9},
        "ZM-1 (3OA)": {'linewidth': 1.8, 'linestyle': '-', 'alpha': 0.85},
        "Spcmic (3OA)": {'linewidth': 2.2, 'linestyle': '-', 'alpha': 1.0},  # Solid, thicker for visibility
        "Spcmic (5OA)": {'linewidth': 1.1, 'linestyle': '-', 'alpha': 0.60},  # Thinner, more transparent so orange shows
    }

    for mic_name in plot_order:
        if mic_name not in MIC_FILES:
            continue
        filename = MIC_FILES[mic_name]
        audio_path = MIC_COMPARISON_SESSION / filename
        if not audio_path.exists():
            print(f"  Warning: {filename} not found")
            continue

        print(f"  Processing {mic_name}...")
        freqs, magnitude_db = compute_spectral_average(audio_path, excerpt_duration, smoothing_octave=6)

        # Normalize each to 0 dB at 1 kHz for comparison
        idx_1k = np.argmin(np.abs(freqs - 1000))
        ref_level = magnitude_db[idx_1k]
        magnitude_db = magnitude_db - ref_level

        # Plot only 20 Hz - 20 kHz
        mask = (freqs >= 20) & (freqs <= 20000)
        style = line_styles.get(mic_name, {'linewidth': 1.5, 'linestyle': '-', 'alpha': 0.9})
        ax.semilogx(freqs[mask], magnitude_db[mask],
                   label=mic_name, color=MIC_COLORS[mic_name],
                   linewidth=style['linewidth'], linestyle=style['linestyle'],
                   alpha=style['alpha'])

    ax.set_xlabel('Frequency (Hz)', fontsize=12)
    ax.set_ylabel('Relative Level (dB)', fontsize=12)
    # No title for publication (caption in paper)
    ax.set_xlim(20, 20000)
    ax.set_ylim(-30, 15)
    ax.grid(True, which='both', alpha=0.3)
    ax.legend(loc='upper right', fontsize=10)

    # Add octave band markers
    for freq in [63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]:
        ax.axvline(freq, color='gray', alpha=0.2, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate spectral comparison figure')
    parser.add_argument('--full', action='store_true', help='Generate full piece analysis')
    parser.add_argument('--excerpt', action='store_true', help='Generate excerpt analysis')
    args = parser.parse_args()
    if MIC_COMPARISON_SESSION is None:
        sys.exit("set HOA_CORPUS_DIR to the corpus audio (download from doi.org/10.34808/w8bx-2094)")

    # Default: generate both if no specific option
    do_both = not args.full and not args.excerpt

    print("="*60)
    print("SPECTRAL COMPARISON ANALYSIS")
    print("="*60)

    if args.excerpt or do_both:
        print("\nGenerating 10-second excerpt spectral comparison...")
        plot_spectral_comparison(OUTPUT_DIR / "fig_spectral_comparison_excerpt.png", use_full_piece=False)

    if args.full or do_both:
        print("\nGenerating full piece spectral comparison (this may take a while)...")
        plot_spectral_comparison(OUTPUT_DIR / "pub_fig07_spectral_comparison.png", use_full_piece=True)

    print("\n" + "="*60)
    print("DONE")
    print("="*60)


if __name__ == "__main__":
    main()
