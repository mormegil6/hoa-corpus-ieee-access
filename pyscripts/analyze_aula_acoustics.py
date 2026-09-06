#!/usr/bin/env python3
"""
Aula Politechniki Gdańskiej - Acoustic Analysis Script

Analyzes 3rd-order Ambisonic Room Impulse Responses (RIRs) recorded at 5 positions
in the Aula of Gdańsk University of Technology Main Building.

Measurement setup (from MSc thesis by Król & Jankowski):
- Microphone: Zylia ZM-1 (3OA, 19 capsules)
- Speaker: B&K TYPE 4292 (omnidirectional, ISO 3382 compliant)
- Excitation: Sine-sweep
- Processing: Aurora plugins (Audacity) for deconvolution
- Format: 48 kHz, B-format ACN/SN3D (16 channels)

Author: Bartłomiej Mróz
Date: 2026-01-24
"""

import numpy as np
import soundfile as sf
from scipy import signal
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import warnings
warnings.filterwarnings('ignore')

# Configuration
SCRIPT_DIR = Path(__file__).parent.parent  # Go up from pyscripts to main dir
DATA_DIR = SCRIPT_DIR / "data" / "aula_acoustics"
OUTPUT_DIR = SCRIPT_DIR / "plots"
OUTPUT_DIR.mkdir(exist_ok=True)

# Measurement positions
POSITIONS = {
    "6.1.przod_prawo": "Front Right (przód prawo)",
    "6.2.srodek_prawo": "Center Right (środek prawo)",
    "6.3.srodek_srodka": "Center Center (środek środka)",
    "6.4.pod_balkonem": "Under Balcony (pod balkonem)",
    "6.5.balkon": "Balcony (balkon)"
}

# Octave band center frequencies for RT60 analysis
OCTAVE_BANDS = [125, 250, 500, 1000, 2000, 4000]


def load_bformat_ir(position_dir: Path) -> tuple:
    """Load B-format impulse response from a position directory."""
    bformat_files = list(position_dir.glob("*Bformat*.wav"))
    if not bformat_files:
        raise FileNotFoundError(f"No B-format file found in {position_dir}")

    data, sr = sf.read(bformat_files[0])
    return data, sr, bformat_files[0].name


def compute_edc(ir: np.ndarray) -> np.ndarray:
    """
    Compute Energy Decay Curve (EDC) using Schroeder backward integration.
    EDC(t) = integral from t to infinity of h²(τ) dτ
    """
    energy = ir ** 2
    # Backward integration (cumulative sum from end)
    edc = np.cumsum(energy[::-1])[::-1]
    # Normalize to 0 dB at start
    edc = edc / edc[0]
    # Convert to dB
    edc_db = 10 * np.log10(edc + 1e-10)
    return edc_db


def compute_rt60(ir: np.ndarray, sr: int, method: str = "T30") -> float:
    """
    Compute RT60 (reverberation time) from impulse response.

    Methods:
    - T20: Extrapolate from -5 dB to -25 dB decay
    - T30: Extrapolate from -5 dB to -35 dB decay (more reliable)
    """
    edc_db = compute_edc(ir)

    # Find time indices for decay range
    if method == "T20":
        start_db, end_db = -5, -25
    elif method == "T30":
        start_db, end_db = -5, -35
    else:
        raise ValueError(f"Unknown method: {method}")

    # Find indices where EDC crosses thresholds
    try:
        start_idx = np.where(edc_db <= start_db)[0][0]
        end_idx = np.where(edc_db <= end_db)[0][0]
    except IndexError:
        return np.nan  # EDC doesn't decay enough

    if end_idx <= start_idx:
        return np.nan

    # Linear regression on the decay portion
    time = np.arange(start_idx, end_idx) / sr
    edc_segment = edc_db[start_idx:end_idx]

    # Fit line: edc = slope * time + intercept
    coeffs = np.polyfit(time, edc_segment, 1)
    slope = coeffs[0]

    if slope >= 0:
        return np.nan  # Not decaying

    # RT60 = time for 60dB decay
    rt60 = -60.0 / slope
    return rt60


