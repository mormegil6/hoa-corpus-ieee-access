#!/usr/bin/env python3
"""
Render publication figures sized for IEEE Access two-column format.

IEEE single-column width = 3.5 in. All font sizes are set for that printed
width at 300 DPI - no reliance on post-render scaling.

Output: figures/  (override with the IEEE_FIG_DIR environment variable)

Figures produced:
  pub_fig03  RT60 octave bands          (CSV)
  pub_fig04  Geographic map full + detail (CSV + contextily/geopandas, network for tiles)
  pub_fig05  Recording timeline          (CSV)
  pub_fig06  LUFS corpus histogram       (CSV)
  pub_fig07  Spectral comparison         (audio: set HOA_CORPUS_DIR, skipped otherwise)
  pub_fig08  LUFS mic comparison         (CSV)
  pub_fig09  Spatial energy per order    (CSV)
  pub_fig10  Directional distribution    (CSV)

pub_fig01 (photo collage) and pub_fig02 (pipeline diagram) are static files;
they are NOT regenerated here.

Usage:
    python render_ieee_figures.py               # all figures
    python render_ieee_figures.py 06 09 10      # selected figure numbers
"""

import argparse
import os
import sys
import csv
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).parent.parent          # corpus root
PLOTS_DIR    = SCRIPT_DIR / "plots"
DATA_DIR     = SCRIPT_DIR / "data"
IEEE_FIG_DIR = Path(os.environ.get("IEEE_FIG_DIR", SCRIPT_DIR / "figures"))
IEEE_FIG_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# IEEE sizing constants
# ---------------------------------------------------------------------------
COL_W   = 3.5    # single-column width in inches
MAP_W   = 1.75   # each map subfigure (2 side-by-side at 0.48 \columnwidth)

# Font hierarchy for single-column IEEE figures (points)
FS_LABEL  = 7.5   # axis labels
FS_TICK   = 6.5   # tick labels
FS_LEGEND = 6.5   # legend entries
FS_ANNOT  = 6.0   # bar / data annotations

DPI = 300


def _apply_ieee_style(ax, xlabel='', ylabel='', legend_loc='best',
                      legend_kw=None, grid_axis='y'):
    """Apply shared IEEE style to an axes object."""
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=FS_LABEL)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=FS_LABEL)
    ax.tick_params(axis='both', labelsize=FS_TICK)
    if grid_axis:
        ax.grid(True, axis=grid_axis, alpha=0.3, linewidth=0.5)
    if legend_kw is None:
        legend_kw = {}
    # Only draw legend if there are labelled artists
    handles, labels = ax.get_legend_handles_labels()
    if labels:
        default = dict(fontsize=FS_LEGEND, framealpha=0.9,
                       edgecolor='0.8', borderpad=0.4)
        default.update(legend_kw)
        ax.legend(handles, labels, loc=legend_loc, **default)


def _save(fig, name):
    out = IEEE_FIG_DIR / name
    fig.savefig(out, dpi=DPI, bbox_inches='tight')
    plt.close(fig)
    print(f"  {out}")


# ---------------------------------------------------------------------------
# Figure 3 - RT60 octave bands
# ---------------------------------------------------------------------------
def render_fig03():
    print("\n[fig03] RT60 octave bands")
    csv_path = PLOTS_DIR / "pub_fig03_rt60_octave_bands.csv"
    bands, values = [], []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            bands.append(row['octave_band'])
            values.append(float(row['rt60_T30_seconds']))

    fig, ax = plt.subplots(figsize=(COL_W, 2.4))
    x = np.arange(len(bands))
    colors = plt.cm.coolwarm(np.linspace(0.2, 0.8, len(bands)))
    bars = ax.bar(x, values, color=colors, alpha=0.85,
                  edgecolor='black', linewidth=0.4)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.04,
                f'{val:.2f}', ha='center', va='bottom', fontsize=FS_ANNOT)
    ax.set_xticks(x)
    ax.set_xticklabels(bands, fontsize=FS_TICK)
    ax.set_ylim(0, 2.85)
    avg = np.mean(values)
    ax.axhline(avg, color='red', linestyle='--', linewidth=1.0, alpha=0.8,
               label=f'Broadband avg: {avg:.2f} s')
    _apply_ieee_style(ax,
                      xlabel='Octave Band Center Frequency',
                      ylabel='Reverberation Time T30 (s)',
                      legend_loc='upper right', grid_axis='y')
    fig.tight_layout(pad=0.3)
    _save(fig, "pub_fig03_rt60_octave_bands.png")


