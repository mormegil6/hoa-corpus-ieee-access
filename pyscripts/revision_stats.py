#!/usr/bin/env python3
"""
revision_stats.py
=================

Uncertainty estimates for the microphone-comparison results of the HOA corpus
paper (IEEE Access). Uses the same per-order RMS definition as the companion
AES Copenhagen paper's analysis (github.com/mormegil6/hoa-mic-comparison-aes2026,
analyze_paper.py), reimplemented here so this repo has no cross-repo dependency.

Method
------
Each recording of the co-located comparison session (2024-08-15) is streamed
in 1-second frames; per-frame per-channel sums of squares are cached. All
arrays recorded the same performance simultaneously, so frames are paired
across arrays by wall-clock time. A paired moving-block bootstrap (block
length 30 s by default, 2000 replicates, fixed seed) resamples frame indices
- the SAME indices for both arrays of a pair - and recomputes the per-order
RMS levels, the 0th-to-3rd order rolloff of each array, and the between-array
rolloff difference for each replicate. Percentile 95% confidence intervals
and the bootstrap standard error (SD of the replicates) are reported.

The block bootstrap respects the strong temporal correlation of musical
material; the paired design removes the shared programme-level variance.
The resulting CI quantifies the within-recording temporal variability of the
reported differences: how much the estimate moves when 30-s stretches of this
one performance are resampled. It carries no information about other venues,
sessions, performances, or physical units, and is not a claim of
generalization beyond the comparison session.

--block-seconds changes the block length of the main analysis. --block-sweep
re-runs the rolloff bootstraps at several block lengths (each from a fresh
generator with the same seed) and reports the CI widths, so the sensitivity
of the intervals to the block-length choice can be cited.

Outputs (revision_results/)
---------------------------
  cache/frames_<key>.npz              per-frame per-channel energy cache
  spatial_energy_two_piece.csv        per-order dBFS + 95% CI, all arrays x pieces
  rolloff_bootstrap.csv               rolloff + difference CIs and bootstrap SEs
  directional_ci.csv                  W dBFS and X/Y/Z-over-W with 95% CIs
  frame_order_energies_<key>.csv      frame-level per-order dBFS (release artifact)
  frame_difference_3OA_<piece>.csv    frame-level ZM-1 vs Spcmic 3OA difference file
  block_sensitivity.csv               rolloff CIs per block length (--block-sweep)
  revision_stats_variables.tex        \\newcommand definitions for the manuscript

Usage:
    python revision_stats.py --base-dir /path/to/deposit
    python revision_stats.py --base-dir /any/path --block-sweep 10,20,30,60,120

--base-dir is the deposit root (audio under
sessions/2024-08-15_aula-pg_solo-piano-mic-comparison/audio/) and is only
consulted for recordings whose frame cache is missing; the deposit layout is tried first.
"""

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import soundfile as sf

# Comparison-session audio relative to --base-dir (the deposit root).
SESSION_AUDIO_DIR = Path("sessions") / "2024-08-15_aula-pg_solo-piano-mic-comparison" / "audio"

# ACN ordering, channel ranges per Ambisonics order.
ORDER_RANGES = {0: (0, 1), 1: (1, 4), 2: (4, 9), 3: (9, 16), 4: (16, 25), 5: (25, 36)}

FRAME_SECONDS = 1.0
BLOCK_SECONDS = 30
N_BOOT = 2000
SEED = 2026
CI_LO, CI_HI = 2.5, 97.5

# (key, filename, mic, format, piece) - comparison session only, incl. SR-VRMIC
RECORDINGS = [
    ("ZMOneFranck",            "3OA_ZM1_CFranck-PreludeChoralFugue.wav",     "ZM-1",     "3OA", "Franck"),
    ("ZMOneProkofiev",         "3OA_ZM1_SProkofiev-Sonata4.wav",             "ZM-1",     "3OA", "Prokofiev"),
    ("SpcmicThreeOAFranck",    "3OA_Spcmic_CFranck-PreludeChoralFugue.wav",  "Spcmic",   "3OA", "Franck"),
    ("SpcmicThreeOAProkofiev", "3OA_Spcmic_SProkofiev-Sonata4.wav",          "Spcmic",   "3OA", "Prokofiev"),
    ("SpcmicFiveOAFranck",     "5OA_Spcmic_CFranck-PreludeChoralFugue.wav",  "Spcmic",   "5OA", "Franck"),
    ("SpcmicFiveOAProkofiev",  "5OA_Spcmic_SProkofiev-Sonata4.wav",          "Spcmic",   "5OA", "Prokofiev"),
    ("SRVRMICFranck",          "1OA_SRVRMIC_CFranck-PreludeChoralFugue.wav", "SR-VRMIC", "1OA", "Franck"),
    ("SRVRMICProkofiev",       "1OA_SRVRMIC_SProkofiev-Sonata4.wav",         "SR-VRMIC", "1OA", "Prokofiev"),
]