def compute_rt60_octave_bands(ir: np.ndarray, sr: int, method: str = "T30") -> dict:
    """Compute RT60 for each octave band."""
    rt60_bands = {}

    for fc in OCTAVE_BANDS:
        # Octave band filter (fc/√2 to fc*√2)
        f_low = fc / np.sqrt(2)
        f_high = fc * np.sqrt(2)

        # Butterworth bandpass filter
        nyq = sr / 2
        low = f_low / nyq
        high = min(f_high / nyq, 0.99)  # Ensure below Nyquist

        try:
            b, a = signal.butter(4, [low, high], btype='band')
            ir_filtered = signal.filtfilt(b, a, ir)
            rt60_bands[fc] = compute_rt60(ir_filtered, sr, method)
        except Exception:
            rt60_bands[fc] = np.nan

    return rt60_bands


def compute_clarity(ir: np.ndarray, sr: int, early_ms: int = 80) -> float:
    """
    Compute Clarity (C80 or C50) - ratio of early to late energy.
    C = 10 * log10(E_early / E_late)

    C80 (early_ms=80): Used for music
    C50 (early_ms=50): Used for speech
    """
    early_samples = int(early_ms * sr / 1000)

    early_energy = np.sum(ir[:early_samples] ** 2)
    late_energy = np.sum(ir[early_samples:] ** 2)

    if late_energy < 1e-10:
        return np.inf

    clarity = 10 * np.log10(early_energy / late_energy)
    return clarity


def compute_definition(ir: np.ndarray, sr: int, early_ms: int = 50) -> float:
    """
    Compute Definition (D50) - fraction of early energy.
    D = E_early / E_total
    """
    early_samples = int(early_ms * sr / 1000)

    early_energy = np.sum(ir[:early_samples] ** 2)
    total_energy = np.sum(ir ** 2)

    if total_energy < 1e-10:
        return 0

    definition = early_energy / total_energy
    return definition


def compute_centre_time(ir: np.ndarray, sr: int) -> float:
    """
    Compute Centre Time (Ts) - first moment of energy.
    Ts = integral(t * h²(t) dt) / integral(h²(t) dt)
    """
    energy = ir ** 2
    time = np.arange(len(ir)) / sr

    total_energy = np.sum(energy)
    if total_energy < 1e-10:
        return 0

    ts = np.sum(time * energy) / total_energy
    return ts * 1000  # Return in milliseconds


def compute_edt(ir: np.ndarray, sr: int) -> float:
    """
    Compute Early Decay Time (EDT) - RT based on first 10dB decay.
    """
    edc_db = compute_edc(ir)

    # Find 0 to -10 dB decay
    try:
        start_idx = 0
        end_idx = np.where(edc_db <= -10)[0][0]
    except IndexError:
        return np.nan

    if end_idx <= start_idx:
        return np.nan

    time = np.arange(start_idx, end_idx) / sr
    edc_segment = edc_db[start_idx:end_idx]

    coeffs = np.polyfit(time, edc_segment, 1)
    slope = coeffs[0]

    if slope >= 0:
        return np.nan

    # Extrapolate to 60dB decay
    edt = -60.0 / slope
    return edt


def extract_w_channel(bformat_data: np.ndarray) -> np.ndarray:
    """Extract omnidirectional (W) channel from B-format data."""
    # ACN ordering: W is channel 0
    if bformat_data.ndim == 1:
        return bformat_data
    return bformat_data[:, 0]


def find_ir_onset(ir: np.ndarray, threshold_db: float = -20) -> int:
    """
    Find the onset of the impulse response (direct sound arrival).
    Uses threshold crossing method relative to peak.
    """
    # Find peak
    peak_idx = np.argmax(np.abs(ir))
    peak_val = np.abs(ir[peak_idx])

    # Threshold in linear scale
    threshold = peak_val * 10 ** (threshold_db / 20)

    # Search backward from peak to find onset
    for i in range(peak_idx, 0, -1):
        if np.abs(ir[i]) < threshold:
            return i
    return 0


