#!/usr/bin/env python3
"""
Figures 9, 10a and 10b of the HOA corpus paper with bootstrap confidence intervals.

Reads the bootstrap outputs of revision_stats.py and renders, in the same IEEE
single-column style as render_ieee_figures.py:

  pub_fig09_spatial_energy_2piece.png   Franck | Prokofiev side-by-side
                                        per-order RMS with 95% CIs
                                        + ideal SN3D diffuse-field profiles
  pub_fig10a_w_channel_level_ci.png     W level with 95% CIs (Franck)
  pub_fig10b_xyz_normalized_ci.png      X/Y/Z over W with 95% CIs (Franck)

Usage:
    python revision_figures.py
"""

import argparse
import csv
import os
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Paths are resolved relative to this file so the script runs from a clean clone.
# Override the figure output directory with the IEEE_FIG_DIR environment variable
# (e.g. point it at the manuscript's figures/ folder).
SCRIPT_DIR = Path(__file__).resolve().parent.parent
REV_RESULTS = Path(os.environ.get("REVISION_RESULTS_DIR", SCRIPT_DIR / "revision_results"))
IEEE_FIG_DIR = Path(os.environ.get("IEEE_FIG_DIR", SCRIPT_DIR / "revision_results" / "figures"))
IEEE_FIG_DIR.mkdir(parents=True, exist_ok=True)

COL_W = 3.5
FS_LABEL, FS_TICK, FS_LEGEND = 7.5, 6.5, 6.5
DPI = 300

MIC_COLORS = {
    'SR-VRMIC (1OA)': '#d62728',
    'ZM-1 (3OA)':     '#1f77b4',
    'Spcmic (3OA)':   '#ff7f0e',
    'Spcmic (5OA)':   '#2ca02c',
}
MIC_MARKERS = {
    'SR-VRMIC (1OA)': 'o',
    'ZM-1 (3OA)':     's',
    'Spcmic (3OA)':   '^',
    'Spcmic (5OA)':   'D',
}
MIC_ORDER = ['SR-VRMIC (1OA)', 'ZM-1 (3OA)', 'Spcmic (3OA)', 'Spcmic (5OA)']


def load_rows(name):
    with open(REV_RESULTS / name) as f:
        return list(csv.DictReader(f))


def fig09_two_piece(rows):
    fig, axes = plt.subplots(1, 2, figsize=(COL_W * 2, 2.6), sharey=True)
    for ax, piece in zip(axes, ('Franck', 'Prokofiev')):
        for mic in MIC_ORDER:
            row = next((r for r in rows
                        if r['microphone'] == mic and r['piece'] == piece), None)
            if row is None:
                continue
            orders, vals, lo_err, hi_err = [], [], [], []
            for o in range(6):
                v = row.get(f'order{o}_dBFS', '')
                if v:
                    orders.append(o)
                    vals.append(float(v))
                    lo_err.append(float(v) - float(row[f'order{o}_ci_lo']))
                    hi_err.append(float(row[f'order{o}_ci_hi']) - float(v))
            ax.errorbar(orders, vals, yerr=[lo_err, hi_err],
                        marker=MIC_MARKERS[mic], color=MIC_COLORS[mic],
                        markersize=5, linewidth=1.5, linestyle='--',
                        alpha=0.9, capsize=2, elinewidth=0.7, label=mic)
            if orders[-1] >= 3:
                ideal = [vals[0] - 10 * np.log10(2 * o + 1) for o in orders]
                # zorder between the grid (1.5) and the measured curves (2)
                ax.plot(orders, ideal, color=MIC_COLORS[mic], linestyle='--',
                        linewidth=0.8, alpha=0.5, zorder=1.8)
        ax.set_xticks(range(6))
        ax.set_xticklabels(['0th\n(W)', '1st', '2nd', '3rd', '4th', '5th'],
                           fontsize=FS_TICK)
        ax.set_xlim(-0.3, 5.3)
        ax.set_xlabel('Ambisonics Order', fontsize=FS_LABEL)
        ax.set_title(piece, fontsize=FS_LABEL)
        ax.tick_params(axis='both', labelsize=FS_TICK)
        ax.grid(True, axis='both', alpha=0.3, linewidth=0.5)
    axes[0].set_ylabel('RMS Level (dBFS)', fontsize=FS_LABEL)
    arrays = axes[1].legend(fontsize=FS_LEGEND, framealpha=0.9, edgecolor='0.8',
                            borderpad=0.4, handlelength=1.5, loc='lower left')
    # separate legend: a fifth row at lower left would cover the ZM-1 2nd-order point
    axes[1].add_artist(arrays)
    axes[1].legend([Line2D([], [], color='0.4', linestyle='--', linewidth=0.8)],
                   ['ideal SN3D diffuse-field profile'], fontsize=FS_LEGEND,
                   framealpha=0.9, edgecolor='0.8', borderpad=0.4,
                   handlelength=1.5, loc='upper right')
    fig.tight_layout(pad=0.3)
    out = IEEE_FIG_DIR / "pub_fig09_spatial_energy_2piece.png"
    fig.savefig(out, dpi=DPI, bbox_inches='tight')
    plt.close(fig)
    print(f"  {out}")