PAIRS = [  # paired bootstrap: ZM-1 vs Spcmic, same piece, both at 3OA
    ("Franck",    "ZMOneFranck",    "SpcmicThreeOAFranck"),
    ("Prokofiev", "ZMOneProkofiev", "SpcmicThreeOAProkofiev"),
]

MIC_LABEL = {
    "ZMOneFranck": "ZM-1 (3OA)", "ZMOneProkofiev": "ZM-1 (3OA)",
    "SpcmicThreeOAFranck": "Spcmic (3OA)", "SpcmicThreeOAProkofiev": "Spcmic (3OA)",
    "SpcmicFiveOAFranck": "Spcmic (5OA)", "SpcmicFiveOAProkofiev": "Spcmic (5OA)",
    "SRVRMICFranck": "SR-VRMIC (1OA)", "SRVRMICProkofiev": "SR-VRMIC (1OA)",
}

SWEEP_MACRO_KEYS = ("ZMOneFranck", "ZMOneProkofiev")


def session_audio_dir(base_dir):
    """Audio folder of the comparison session under the deposit root."""
    return base_dir / SESSION_AUDIO_DIR


def max_order_for(n_channels):
    return 5 if n_channels >= 36 else 3 if n_channels >= 16 else 1


def build_frame_cache(path, cache_path):
    """Stream a WAV in 1-s frames; cache per-frame per-channel sum of squares."""
    if cache_path.exists():
        z = np.load(cache_path)
        return z["energy"], z["counts"], int(z["sr"])
    info = sf.info(str(path))
    sr = info.samplerate
    frame_len = int(round(sr * FRAME_SECONDS))
    energies, counts = [], []
    with sf.SoundFile(str(path)) as f:
        for block in f.blocks(blocksize=frame_len, dtype="float32"):
            if block.ndim == 1:
                block = block.reshape(-1, 1)
            energies.append(np.sum(block.astype(np.float64) ** 2, axis=0))
            counts.append(block.shape[0])
    energy = np.vstack(energies)
    counts = np.asarray(counts, dtype=np.int64)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache_path, energy=energy, counts=counts, sr=sr)
    return energy, counts, sr


def order_levels_from_selection(energy, counts, sel, max_order):
    """Per-order dBFS from selected frame indices; identical metric to
    analyze_paper.order_energies_dbfs (linear mean of per-channel RMS)."""
    ssum = energy[sel].sum(axis=0)
    n = counts[sel].sum()
    rms = np.sqrt(ssum / n)
    out = {}
    for order in range(max_order + 1):
        s, e = ORDER_RANGES[order]
        if e <= len(rms):
            out[order] = 20.0 * np.log10(float(np.mean(rms[s:e])) + 1e-20)
    return out


def directional_from_selection(energy, counts, sel):
    ssum = energy[sel].sum(axis=0)
    n = counts[sel].sum()
    rms = np.sqrt(ssum / n)
    w = rms[0]
    return {
        "W_dBFS": 20.0 * np.log10(w + 1e-20),
        # ACN: 0=W, 1=Y, 2=Z, 3=X
        "X_over_W": float(rms[3] / w),
        "Y_over_W": float(rms[1] / w),
        "Z_over_W": float(rms[2] / w),
    }


def block_bootstrap_indices(rng, n, block_len, n_boot):
    """Yield n_boot arrays of frame indices from a moving-block bootstrap."""
    n_blocks = int(np.ceil(n / block_len))
    starts_max = n - block_len
    for _ in range(n_boot):
        starts = rng.integers(0, starts_max + 1, size=n_blocks)
        idx = (starts[:, None] + np.arange(block_len)[None, :]).ravel()[:n]
        yield idx