def trim_ir_to_onset(ir: np.ndarray, pre_samples: int = 100) -> np.ndarray:
    """
    Trim impulse response to start just before the direct sound.
    Keeps a small pre-onset portion for reference.
    """
    onset = find_ir_onset(ir)
    start = max(0, onset - pre_samples)
    return ir[start:]


def analyze_position(position_dir: Path, position_name: str) -> dict:
    """Analyze acoustics for a single measurement position."""
    print(f"\nAnalyzing: {position_name}")

    try:
        data, sr, filename = load_bformat_ir(position_dir)
    except FileNotFoundError as e:
        print(f"  Error: {e}")
        return None

    print(f"  File: {filename}")
    print(f"  Sample rate: {sr} Hz")
    print(f"  Duration: {len(data)/sr:.3f} s")
    print(f"  Channels: {data.shape[1] if data.ndim > 1 else 1}")

    # Extract W channel (omnidirectional) for standard acoustic parameters
    w_channel = extract_w_channel(data)

    # Find and trim to IR onset (remove pre-arrival silence)
    onset_idx = find_ir_onset(w_channel)
    onset_time_ms = onset_idx / sr * 1000
    print(f"  Direct sound onset: {onset_time_ms:.1f} ms")

    # Trim IR to start at onset (keep 2ms pre-onset)
    w_trimmed = trim_ir_to_onset(w_channel, pre_samples=int(0.002 * sr))

    # Normalize
    w_trimmed = w_trimmed / np.max(np.abs(w_trimmed))

    results = {
        "position": position_name,
        "filename": filename,
        "sample_rate": sr,
        "duration_s": len(data) / sr,
        "channels": data.shape[1] if data.ndim > 1 else 1,
        "onset_ms": onset_time_ms,
    }

    # Compute acoustic parameters on trimmed IR
    results["T30"] = compute_rt60(w_trimmed, sr, "T30")
    results["T20"] = compute_rt60(w_trimmed, sr, "T20")
    results["EDT"] = compute_edt(w_trimmed, sr)
    results["C80"] = compute_clarity(w_trimmed, sr, 80)
    results["C50"] = compute_clarity(w_trimmed, sr, 50)
    results["D50"] = compute_definition(w_trimmed, sr, 50)
    results["Ts"] = compute_centre_time(w_trimmed, sr)

    # Octave band RT60
    results["T30_bands"] = compute_rt60_octave_bands(w_trimmed, sr, "T30")

    # Print results
    print(f"  T30: {results['T30']:.2f} s" if not np.isnan(results['T30']) else "  T30: N/A")
    print(f"  T20: {results['T20']:.2f} s" if not np.isnan(results['T20']) else "  T20: N/A")
    print(f"  EDT: {results['EDT']:.2f} s" if not np.isnan(results['EDT']) else "  EDT: N/A")
    print(f"  C80: {results['C80']:.1f} dB")
    print(f"  C50: {results['C50']:.1f} dB")
    print(f"  D50: {results['D50']:.2%}")
    print(f"  Ts: {results['Ts']:.0f} ms")

    # Store raw data for plotting (use trimmed version)
    results["w_channel"] = w_trimmed
    results["edc_db"] = compute_edc(w_trimmed)

    return results