def fig10_ci(rows):
    franck = {r['microphone']: r for r in rows if r['piece'] == 'Franck'}
    mics = [m for m in MIC_ORDER if m in franck]
    x_pos = np.arange(len(mics))
    x_lab = [m.replace(' (', '\n(') for m in mics]
    colors = [MIC_COLORS[m] for m in mics]

    # --- 10a: W level (dBFS) with CI ---
    w = [float(franck[m]['W_dBFS']) for m in mics]
    w_lo = [float(franck[m]['W_dBFS']) - float(franck[m]['W_dBFS_ci_lo']) for m in mics]
    w_hi = [float(franck[m]['W_dBFS_ci_hi']) - float(franck[m]['W_dBFS']) for m in mics]
    fig1, ax1 = plt.subplots(figsize=(COL_W, 1.7))
    ax1.bar(x_pos, w, width=0.45, color=colors, alpha=0.85,
            edgecolor='black', linewidth=0.4,
            yerr=[w_lo, w_hi], capsize=2.5,
            error_kw=dict(elinewidth=0.8, capthick=0.8))
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(x_lab, fontsize=FS_TICK)
    ax1.set_ylabel('W Channel Level (dBFS)', fontsize=FS_LABEL)
    ax1.tick_params(axis='y', labelsize=FS_TICK)
    ax1.grid(True, axis='y', alpha=0.3, linewidth=0.5, linestyle=':')
    fig1.tight_layout(pad=0.3)
    out1 = IEEE_FIG_DIR / "pub_fig10a_w_channel_level_ci.png"
    fig1.savefig(out1, dpi=DPI, bbox_inches='tight')
    plt.close(fig1)
    print(f"  {out1}")

    # --- 10b: X/Y/Z over W with CI ---
    comp_colors = {'X': '#d62728', 'Y': '#1f77b4', 'Z': '#2ca02c'}
    comp_labels = {'X': 'X (Front-Back)', 'Y': 'Y (Left-Right)', 'Z': 'Z (Up-Down)'}
    bar_w = 0.25
    fig2, ax2 = plt.subplots(figsize=(COL_W, 1.7))
    for i, comp in enumerate(['X', 'Y', 'Z']):
        vals = [float(franck[m][f'{comp}_over_W']) for m in mics]
        lo = [float(franck[m][f'{comp}_over_W']) -
              float(franck[m][f'{comp}_over_W_ci_lo']) for m in mics]
        hi = [float(franck[m][f'{comp}_over_W_ci_hi']) -
              float(franck[m][f'{comp}_over_W']) for m in mics]
        ax2.bar(x_pos + (i - 1) * bar_w, vals, bar_w,
                color=comp_colors[comp], alpha=0.85,
                edgecolor='black', linewidth=0.4, label=comp_labels[comp],
                yerr=[lo, hi], capsize=1.8,
                error_kw=dict(elinewidth=0.7, capthick=0.7))
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(x_lab, fontsize=FS_TICK)
    ax2.set_ylabel('Normalised to W Channel', fontsize=FS_LABEL)
    ax2.tick_params(axis='y', labelsize=FS_TICK)
    ax2.grid(True, axis='y', alpha=0.3, linewidth=0.5, linestyle=':')
    ax2.legend(fontsize=FS_LEGEND, framealpha=0.9, edgecolor='0.8',
               borderpad=0.3, handlelength=1.0, loc='lower left')
    fig2.tight_layout(pad=0.3)
    out2 = IEEE_FIG_DIR / "pub_fig10b_xyz_normalized_ci.png"
    fig2.savefig(out2, dpi=DPI, bbox_inches='tight')
    plt.close(fig2)
    print(f"  {out2}")


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    fig09_two_piece(load_rows("spatial_energy_two_piece.csv"))
    fig10_ci(load_rows("directional_ci.csv"))