def pct_ci(values):
    return float(np.percentile(values, CI_LO)), float(np.percentile(values, CI_HI))


def boot_se(values):
    return float(np.std(values, ddof=1))


def n_full_frames(counts):
    """Frames of full length; the trailing partial frame is dropped for the CI."""
    return int(np.sum(counts == counts.max()))


MAX_PAIR_LAG = 15


def pair_lag(cz, cs, max_lag=MAX_PAIR_LAG):
    """Integer-frame lag that aligns two renders of the same performance.

    The corpus renders of one session were exported from separate projects and
    do not start at the same instant, so frame i of one render is not frame i
    of the other. The lag is found by cross-correlating the per-frame W-channel
    log energy over -max_lag..max_lag frames; Spcmic frame = ZM-1 frame + lag.
    Returns (lag, r_at_lag, r_at_zero)."""
    def wlog(c):
        n = n_full_frames(c["counts"])
        return 10.0 * np.log10(c["energy"][:n, 0] / c["counts"][:n] + 1e-30)
    z, s = wlog(cz), wlog(cs)
    n = min(len(z), len(s))
    z, s = z[:n], s[:n]
    best = None
    r0 = None
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            a, b = z[:n - lag], s[lag:]
        else:
            a, b = z[-lag:], s[:n + lag]
        r = float(np.corrcoef(a, b)[0, 1])
        if lag == 0:
            r0 = r
        if best is None or r > best[1]:
            best = (lag, r)
    return best[0], best[1], r0


def paired_indices(cz, cs, lag):
    """ZM-1 and Spcmic frame indices of the same wall-clock second, full frames only."""
    nz, ns = n_full_frames(cz["counts"]), n_full_frames(cs["counts"])
    i0 = max(0, -lag)
    i1 = min(nz, ns - lag)
    iz = np.arange(i0, i1)
    return iz, iz + lag


def bootstrap_all(caches, block_seconds):
    """Single-array and paired bootstraps at one block length. Each call
    starts a fresh generator from SEED, so every block length of a sweep is
    an independent replication of the whole procedure."""
    rng = np.random.default_rng(SEED)
    block_len = int(round(block_seconds / FRAME_SECONDS))

    single = {}
    for key, c in caches.items():
        n_full = n_full_frames(c["counts"])
        all_idx = np.arange(len(c["counts"]))
        pt_orders = order_levels_from_selection(c["energy"], c["counts"], all_idx, c["max_order"])
        pt_dir = directional_from_selection(c["energy"], c["counts"], all_idx)

        boot_orders = {o: [] for o in pt_orders}
        boot_roll = []
        boot_dir = {k: [] for k in pt_dir}
        for idx in block_bootstrap_indices(rng, n_full, block_len, N_BOOT):
            ords = order_levels_from_selection(c["energy"], c["counts"], idx, c["max_order"])
            for o, v in ords.items():
                boot_orders[o].append(v)
            if 0 in ords and 3 in ords:
                boot_roll.append(ords[0] - ords[3])
            d = directional_from_selection(c["energy"], c["counts"], idx)
            for k, v in d.items():
                boot_dir[k].append(v)

        single[key] = {
            "orders": pt_orders,
            "order_ci": {o: pct_ci(v) for o, v in boot_orders.items()},
            "rolloff": ((pt_orders[0] - pt_orders[3], *pct_ci(boot_roll), boot_se(boot_roll))
                        if boot_roll else None),
            "dir": {k: (pt_dir[k], *pct_ci(v)) for k, v in boot_dir.items()},
        }

    paired = {}
    for piece, kz, ks in PAIRS:
        cz, cs = caches[kz], caches[ks]
        lag, r_lag, r0 = pair_lag(cz, cs)
        iz, is_ = paired_indices(cz, cs, lag)
        n = len(iz)
        pt_z = order_levels_from_selection(cz["energy"], cz["counts"],
                                           np.arange(len(cz["counts"])), 3)
        pt_s = order_levels_from_selection(cs["energy"], cs["counts"],
                                           np.arange(len(cs["counts"])), 3)
        pt_diff = (pt_z[0] - pt_z[3]) - (pt_s[0] - pt_s[3])
        boots = []
        for idx in block_bootstrap_indices(rng, n, block_len, N_BOOT):
            oz = order_levels_from_selection(cz["energy"], cz["counts"], iz[idx], 3)
            os_ = order_levels_from_selection(cs["energy"], cs["counts"], is_[idx], 3)
            boots.append((oz[0] - oz[3]) - (os_[0] - os_[3]))
        paired[piece] = (pt_diff, *pct_ci(boots), boot_se(boots), n, lag, r_lag, r0)

    return single, paired


