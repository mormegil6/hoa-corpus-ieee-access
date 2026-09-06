#!/usr/bin/env python3
"""
Shared utilities for microphone comparison analysis.

Common functions and configuration for figure generation.

Author: Bartłomiej Mróz
Date: 2026-01-26
"""

import numpy as np
import soundfile as sf
import yaml
import csv
import os
from pathlib import Path
from scipy import signal
from scipy.fft import fft, fftfreq
import warnings
warnings.filterwarnings('ignore')

# Configuration
SCRIPT_DIR = Path(__file__).parent.parent  # Go up from pyscripts to main dir
DATA_DIR = SCRIPT_DIR / "data"
METADATA_DIR = DATA_DIR / "metadata"
ACOUSTICS_DIR = DATA_DIR / "aula_acoustics"
OUTPUT_DIR = SCRIPT_DIR / "plots"
OUTPUT_DIR.mkdir(exist_ok=True)

# Audio location: HOA_CORPUS_DIR is the root of the deposit (the directory holding
# sessions/; download from doi.org/10.34808/w8bx-2094). Only the scripts that open
# audio need it; both names are None when it is unset.
CORPUS_ROOT = Path(os.environ["HOA_CORPUS_DIR"]) if os.environ.get("HOA_CORPUS_DIR") else None
COMPARISON_SESSION = "2024-08-15_aula-pg_solo-piano-mic-comparison"   # session with all microphone types
MIC_COMPARISON_SESSION = (CORPUS_ROOT / "sessions" / COMPARISON_SESSION / "audio"
                          if CORPUS_ROOT else None)

# Microphone files for Franck piece (same performance, different mics)
MIC_FILES = {
    "ZM-1 (3OA)": "3OA_ZM1_CFranck-PreludeChoralFugue.wav",
    "Spcmic (3OA)": "3OA_Spcmic_CFranck-PreludeChoralFugue.wav",
    "Spcmic (5OA)": "5OA_Spcmic_CFranck-PreludeChoralFugue.wav",
    "Saramonic (1OA)": "1OA_SRVRMIC_CFranck-PreludeChoralFugue.wav",
}

# Colors for each microphone
MIC_COLORS = {
    "ZM-1 (3OA)": "#1f77b4",      # Blue
    "Spcmic (3OA)": "#ff7f0e",    # Orange
    "Spcmic (5OA)": "#2ca02c",    # Green
    "Saramonic (1OA)": "#d62728", # Red
}


def load_metadata_files():
    """Load all metadata YAML files."""
    metadata = {}
    for yaml_file in METADATA_DIR.glob("*.yaml"):
        with open(yaml_file, 'r') as f:
            try:
                data = yaml.safe_load(f)
                metadata[yaml_file.stem] = data
            except Exception as e:
                print(f"Error loading {yaml_file.name}: {e}")
    return metadata


def load_lufs_from_csv():
    """Load LUFS data from parsed render_stats CSV file."""
    csv_path = DATA_DIR / "render_stats_all.csv"
    if not csv_path.exists():
        print(f"  Warning: {csv_path} not found. Run parse_render_stats.py first.")
        return []

    lufs_data = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['lufs_i']:
                try:
                    lufs_data.append({
                        'session': row['session'],
                        'filename': row['filename'],
                        'lufs_i': float(row['lufs_i']),
                        'true_peak_db': float(row['true_peak_db']) if row['true_peak_db'] else None,
                        'lra': float(row['lra']) if row['lra'] else None,
                    })
                except (ValueError, KeyError):
                    pass
    return lufs_data


def extract_lufs_from_metadata(metadata):
    """Extract LUFS values from all metadata files (fallback if CSV not available)."""
    lufs_data = []

    for session_name, data in metadata.items():
        if 'rendered_files' not in data:
            continue

        for rendered in data.get('rendered_files', []):
            if isinstance(rendered, dict) and 'lufs_i' in rendered:
                lufs_data.append({
                    'session': session_name,
                    'filename': rendered.get('filename', 'unknown'),
                    'lufs_i': rendered['lufs_i'],
                    'channels': rendered.get('channels', 0),
                    'duration': rendered.get('duration_minutes', 0),
                })

    return lufs_data


def compute_spectral_average(audio_path, excerpt_seconds=None, smoothing_octave=12):
    """
    Compute smoothed frequency response from audio file.

    If excerpt_seconds is None, uses entire file.
    Returns frequencies and magnitude in dB.
    """
    data, sr = sf.read(audio_path)

    # Extract W channel (omnidirectional, channel 0 in ACN)
    if data.ndim > 1:
        w_channel = data[:, 0]
    else:
        w_channel = data

    # Use excerpt or full duration
    if excerpt_seconds:
        samples = int(excerpt_seconds * sr)
        # Take from middle of the piece for more representative content
        start = (len(w_channel) - samples) // 2
        w_channel = w_channel[start:start + samples]

    # Compute FFT with windowing
    n = len(w_channel)
    window = signal.windows.hann(n)
    fft_result = fft(w_channel * window)
    freqs = fftfreq(n, 1/sr)[:n//2]
    magnitude = np.abs(fft_result[:n//2])

    # Convert to dB
    magnitude_db = 20 * np.log10(magnitude + 1e-10)

    # Apply 1/N octave smoothing using log-spaced moving average
    if smoothing_octave > 0:
        # Convert to log scale for smoothing
        log_freqs = np.log2(freqs[1:] + 1)  # Skip DC
        log_spacing = np.mean(np.diff(log_freqs))
        window_size = int(1 / (smoothing_octave * log_spacing))
        if window_size > 1:
            from scipy.ndimage import uniform_filter1d
            magnitude_db[1:] = uniform_filter1d(magnitude_db[1:], window_size)

    return freqs, magnitude_db


def compute_spatial_energy_distribution(audio_path):
    """
    Compute energy distribution across ambisonics orders.

    Returns energy ratios for each order relative to W channel.
    """
    data, sr = sf.read(audio_path)

    if data.ndim == 1:
        return {'0th': 1.0}

    n_channels = data.shape[1]

    # Determine ambisonics order from channel count
    if n_channels >= 36:
        order = 5
    elif n_channels >= 16:
        order = 3
    elif n_channels >= 4:
        order = 1
    else:
        return {'0th': 1.0}

    # Channel ranges for each order (ACN ordering)
    order_ranges = {
        0: (0, 1),
        1: (1, 4),
        2: (4, 9),
        3: (9, 16),
        4: (16, 25),
        5: (25, 36),
    }

    # Compute total energy per order
    energies = {}
    for ord_num in range(order + 1):
        start, end = order_ranges[ord_num]
        if end <= n_channels:
            order_data = data[:, start:end]
            energies[f"{ord_num}th"] = np.sum(order_data ** 2)

    # Normalize to W channel energy
    w_energy = energies.get('0th', 1.0)
    for key in energies:
        energies[key] = 10 * np.log10(energies[key] / w_energy + 1e-10)

    return energies