# ---------------------------------------------------------------------------
# Figure 4 - Geographic map  (copy full-size render from plots/)
# ---------------------------------------------------------------------------
def render_fig04():
    """Re-render both maps from the committed location CSV.

    Needs contextily and geopandas for the basemap tiles (and network access to
    fetch them), so unlike the other figures this one can fail on a bare install;
    the published renders are committed under figures/ either way.
    """
    print("\n[fig04] Geographic map")
    csv_path = PLOTS_DIR / "pub_fig04_geographic_map.csv"
    if not csv_path.exists():
        print(f"  Warning: {csv_path} not found - skipping")
        return

    # generate_all_figures imports these lazily, deep inside the plotting call,
    # so check here rather than letting it fail halfway through rendering.
    try:
        import contextily  # noqa: F401
        import geopandas  # noqa: F401
    except ImportError:
        print("  Skipping: needs the optional map extras")
        print("    pip install contextily geopandas")
        print("  The published renders are committed under figures/")
        return

    sys.path.insert(0, str(Path(__file__).parent))
    from generate_all_figures import (load_locations_from_csv,
                                      plot_geographic_map)

    locations = load_locations_from_csv(csv_path)
    plot_geographic_map(locations=locations, output_dir=IEEE_FIG_DIR)


# ---------------------------------------------------------------------------
# Figure 5 - Recording timeline  (rendered at full textwidth, compact height)
# ---------------------------------------------------------------------------
# IEEE Access textwidth ~ 7.0 in (505 pt).  Timeline is figure* so it uses
# the full two-column width.  Height is kept very short - events are just dots.
TW = 7.0   # target printed width for figure* floats

def render_fig05():
    print("\n[fig05] Recording timeline")
    csv_path = PLOTS_DIR / "pub_fig05_timeline.csv"
    sessions = []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            try:
                sessions.append({
                    'date':         datetime.strptime(row['date'], '%Y-%m-%d'),
                    'content_type': row['content_type'],
                    'is_outdoor':   row['is_outdoor'].lower() == 'true',
                })
            except (ValueError, KeyError):
                pass

    type_styles = {
        'solo_piano':           ('#1f77b4', 'o', 'Solo piano'),
        'piano_duet':           ('#1f77b4', 'o', 'Solo piano'),
        'choir':                ('#2ca02c', 's', 'Choir'),
        'choir_with_orchestra': ('#2ca02c', 's', 'Choir'),
        'choir_with_soloists':  ('#2ca02c', 's', 'Choir'),
        'choir_with_ensemble':  ('#2ca02c', 's', 'Choir'),
        'orchestra':            ('#d62728', 'D', 'Orch./Ensemble'),
        'ensemble':             ('#d62728', 'D', 'Orch./Ensemble'),
        'chamber':              ('#9467bd', '^', 'Chamber'),
        'ambient':              ('#e377c2', '*', 'Outdoor/Ambient'),
        'ambience':             ('#e377c2', '*', 'Outdoor/Ambient'),
        'vr_film_production':   ('#17becf', 'v', 'VR/Film'),
        'unknown':              ('#7f7f7f', 'x', 'Other'),
    }

    # 3-lane staggering; centre shifted down so points don't crowd the legend
    LANES = [-0.18, 0.0, 0.18]
    CENTRE = 0.92   # slightly below midpoint, leaving more space above for legend

    fig, ax = plt.subplots(figsize=(TW, 1.5))
    seen_labels = set()
    for i, s in enumerate(sessions):
        c, m, lbl = type_styles.get(s['content_type'], ('#7f7f7f', 'x', 'Other'))
        y = CENTRE + LANES[i % 3]
        kw = dict(marker=m, color=c, markersize=5, markeredgewidth=0.3,
                  markeredgecolor='white', zorder=4, linestyle='none')
        if lbl not in seen_labels:
            ax.plot(s['date'], y, label=lbl, **kw)
            seen_labels.add(lbl)
        else:
            ax.plot(s['date'], y, **kw)
        if s['is_outdoor']:
            ax.plot(s['date'], y, marker='o', color='none',
                    markersize=9, markeredgewidth=0.8,
                    markeredgecolor='black', zorder=3, linestyle='none')

    ax.plot([], [], marker='o', color='none', markersize=9, markeredgewidth=0.8,
            markeredgecolor='black', linestyle='none', label='Outdoor venue')

    ax.set_ylim(0.60, 1.35)
    ax.set_yticks([])
    ax.tick_params(axis='x', labelsize=FS_TICK)
    ax.grid(True, axis='x', alpha=0.25, linewidth=0.5)
    ax.set_xlabel('Recording Date', fontsize=FS_LABEL)

    handles, labels = ax.get_legend_handles_labels()
    seen, h2, l2 = set(), [], []
    for h, l in zip(handles, labels):
        if l not in seen:
            h2.append(h); l2.append(l); seen.add(l)
    # All categories in a single row - figure is wide enough (7 in)
    ax.legend(h2, l2, loc='upper left', fontsize=FS_LEGEND,
              ncol=len(l2), framealpha=0.9, edgecolor='0.8',
              borderpad=0.4, handlelength=1.0)
    fig.tight_layout(pad=0.3)
    _save(fig, "pub_fig05_timeline.png")