def plot_all_results(all_results: list):
    """Generate comprehensive plots for all positions."""

    # Filter out None results
    results = [r for r in all_results if r is not None]
    if not results:
        print("No valid results to plot")
        return

    sr = results[0]["sample_rate"]

    # === Figure 1: Energy Decay Curves ===
    fig1, ax1 = plt.subplots(figsize=(12, 6))

    for r in results:
        time = np.arange(len(r["edc_db"])) / sr
        ax1.plot(time, r["edc_db"], label=r["position"], linewidth=1.5)

    ax1.set_xlabel("Time (s)", fontsize=12)
    ax1.set_ylabel("Energy Decay (dB)", fontsize=12)
    ax1.set_title("Energy Decay Curves (EDC) - Aula PG, All Positions", fontsize=14)
    ax1.set_xlim(0, 3)
    ax1.set_ylim(-80, 5)
    ax1.axhline(-5, color='gray', linestyle='--', alpha=0.5, label='T30 start (-5 dB)')
    ax1.axhline(-35, color='gray', linestyle=':', alpha=0.5, label='T30 end (-35 dB)')
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3)

    fig1.tight_layout()
    fig1.savefig(OUTPUT_DIR / "01_energy_decay_curves.png", dpi=150)
    print(f"\nSaved: {OUTPUT_DIR / '01_energy_decay_curves.png'}")

    # === Figure 2: Impulse Responses ===
    fig2, axes2 = plt.subplots(len(results), 1, figsize=(14, 3*len(results)), sharex=True)
    if len(results) == 1:
        axes2 = [axes2]

    for ax, r in zip(axes2, results):
        time = np.arange(len(r["w_channel"])) / sr * 1000  # ms
        ax.plot(time, r["w_channel"], linewidth=0.5, color='steelblue')
        ax.set_ylabel(r["position"].split('(')[1].rstrip(')'), fontsize=10)
        ax.set_xlim(0, 500)
        ax.grid(True, alpha=0.3)

    axes2[-1].set_xlabel("Time (ms)", fontsize=12)
    fig2.suptitle("Impulse Responses (W channel) - Aula PG", fontsize=14, y=1.02)

    fig2.tight_layout()
    fig2.savefig(OUTPUT_DIR / "02_impulse_responses.png", dpi=150)
    print(f"Saved: {OUTPUT_DIR / '02_impulse_responses.png'}")

    # === Figure 3: RT60 Comparison ===
    fig3, ax3 = plt.subplots(figsize=(10, 6))

    positions = [r["position"].split('(')[1].rstrip(')') for r in results]
    t30_values = [r["T30"] for r in results]
    t20_values = [r["T20"] for r in results]
    edt_values = [r["EDT"] for r in results]

    x = np.arange(len(positions))
    width = 0.25

    bars1 = ax3.bar(x - width, t30_values, width, label='T30', color='steelblue')
    bars2 = ax3.bar(x, t20_values, width, label='T20', color='coral')
    bars3 = ax3.bar(x + width, edt_values, width, label='EDT', color='seagreen')

    ax3.set_ylabel('Reverberation Time (s)', fontsize=12)
    ax3.set_xlabel('Measurement Position', fontsize=12)
    ax3.set_title('Reverberation Time Comparison - Aula PG', fontsize=14)
    ax3.set_xticks(x)
    ax3.set_xticklabels(positions, rotation=15, ha='right')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')

    # Add value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if not np.isnan(height):
                ax3.annotate(f'{height:.2f}',
                           xy=(bar.get_x() + bar.get_width()/2, height),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom', fontsize=8)

    fig3.tight_layout()
    fig3.savefig(OUTPUT_DIR / "03_reverberation_times.png", dpi=150)
    print(f"Saved: {OUTPUT_DIR / '03_reverberation_times.png'}")

    # === Figure 4: Octave Band RT60 ===
    fig4, ax4 = plt.subplots(figsize=(12, 6))

    for r in results:
        freqs = list(r["T30_bands"].keys())
        rt_values = [r["T30_bands"][f] for f in freqs]
        ax4.plot(freqs, rt_values, 'o-', label=r["position"].split('(')[1].rstrip(')'),
                linewidth=2, markersize=8)

    ax4.set_xscale('log')
    ax4.set_xlabel('Frequency (Hz)', fontsize=12)
    ax4.set_ylabel('T30 (s)', fontsize=12)
    ax4.set_title('Octave Band Reverberation Time (T30) - Aula PG', fontsize=14)
    ax4.set_xticks(OCTAVE_BANDS)
    ax4.set_xticklabels([str(f) for f in OCTAVE_BANDS])
    ax4.legend(loc='upper right')
    ax4.grid(True, alpha=0.3)

    fig4.tight_layout()
    fig4.savefig(OUTPUT_DIR / "04_octave_band_rt60.png", dpi=150)
    print(f"Saved: {OUTPUT_DIR / '04_octave_band_rt60.png'}")

    # === Figure 5: Clarity and Definition ===
    fig5, (ax5a, ax5b) = plt.subplots(1, 2, figsize=(14, 5))

    c80_values = [r["C80"] for r in results]
    c50_values = [r["C50"] for r in results]
    d50_values = [r["D50"] * 100 for r in results]  # Convert to percentage
    ts_values = [r["Ts"] for r in results]

    # Clarity subplot
    x = np.arange(len(positions))
    width = 0.35
    ax5a.bar(x - width/2, c80_values, width, label='C80 (music)', color='steelblue')
    ax5a.bar(x + width/2, c50_values, width, label='C50 (speech)', color='coral')
    ax5a.set_ylabel('Clarity (dB)', fontsize=12)
    ax5a.set_xlabel('Position', fontsize=12)
    ax5a.set_title('Clarity Index', fontsize=14)
    ax5a.set_xticks(x)
    ax5a.set_xticklabels(positions, rotation=15, ha='right')
    ax5a.legend()
    ax5a.grid(True, alpha=0.3, axis='y')
    ax5a.axhline(0, color='black', linestyle='-', linewidth=0.5)

    # D50 and Ts subplot
    ax5b_twin = ax5b.twinx()
    ax5b.bar(x - width/2, d50_values, width, label='D50 (%)', color='seagreen')
    ax5b_twin.plot(x + width/2, ts_values, 'D-', color='purple',
                            label='Ts (ms)', markersize=10, linewidth=2)

    ax5b.set_ylabel('Definition D50 (%)', fontsize=12, color='seagreen')
    ax5b_twin.set_ylabel('Centre Time Ts (ms)', fontsize=12, color='purple')
    ax5b.set_xlabel('Position', fontsize=12)
    ax5b.set_title('Definition & Centre Time', fontsize=14)
    ax5b.set_xticks(x)
    ax5b.set_xticklabels(positions, rotation=15, ha='right')
    ax5b.grid(True, alpha=0.3, axis='y')

    # Combined legend
    lines1, labels1 = ax5b.get_legend_handles_labels()
    lines2, labels2 = ax5b_twin.get_legend_handles_labels()
    ax5b.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

    fig5.tight_layout()
    fig5.savefig(OUTPUT_DIR / "05_clarity_definition.png", dpi=150)
    print(f"Saved: {OUTPUT_DIR / '05_clarity_definition.png'}")

    plt.close('all')


def generate_report(all_results: list):
    """Generate a text report summarizing the analysis."""
    results = [r for r in all_results if r is not None]
    if not results:
        return

    report_path = OUTPUT_DIR / "aula_acoustics_report.txt"

    with open(report_path, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("ACOUSTIC ANALYSIS REPORT\n")
        f.write("Aula Politechniki Gdańskiej (Main Building Concert Hall)\n")
        f.write("=" * 70 + "\n\n")

        f.write("MEASUREMENT SETUP:\n")
        f.write("-" * 40 + "\n")
        f.write("Microphone:    Zylia ZM-1 (3rd Order Ambisonics)\n")
        f.write("Speaker:       B&K TYPE 4292 (Omnidirectional)\n")
        f.write("Excitation:    Logarithmic Sine Sweep\n")
        f.write("Processing:    Aurora plugins (Audacity)\n")
        f.write(f"Sample Rate:   {results[0]['sample_rate']} Hz\n")
        f.write("Format:        B-format ACN/SN3D (16 channels)\n\n")

        f.write("MEASUREMENT POSITIONS:\n")
        f.write("-" * 40 + "\n")
        for pos_id, pos_name in POSITIONS.items():
            f.write(f"  {pos_id}: {pos_name}\n")
        f.write("\n")

        f.write("RESULTS SUMMARY:\n")
        f.write("-" * 40 + "\n")
        f.write(f"{'Position':<25} {'T30(s)':<8} {'T20(s)':<8} {'EDT(s)':<8} {'C80(dB)':<8} {'D50(%)':<8} {'Ts(ms)':<8}\n")
        f.write("-" * 70 + "\n")

        for r in results:
            pos = r["position"].split('(')[1].rstrip(')')
            t30 = f"{r['T30']:.2f}" if not np.isnan(r['T30']) else "N/A"
            t20 = f"{r['T20']:.2f}" if not np.isnan(r['T20']) else "N/A"
            edt = f"{r['EDT']:.2f}" if not np.isnan(r['EDT']) else "N/A"
            c80 = f"{r['C80']:.1f}"
            d50 = f"{r['D50']*100:.1f}"
            ts = f"{r['Ts']:.0f}"
            f.write(f"{pos:<25} {t30:<8} {t20:<8} {edt:<8} {c80:<8} {d50:<8} {ts:<8}\n")

        f.write("\n")
        f.write("OCTAVE BAND T30 (seconds):\n")
        f.write("-" * 40 + "\n")
        f.write(f"{'Position':<25} " + " ".join([f"{fc:>6}" for fc in OCTAVE_BANDS]) + " Hz\n")
        f.write("-" * 70 + "\n")

        for r in results:
            pos = r["position"].split('(')[1].rstrip(')')
            values = [f"{r['T30_bands'][fc]:.2f}" if not np.isnan(r['T30_bands'][fc]) else "N/A"
                     for fc in OCTAVE_BANDS]
            f.write(f"{pos:<25} " + " ".join([f"{v:>6}" for v in values]) + "\n")

        # Statistics
        t30_values = [r['T30'] for r in results if not np.isnan(r['T30'])]
        if t30_values:
            f.write("\n")
            f.write("STATISTICS:\n")
            f.write("-" * 40 + "\n")
            f.write(f"Average T30:  {np.mean(t30_values):.2f} s\n")
            f.write(f"Std Dev T30:  {np.std(t30_values):.2f} s\n")
            f.write(f"Min T30:      {np.min(t30_values):.2f} s\n")
            f.write(f"Max T30:      {np.max(t30_values):.2f} s\n")

        f.write("\n")
        f.write("INTERPRETATION:\n")
        f.write("-" * 40 + "\n")
        avg_t30 = np.mean(t30_values) if t30_values else 0
        if avg_t30 > 2.0:
            f.write("The Aula has a long reverberation time (>2s), characteristic of\n")
            f.write("large concert halls. Good for orchestral/choral music, may require\n")
            f.write("speech reinforcement for lectures.\n")
        elif avg_t30 > 1.0:
            f.write("The Aula has moderate reverberation (1-2s), suitable for\n")
            f.write("multi-purpose use including both music and speech.\n")
        else:
            f.write("The Aula has relatively short reverberation (<1s), good for\n")
            f.write("speech intelligibility.\n")

        f.write("\n")
        f.write("=" * 70 + "\n")
        f.write("Report generated by analyze_aula_acoustics.py\n")
        f.write("Data source: MSc Thesis by Jakub Król & Błażej Jankowski (2023)\n")
        f.write("=" * 70 + "\n")

    print(f"\nSaved: {report_path}")


def main():
    """Main analysis function."""
    print("=" * 60)
    print("AULA POLITECHNIKI GDAŃSKIEJ - ACOUSTIC ANALYSIS")
    print("=" * 60)

    all_results = []

    for pos_id, pos_name in POSITIONS.items():
        pos_dir = DATA_DIR / pos_id
        if pos_dir.exists():
            result = analyze_position(pos_dir, pos_name)
            all_results.append(result)
        else:
            print(f"\nWarning: Directory not found: {pos_dir}")

    print("\n" + "=" * 60)
    print("GENERATING PLOTS...")
    print("=" * 60)

    plot_all_results(all_results)
    generate_report(all_results)

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print(f"Results saved to: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    main()