def number_word(n):
    """LaTeX macro names cannot contain digits: 30 -> Thirty, 120 -> OneTwenty."""
    ones = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
            "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
            "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy",
            "Eighty", "Ninety"]
    if n < 20:
        return ones[n]
    if n < 100:
        return tens[n // 10] + (ones[n % 10] if n % 10 else "")
    if n < 1000:
        return ones[n // 100] + (number_word(n % 100) if n % 100 else "Hundred")
    raise ValueError(f"no macro name for a {n}-s block length")


def fmt(v, d=1):
    return f"{v:.{d}f}"


def main():
    ap = argparse.ArgumentParser(description="Paired moving-block bootstrap for the comparison session")
    ap.add_argument("--base-dir", type=Path, required=True,
                    help="deposit root (holding sessions/); read only for recordings "
                         "whose frame cache is missing, so any path is accepted when <out>/cache/ is complete")
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).resolve().parent.parent / "revision_results",
                    help="output directory, also holding cache/ (default %(default)s)")
    ap.add_argument("--block-seconds", type=int, default=BLOCK_SECONDS,
                    help="moving-block length in seconds (default %(default)s)")
    ap.add_argument("--block-sweep", type=lambda s: [int(v) for v in s.split(",")],
                    help="comma-separated block lengths in seconds, e.g. 10,20,30,60,120; "
                         "writes block_sensitivity.csv and the *Width* macros")
    args = ap.parse_args()

    render_dir = session_audio_dir(args.base_dir)
    args.out.mkdir(parents=True, exist_ok=True)
    cache_dir = args.out / "cache"

    # Audio is only needed for recordings whose frame cache is missing: with the
    # committed caches present, the whole analysis reproduces without the WAV files.
    missing = [f for k, f, *_ in RECORDINGS
               if not (cache_dir / f"frames_{k}.npz").exists()]
    if missing and not render_dir.exists():
        print(f"[!] Frame caches missing for {len(missing)} recording(s) and no audio "
              f"at {render_dir}\n[!] Pass --base-dir pointing at the corpus download "
              f"(doi.org/10.34808/w8bx-2094).", file=sys.stderr)
        sys.exit(1)

    caches = {}
    print(f"[i] Frame caches in {cache_dir}"
          + (f"; reading audio from {render_dir}" if missing else " (complete, no audio needed)"))
    for key, fname, mic, fmt_, piece in RECORDINGS:
        path = render_dir / fname
        if not path.exists() and not (cache_dir / f"frames_{key}.npz").exists():
            print(f"[!] Missing: {path}", file=sys.stderr)
            sys.exit(1)
        print(f"  - {key}")
        energy, counts, sr = build_frame_cache(path, cache_dir / f"frames_{key}.npz")
        caches[key] = dict(energy=energy, counts=counts, sr=sr,
                           mic=mic, format=fmt_, piece=piece,
                           max_order=max_order_for(energy.shape[1]))

    print(f"[i] Bootstrap: {args.block_seconds}-s blocks, {N_BOOT} replicates, seed {SEED}")
    single, paired = bootstrap_all(caches, args.block_seconds)

    # ---------------- per-file tables and frame-level release artifacts ----
    spatial_rows, dir_rows = [], []
    for key, c in caches.items():
        s = single[key]
        pt_orders = s["orders"]
        row = {"key": key, "microphone": MIC_LABEL[key], "mic": c["mic"],
               "format": c["format"], "piece": c["piece"],
               "max_order": c["max_order"]}
        for o in range(6):
            if o in pt_orders:
                lo, hi = s["order_ci"][o]
                row[f"order{o}_dBFS"] = f"{pt_orders[o]:.3f}"
                row[f"order{o}_ci_lo"] = f"{lo:.3f}"
                row[f"order{o}_ci_hi"] = f"{hi:.3f}"
        if s["rolloff"]:
            pt, lo, hi, se = s["rolloff"]
            row["rolloff_0_to_3_dB"] = f"{pt:.3f}"
            row["rolloff_ci_lo"] = f"{lo:.3f}"
            row["rolloff_ci_hi"] = f"{hi:.3f}"
        spatial_rows.append(row)

        drow = {"key": key, "microphone": MIC_LABEL[key], "piece": c["piece"]}
        for k in ("W_dBFS", "X_over_W", "Y_over_W", "Z_over_W"):
            pt, lo, hi = s["dir"][k]
            drow[k] = f"{pt:.4f}"
            drow[f"{k}_ci_lo"] = f"{lo:.4f}"
            drow[f"{k}_ci_hi"] = f"{hi:.4f}"
        dir_rows.append(drow)

        with open(args.out / f"frame_order_energies_{key}.csv", "w", newline="") as f:
            orders = sorted(pt_orders)
            w = csv.writer(f)
            w.writerow(["t_start_s"] + [f"order{o}_dBFS" for o in orders])
            for i in range(len(c["counts"])):
                ords = order_levels_from_selection(c["energy"], c["counts"],
                                                  np.array([i]), c["max_order"])
                w.writerow([f"{i * FRAME_SECONDS:.1f}"] +
                           [f"{ords[o]:.3f}" for o in orders])

    # ---------------- rolloff table and paired frame-level difference files -
    roll_rows = []
    for piece, kz, ks in PAIRS:
        pt_diff, lo, hi, se, n, lag, r_lag, r0 = paired[piece]
        print(f"[i] {piece}: pairing lag {lag:+d} frames (r={r_lag:.3f} at lag, {r0:.3f} at 0), {n} paired frames")
        roll_rows.append({"comparison": f"ZM1_minus_Spcmic3OA_{piece}",
                          "point_dB": f"{pt_diff:.3f}", "ci_lo": f"{lo:.3f}",
                          "ci_hi": f"{hi:.3f}", "bootstrap_se": f"{se:.3f}",
                          "n_frames": n, "block_s": args.block_seconds,
                          "replicates": N_BOOT, "pair_lag_frames": lag,
                          "pair_r_at_lag": f"{r_lag:.3f}", "pair_r_at_zero": f"{r0:.3f}"})

        # frame-level difference file (3OA pair), frames aligned by the lag
        cz, cs = caches[kz], caches[ks]
        iz, is_ = paired_indices(cz, cs, lag)
        with open(args.out / f"frame_difference_3OA_{piece}.csv", "w", newline="") as f:
            w = csv.writer(f)
            hdr = ["t_start_s", "zm1_frame", "spcmic_frame"]
            for tag in ("zm1", "spcmic"):
                hdr += [f"{tag}_order{o}_dBFS" for o in range(4)]
            hdr += [f"diff_order{o}_dB" for o in range(4)]
            w.writerow(hdr)
            for i, j in zip(iz, is_):
                oz = order_levels_from_selection(cz["energy"], cz["counts"],
                                                 np.array([i]), 3)
                os_ = order_levels_from_selection(cs["energy"], cs["counts"],
                                                  np.array([j]), 3)
                w.writerow([f"{i * FRAME_SECONDS:.1f}", int(i), int(j)] +
                           [f"{oz[o]:.3f}" for o in range(4)] +
                           [f"{os_[o]:.3f}" for o in range(4)] +
                           [f"{oz[o] - os_[o]:.3f}" for o in range(4)])

    rolloff_keys = [k for k in caches if single[k]["rolloff"]]
    for key in rolloff_keys:
        pt, lo, hi, se = single[key]["rolloff"]
        roll_rows.append({"comparison": f"rolloff_0_3_{key}",
                          "point_dB": f"{pt:.3f}", "ci_lo": f"{lo:.3f}",
                          "ci_hi": f"{hi:.3f}", "bootstrap_se": f"{se:.3f}",
                          "n_frames": len(caches[key]["counts"]),
                          "block_s": args.block_seconds, "replicates": N_BOOT})

    # ---------------- block-length sensitivity sweep -----------------------
    sweep_rows, sweep_widths = [], []
    for block_s in args.block_sweep or []:
        print(f"[i] Sweep: {block_s}-s blocks")
        b_single, b_paired = ((single, paired) if block_s == args.block_seconds
                              else bootstrap_all(caches, block_s))
        results = [(f"ZM1_minus_Spcmic3OA_{piece}", f"RolloffDelta{piece}", b_paired[piece][:4])
                   for piece, *_ in PAIRS]
        results += [(f"rolloff_0_3_{key}", f"Rolloff{key}", b_single[key]["rolloff"])
                    for key in rolloff_keys]
        for csv_key, macro, (pt, lo, hi, se) in results:
            sweep_rows.append({"block_s": block_s, "key": csv_key,
                               "pt": f"{pt:.3f}", "ci_lo": f"{lo:.3f}",
                               "ci_hi": f"{hi:.3f}", "width": f"{hi - lo:.3f}",
                               "se": f"{se:.3f}"})
            if macro.startswith("RolloffDelta") or macro[len("Rolloff"):] in SWEEP_MACRO_KEYS:
                sweep_widths.append((f"{macro}Width{number_word(block_s)}s", hi - lo))

    # ---------------- writers ----------------------------------------------
    def write_rows(path, rows):
        keys = []
        for r in rows:
            for k in r:
                if k not in keys:
                    keys.append(k)
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)

    write_rows(args.out / "spatial_energy_two_piece.csv", spatial_rows)
    write_rows(args.out / "directional_ci.csv", dir_rows)
    write_rows(args.out / "rolloff_bootstrap.csv", roll_rows)
    if sweep_rows:
        write_rows(args.out / "block_sensitivity.csv", sweep_rows)

    # ---------------- LaTeX variables ---------------------------------------
    lines = ["% Auto-generated by revision_stats.py - do not edit by hand.",
             f"% Generated: {datetime.now().isoformat(timespec='seconds')}",
             f"% Paired moving-block bootstrap: {FRAME_SECONDS:.0f}-s frames, "
             f"{args.block_seconds}-s blocks, {N_BOOT} replicates, seed {SEED}.", ""]

    def cmd(name, value):
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")

    cmd("StatsFrameSeconds", f"{FRAME_SECONDS:.0f}")
    cmd("StatsBlockSeconds", f"{args.block_seconds}")
    cmd("StatsBootstrapReplicates", f"{N_BOOT}")
    lines.append("")
    for key in rolloff_keys:
        pt, lo, hi, se = single[key]["rolloff"]
        cmd(f"Rolloff{key}Pt", fmt(pt))
        cmd(f"Rolloff{key}CILo", fmt(lo))
        cmd(f"Rolloff{key}CIHi", fmt(hi))
        cmd(f"Rolloff{key}SE", fmt(se, 2))
    lines.append("")
    for piece, (pt, lo, hi, se, _, lag, r_lag, r0) in paired.items():
        cmd(f"RolloffDelta{piece}Pt", fmt(pt))
        cmd(f"RolloffDelta{piece}CILo", fmt(lo))
        cmd(f"RolloffDelta{piece}CIHi", fmt(hi))
        cmd(f"RolloffDelta{piece}SE", fmt(se, 2))
        cmd(f"PairLag{piece}", f"{lag:+d}")
        cmd(f"PairLagAbs{piece}", f"{abs(lag)}")
        cmd(f"PairCorr{piece}", fmt(r_lag, 2))
        cmd(f"PairCorrZero{piece}", fmt(r0, 2))
    lines.append("")
    for key in caches:
        for comp in ("X", "Y", "Z"):
            pt, lo, hi = single[key]["dir"][f"{comp}_over_W"]
            cmd(f"Dir{comp}{key}Pt", fmt(pt, 2))
            cmd(f"Dir{comp}{key}CILo", fmt(lo, 2))
            cmd(f"Dir{comp}{key}CIHi", fmt(hi, 2))
    if sweep_widths:
        lines.append("")
        lines.append("% Block-length sensitivity: 95% CI widths (dB) for --block-sweep "
                     + ",".join(str(b) for b in args.block_sweep) + " s.")
        for name, width in sweep_widths:
            cmd(name, fmt(width, 2))
    (args.out / "revision_stats_variables.tex").write_text("\n".join(lines) + "\n")

    print(f"\n[OK] Wrote {args.out}/")
    for p in sorted(args.out.iterdir()):
        print(f"     {p.name}")


if __name__ == "__main__":
    main()