# ---------------------------------------------------------------------------
# Figure 6 - LUFS corpus histogram
# ---------------------------------------------------------------------------
def render_fig06():
    print("\n[fig06] LUFS corpus histogram")
    lufs_values = []
    with open(DATA_DIR / "render_stats_all.csv") as f:
        for row in csv.DictReader(f):
            if ('NOT-TO-PUBLISH' in row.get('session', '') or
                    'NOT-TO-PUBLISH' in row.get('filename', '')):
                continue
            try:
                lufs_values.append(float(row['lufs_i']))
            except (ValueError, KeyError):
                pass

    min_v = np.floor(min(lufs_values) / 2) * 2
    max_v = np.ceil(max(lufs_values) / 2) * 2
    bins = np.arange(min_v, max_v + 2, 2)

    fig, ax = plt.subplots(figsize=(COL_W, 2.4))
    ax.hist(lufs_values, bins=bins, color='#1f77b4', edgecolor='white',
            linewidth=0.4, alpha=0.85)
    mean_v   = np.mean(lufs_values)
    median_v = np.median(lufs_values)
    ax.axvline(mean_v,   color='#d62728', linestyle='--', linewidth=1.2,
               label=f'Mean: {mean_v:.1f} LUFS')
    ax.axvline(median_v, color='#2ca02c', linestyle=':',  linewidth=1.2,
               label=f'Median: {median_v:.1f} LUFS')
    _apply_ieee_style(ax,
                      xlabel='LUFS-I (Integrated Loudness)',
                      ylabel='Number of Files',
                      legend_loc='upper left', grid_axis='y')
    fig.tight_layout(pad=0.3)
    _save(fig, "pub_fig06_lufs_corpus.png")
    print(f"    N={len(lufs_values)}, mean={mean_v:.2f}, median={median_v:.2f}")


# ---------------------------------------------------------------------------
# Figure 7 - Spectral comparison  (requires audio drive)
# ---------------------------------------------------------------------------
def render_fig07():
    print("\n[fig07] Spectral comparison (processing audio - may take a minute)")
    try:
        sys.path.insert(0, str(SCRIPT_DIR / "pyscripts"))
        from analysis_utils import (MIC_FILES, MIC_COLORS,
                                    MIC_COMPARISON_SESSION,
                                    compute_spectral_average)
    except ImportError as e:
        print(f"  Skipped: {e}")
        return
    if MIC_COMPARISON_SESSION is None:
        print("  Skipped: set HOA_CORPUS_DIR to the corpus audio (download from doi.org/10.34808/w8bx-2094);"
              " the published render is committed under figures/")
        return

    plot_order  = ["Saramonic (1OA)", "ZM-1 (3OA)", "Spcmic (3OA)", "Spcmic (5OA)"]
    line_styles = {
        "Saramonic (1OA)": {'lw': 1.2, 'ls': '-',  'alpha': 0.90},
        "ZM-1 (3OA)":      {'lw': 1.2, 'ls': '-',  'alpha': 0.85},
        "Spcmic (3OA)":    {'lw': 1.5, 'ls': '-',  'alpha': 1.00},
        "Spcmic (5OA)":    {'lw': 0.9, 'ls': '--', 'alpha': 0.65},
    }

    fig, ax = plt.subplots(figsize=(COL_W, 2.4))
    n_plotted = 0
    for mic_name in plot_order:
        if mic_name not in MIC_FILES:
            continue
        audio_path = MIC_COMPARISON_SESSION / MIC_FILES[mic_name]
        if not audio_path.exists():
            print(f"  Warning: {audio_path.name} not found - skipping")
            continue
        n_plotted += 1
        print(f"  Processing {mic_name}...")
        freqs, mag_db = compute_spectral_average(audio_path,
                                                 excerpt_seconds=None,
                                                 smoothing_octave=6)
        ref = mag_db[np.argmin(np.abs(freqs - 1000))]
        mag_db -= ref
        mask = (freqs >= 20) & (freqs <= 20000)
        sty  = line_styles.get(mic_name, {'lw': 1.2, 'ls': '-', 'alpha': 0.9})
        ax.semilogx(freqs[mask], mag_db[mask],
                    label=mic_name, color=MIC_COLORS[mic_name],
                    linewidth=sty['lw'], linestyle=sty['ls'], alpha=sty['alpha'])

    if not n_plotted:
        # nothing to plot: leave the committed figure alone instead of overwriting it with empty axes
        print(f"  Skipped: no comparison audio under {MIC_COMPARISON_SESSION}")
        plt.close(fig)
        return

    ax.set_xlim(20, 20000)
    ax.set_ylim(-30, 15)
    for f in [63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]:
        ax.axvline(f, color='gray', alpha=0.15, linewidth=0.4)
    _apply_ieee_style(ax,
                      xlabel='Frequency (Hz)',
                      ylabel='Relative Level (dB)',
                      legend_loc='upper right',
                      legend_kw={'handlelength': 1.5},
                      grid_axis='both')
    fig.tight_layout(pad=0.3)
    _save(fig, "pub_fig07_spectral_comparison.png")


# ---------------------------------------------------------------------------
# Figure 8 - LUFS mic comparison (horizontal bar)
# ---------------------------------------------------------------------------
def render_fig08():
    print("\n[fig08] LUFS mic comparison")
    csv_path = PLOTS_DIR / "pub_fig08_lufs_mic_comparison.csv"
    raw_labels, values = [], []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            raw_labels.append(row['label'])
            values.append(float(row['lufs_i']))

    # Split "Mic (OA): PieceName" -> two-line label "Mic (OA)\nPieceName"
    def _two_line(lbl):
        if ': ' in lbl:
            mic, piece = lbl.split(': ', 1)
            # Shorten verbose piece names
            piece = (piece.replace('CFranck-PreludeChoralFugue', 'C. Franck - Prélude')
                         .replace('SProkofiev-Sonata4', 'S. Prokofiev - Sonata 4'))
            return f"{mic}\n{piece}"
        return lbl

    labels = [_two_line(l) for l in raw_labels]

    # Color by microphone family
    def _color(lbl):
        if 'SR-VRMIC' in lbl or '1OA' in lbl: return '#d62728'
        if 'ZM-1'    in lbl:                  return '#1f77b4'
        if '3OA'     in lbl:                  return '#ff7f0e'
        if '5OA'     in lbl:                  return '#2ca02c'
        return '#7f7f7f'

    colors = [_color(l) for l in raw_labels]
    n      = len(labels)
    fig, ax = plt.subplots(figsize=(COL_W, max(2.4, n * 0.38)))
    y_pos = np.arange(n)
    ax.barh(y_pos, values, color=colors, alpha=0.85, edgecolor='white',
            linewidth=0.3)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=FS_TICK)
    for i, v in enumerate(values):
        ax.text(v + 0.2, i, f'{v:.1f}', va='center', fontsize=FS_ANNOT)
    ax.axvline(-23, color='green', linestyle='--', linewidth=0.9, alpha=0.7,
               label='EBU R128 (-23 LUFS)')
    _apply_ieee_style(ax,
                      xlabel='LUFS-I (Integrated Loudness)',
                      legend_loc='lower right', grid_axis='x')
    fig.tight_layout(pad=0.3)
    _save(fig, "pub_fig08_lufs_mic_comparison.png")


# ---------------------------------------------------------------------------
# Figure 9 - Spatial energy per Ambisonics order
# ---------------------------------------------------------------------------
def render_fig09():
    print("\n[fig09] Spatial energy per order")
    csv_path = PLOTS_DIR / "pub_fig09_spatial_energy.csv"
    mic_data = []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            entry = {'name': row['microphone'], 'max_order': int(row['max_order'])}
            for k, v in row.items():
                if k.startswith('order_') and k.endswith('_dBFS') and v:
                    try:
                        order = int(k.split('_')[1])
                        entry[order] = float(v)
                    except ValueError:
                        pass
            mic_data.append(entry)

    # Original color scheme from generate_all_figures.py MIC_ORDER
    mic_colors  = {
        'SR-VRMIC (1OA)': '#d62728',   # Red
        'ZM-1 (3OA)':     '#1f77b4',   # Blue
        'Spcmic (3OA)':   '#ff7f0e',   # Orange
        'Spcmic (5OA)':   '#2ca02c',   # Green
    }
    mic_markers = {
        'SR-VRMIC (1OA)': 'o',
        'ZM-1 (3OA)':     's',
        'Spcmic (3OA)':   '^',
        'Spcmic (5OA)':   'D',
    }

    x_labels = ['0th (W)\nOmni', '1st\nDipole', '2nd', '3rd', '4th', '5th']

    fig, ax = plt.subplots(figsize=(COL_W, 2.6))
    for mic in mic_data:
        orders = sorted(k for k in mic if isinstance(k, int))
        vals   = [mic[o] for o in orders]
        c = mic_colors.get(mic['name'], '#7f7f7f')
        m = mic_markers.get(mic['name'], 'o')
        ax.plot(orders, vals, marker=m, color=c, markersize=5,
                linewidth=1.5, linestyle='--', alpha=0.9, label=mic['name'])

    ax.set_xticks(range(6))
    ax.set_xticklabels(x_labels, fontsize=FS_TICK)
    ax.set_xlim(-0.3, 5.3)
    _apply_ieee_style(ax,
                      xlabel='Ambisonics Order',
                      ylabel='RMS Level (dBFS)',
                      legend_loc='upper right',
                      legend_kw={'handlelength': 1.5},
                      grid_axis='both')
    fig.tight_layout(pad=0.3)
    _save(fig, "pub_fig09_spatial_energy.png")


# ---------------------------------------------------------------------------
# Figure 10 - Directional distribution (two separate figures: 10a and 10b)
# ---------------------------------------------------------------------------
def render_fig10():
    print("\n[fig10] Directional distribution (two separate figures)")
    csv_path = PLOTS_DIR / "pub_fig10_directional_distribution.csv"
    mic_data = []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            try:
                mic_data.append({
                    'name':  row['microphone'],
                    'W_rms': float(row['W_rms']),
                    'X_rms': float(row['X_rms']),
                    'Y_rms': float(row['Y_rms']),
                    'Z_rms': float(row['Z_rms']),
                })
            except (ValueError, KeyError):
                pass

    # Original colors from generate_all_figures.py
    mic_colors = {
        'SR-VRMIC (1OA)': '#d62728',
        'ZM-1 (3OA)':     '#1f77b4',
        'Spcmic (3OA)':   '#ff7f0e',
        'Spcmic (5OA)':   '#2ca02c',
    }
    names  = [m['name'] for m in mic_data]
    colors = [mic_colors.get(n, '#7f7f7f') for n in names]
    x_pos  = np.arange(len(names))
    # Abbreviate x-tick labels to fit single-column width
    x_tick_labels = ['SR-VRMIC\n(1OA)', 'ZM-1\n(3OA)', 'Spcmic\n(3OA)', 'Spcmic\n(5OA)']

    # --- Figure 10a: W-channel level (dBFS) ---
    fig1, ax1 = plt.subplots(figsize=(COL_W, 1.7))
    w_db = [20 * np.log10(m['W_rms']) for m in mic_data]
    ax1.bar(x_pos, w_db, width=0.45, color=colors, alpha=0.85,
            edgecolor='black', linewidth=0.4)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(x_tick_labels, fontsize=FS_TICK)
    ax1.set_ylabel('W Channel Level (dBFS)', fontsize=FS_LABEL)
    ax1.tick_params(axis='y', labelsize=FS_TICK)
    ax1.grid(True, axis='y', alpha=0.3, linewidth=0.5, linestyle=':')
    fig1.tight_layout(pad=0.3)
    _save(fig1, "pub_fig10a_w_channel_level.png")

    # --- Figure 10b: XYZ normalised to W ---
    w_bar = {'X': [], 'Y': [], 'Z': []}
    for m in mic_data:
        w = m['W_rms']
        w_bar['X'].append(m['X_rms'] / w if w else 0)
        w_bar['Y'].append(m['Y_rms'] / w if w else 0)
        w_bar['Z'].append(m['Z_rms'] / w if w else 0)

    bar_w = 0.25
    comp_colors = {
        'X': '#d62728',   # Front-Back - red
        'Y': '#1f77b4',   # Left-Right - blue
        'Z': '#2ca02c',   # Up-Down    - green
    }
    comp_labels = {
        'X': 'X (Front-Back)',
        'Y': 'Y (Left-Right)',
        'Z': 'Z (Up-Down)',
    }
    fig2, ax2 = plt.subplots(figsize=(COL_W, 1.7))
    for i, comp in enumerate(['X', 'Y', 'Z']):
        offset = (i - 1) * bar_w
        ax2.bar(x_pos + offset, w_bar[comp], bar_w,
                color=comp_colors[comp], alpha=0.85,
                edgecolor='black', linewidth=0.4,
                label=comp_labels[comp])
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(x_tick_labels, fontsize=FS_TICK)
    ax2.set_ylabel('Normalized to W Channel', fontsize=FS_LABEL)
    ax2.tick_params(axis='y', labelsize=FS_TICK)
    ax2.grid(True, axis='y', alpha=0.3, linewidth=0.5, linestyle=':')
    ax2.legend(fontsize=FS_LEGEND, framealpha=0.9, edgecolor='0.8',
               borderpad=0.3, handlelength=1.0, loc='lower left')
    fig2.tight_layout(pad=0.3)
    _save(fig2, "pub_fig10b_xyz_normalized.png")


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
FIGURES = {
    '03': render_fig03,
    '04': render_fig04,
    '05': render_fig05,
    '06': render_fig06,
    '07': render_fig07,
    '08': render_fig08,
    '09': render_fig09,
    '10': render_fig10,
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("figures", nargs="*", help="figure numbers to render, e.g. 06 09 10 (default: all)")
    requested = ap.parse_args().figures or sorted(FIGURES)
    unknown = [r for r in requested if r not in FIGURES]
    if unknown:
        print(f"Unknown figure numbers: {unknown}")
        print(f"Available: {sorted(FIGURES.keys())}")
        sys.exit(1)

    print(f"Output -> {IEEE_FIG_DIR}")
    for fig_id in requested:
        FIGURES[fig_id]()

    print(f"\nDone - {len(requested)} figure(s) written to {IEEE_FIG_DIR}")


if __name__ == "__main__":
    main()
