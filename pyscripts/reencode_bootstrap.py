#!/usr/bin/env python3
"""
reencode_bootstrap.py - block-bootstrap CIs for the re-encoded ZM-1 rolloffs.

Reuses the sibling revision_stats.py unchanged: order_levels_from_selection,
block_bootstrap_indices, pct_ci and the constants FRAME_SECONDS / BLOCK_SECONDS /
N_BOOT / SEED / CI_LO / CI_HI.

Single-array: for every (config, piece) the 0->3 rolloff point estimate uses all
frames (trailing partial included), the bootstrap uses only full-length frames,
exactly as the per-file loop of revision_stats.bootstrap_all(). One np.random.default_rng(SEED)
is created per file (revision_stats shares one generator across its file loop, so
only its first file, ZMOneFranck, is reproduced bit-for-bit; that row is asserted).
So that each quantity has one committed interval, the factory ZM-1 and Spcmic 3OA
rows (single and paired) are copied from revision_results/rolloff_bootstrap.csv and
marked ci_source=rolloff_bootstrap.csv; rows computed here carry ci_source=this script.

Paired: ZM-1 config minus Spcmic 3OA (corpus render). The integer frame offset is
found by Pearson cross-correlation of the per-frame W-channel log mean-square
sequences over lags -10..+10; offset k means ZM-1 frame i pairs with Spcmic frame
i + k. The paired bootstrap then resamples the SAME index into both aligned
full-frame index vectors, as revision_stats does for its PAIRS.

Usage:
    python reencode_bootstrap.py                 # revision_results/reencode/
    python reencode_bootstrap.py --out /other/dir

--out must hold cache/frames_ZMOne_<config>_<piece>.npz as written by
reencode_zm1.py; the Spcmic reference caches and the committed rolloff table
come from revision_results/. Writes <out>/reencode_bootstrap.csv.
"""
import argparse
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import revision_stats as rs  # noqa: E402

REPO_DIR = Path(__file__).resolve().parent.parent
CORPUS_CACHE = REPO_DIR / "revision_results" / "cache"
DEFAULT_OUT = REPO_DIR / "revision_results" / "reencode"
CONFIGS = ["factory", "tikhonov", "tikhonov_ordlim", "softlimit_20",
           "softlimit_30", "softlimit_40", "mmse_20"]
PIECES = ["Franck", "Prokofiev"]
LAGS = range(-10, 11)
PEAK_MIN = 0.9
BLOCK_LEN = int(round(rs.BLOCK_SECONDS / rs.FRAME_SECONDS))


def load(path):
    z = np.load(path)
    return z["energy"], z["counts"], int(z["sr"])


def n_full(counts):
    return int(np.sum(counts == counts.max()))


def single_array(energy, counts):
    """Mirror of the revision_stats.bootstrap_all() per-file loop, rolloff part only."""
    rng = np.random.default_rng(rs.SEED)
    nf = n_full(counts)
    all_idx = np.arange(len(counts))
    full_idx = np.arange(nf)
    pt = rs.order_levels_from_selection(energy, counts, all_idx, 3)
    boot = []
    for idx in rs.block_bootstrap_indices(rng, nf, BLOCK_LEN, rs.N_BOOT):
        o = rs.order_levels_from_selection(energy, counts, full_idx[idx], 3)
        boot.append(o[0] - o[3])
    lo, hi = rs.pct_ci(boot)
    return pt, pt[0] - pt[3], lo, hi, float(np.std(boot, ddof=1)), nf


def w_logms(energy, counts):
    return 10.0 * np.log10(energy[:, 0] / counts + 1e-30)


def xcorr_lag(ez, cz, es, cs):
    """Pearson correlation of W log-mean-square sequences (full frames only) for each lag."""
    wz = w_logms(ez, cz)[: n_full(cz)]
    ws = w_logms(es, cs)[: n_full(cs)]
    out = {}
    for k in LAGS:
        i = np.arange(len(wz))
        j = i + k
        m = (j >= 0) & (j < len(ws))
        a, b = wz[i[m]], ws[j[m]]
        out[k] = (float(np.corrcoef(a, b)[0, 1]), int(m.sum()))
    ranked = sorted(out.items(), key=lambda kv: kv[1][0], reverse=True)
    return out, ranked


def paired(ez, cz, es, cs, k):
    """revision_stats paired bootstrap on offset-aligned full-frame index vectors."""
    i = np.arange(n_full(cz))
    j = i + k
    m = (j >= 0) & (j < n_full(cs))
    zi, si = i[m], j[m]
    n = len(zi)
    oz = rs.order_levels_from_selection(ez, cz, zi, 3)
    os_ = rs.order_levels_from_selection(es, cs, si, 3)
    pt_aligned = (oz[0] - oz[3]) - (os_[0] - os_[3])
    rng = np.random.default_rng(rs.SEED)
    boots = []
    for idx in rs.block_bootstrap_indices(rng, n, BLOCK_LEN, rs.N_BOOT):
        bz = rs.order_levels_from_selection(ez, cz, zi[idx], 3)
        bs = rs.order_levels_from_selection(es, cs, si[idx], 3)
        boots.append((bz[0] - bz[3]) - (bs[0] - bs[3]))
    lo, hi = rs.pct_ci(boots)
    return pt_aligned, lo, hi, float(np.std(boots, ddof=1)), n, oz, os_


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT,
                    help="re-encoding results directory with cache/ (default %(default)s)")
    args = ap.parse_args()
    re_cache = args.out / "cache"
    out_csv = args.out / "reencode_bootstrap.csv"

    rows = []
    spc = {p: load(CORPUS_CACHE / f"frames_SpcmicThreeOA{p}.npz") for p in PIECES}
    spc_single = {p: single_array(spc[p][0], spc[p][1]) for p in PIECES}
    for p in PIECES:
        pt, roll, lo, hi, se, nf = spc_single[p]
        rows.append(dict(kind="single", piece=p, config="Spcmic3OA_corpus",
                         n_frames=len(spc[p][1]), n_full_frames=nf,
                         order0_dBFS=f"{pt[0]:.3f}", order1_dBFS=f"{pt[1]:.3f}",
                         order2_dBFS=f"{pt[2]:.3f}", order3_dBFS=f"{pt[3]:.3f}",
                         rolloff_0_3_dB=f"{roll:.3f}", ci_lo=f"{lo:.3f}", ci_hi=f"{hi:.3f}",
                         bootstrap_se=f"{se:.3f}", block_s=rs.BLOCK_SECONDS,
                         replicates=rs.N_BOOT, seed=rs.SEED))
        print(f"[single] Spcmic3OA {p}: rolloff {roll:.3f} [{lo:.3f}, {hi:.3f}] se {se:.3f} n_full {nf}")

    single = {}
    for p in PIECES:
        for cfg in CONFIGS:
            path = re_cache / f"frames_ZMOne_{cfg}_{p}.npz"
            e, c, sr = load(path)
            pt, roll, lo, hi, se, nf = single_array(e, c)
            single[(cfg, p)] = dict(pt=roll, lo=lo, hi=hi, se=se)
            rows.append(dict(kind="single", piece=p, config=cfg, n_frames=len(c), n_full_frames=nf,
                             order0_dBFS=f"{pt[0]:.3f}", order1_dBFS=f"{pt[1]:.3f}",
                             order2_dBFS=f"{pt[2]:.3f}", order3_dBFS=f"{pt[3]:.3f}",
                             rolloff_0_3_dB=f"{roll:.3f}", ci_lo=f"{lo:.3f}", ci_hi=f"{hi:.3f}",
                             bootstrap_se=f"{se:.3f}", block_s=rs.BLOCK_SECONDS,
                             replicates=rs.N_BOOT, seed=rs.SEED, cache=str(path.relative_to(args.out))))
            print(f"[single] {cfg:16s} {p}: rolloff {roll:.3f} [{lo:.3f}, {hi:.3f}] se {se:.3f} n_full {nf}")

    # reproduction check against the committed revision_results (first file of its loop
    # shares the fresh-seed generator state with ours)
    committed = {}
    with open(CORPUS_CACHE.parent / "rolloff_bootstrap.csv") as f:
        for r in csv.DictReader(f):
            committed[r["comparison"]] = r
    fr = single[("factory", "Franck")]
    ref = committed["rolloff_0_3_ZMOneFranck"]
    print(f"[check] factory Franck vs committed: pt {fr['pt']:.3f}/{ref['point_dB']} "
          f"lo {fr['lo']:.3f}/{ref['ci_lo']} hi {fr['hi']:.3f}/{ref['ci_hi']}")
    assert f"{fr['pt']:.3f}" == ref["point_dB"] and f"{fr['lo']:.3f}" == ref["ci_lo"] \
        and f"{fr['hi']:.3f}" == ref["ci_hi"], "factory Franck does not reproduce committed row"

    # diagnostics: lag tables of corpus factory render vs Spcmic, and factory vs re-encoded
    for p in PIECES:
        es, cs, _ = spc[p]
        ef, cf, _ = load(re_cache / f"frames_ZMOne_factory_{p}.npz")
        table, ranked = xcorr_lag(ef, cf, es, cs)
        print(f"[lagtable] factory vs Spcmic3OA {p}: " + " ".join(f"{k:+d}:{v[0]:.3f}" for k, v in table.items()))
        print(f"           lag 0 r = {table[0][0]:.4f}; best {ranked[0][0]:+d} r={ranked[0][1][0]:.4f}")
        et, ct, _ = load(re_cache / f"frames_ZMOne_tikhonov_{p}.npz")
        table, ranked = xcorr_lag(ef, cf, et, ct)
        print(f"[lagtable] factory vs re-encoded(tikhonov) {p}: " + " ".join(f"{k:+d}:{v[0]:.3f}" for k, v in table.items()))
        print(f"           best {ranked[0][0]:+d} r={ranked[0][1][0]:.4f}, next {ranked[1][0]:+d} r={ranked[1][1][0]:.4f}")
        table, ranked = xcorr_lag(et, ct, es, cs)
        print(f"[lagtable] re-encoded(tikhonov) vs Spcmic3OA {p}: " + " ".join(f"{k:+d}:{v[0]:.3f}" for k, v in table.items()))

    for p in PIECES:
        es, cs, _ = spc[p]
        for cfg in CONFIGS:
            ez, cz, _ = load(re_cache / f"frames_ZMOne_{cfg}_{p}.npz")
            table, ranked = xcorr_lag(ez, cz, es, cs)
            (k, (peak, nov)), (k2, (second, _)) = ranked[0], ranked[1]
            unambiguous = peak > PEAK_MIN and (peak - second) > 0.05
            lagstr = ";".join(f"{kk}:{v[0]:.4f}" for kk, v in table.items())
            print(f"[xcorr] {cfg:16s} {p}: best lag {k:+d} r={peak:.4f} (n={nov}), "
                  f"next lag {k2:+d} r={second:.4f}, unambiguous={unambiguous}")
            row = dict(kind="paired_vs_Spcmic3OA", piece=p, config=cfg,
                       offset_frames=k, xcorr_peak=f"{peak:.4f}", xcorr_second_lag=k2,
                       xcorr_second=f"{second:.4f}", xcorr_table=lagstr,
                       unambiguous=unambiguous, block_s=rs.BLOCK_SECONDS,
                       replicates=rs.N_BOOT, seed=rs.SEED)
            if unambiguous:
                pt, lo, hi, se, n, oz, os_ = paired(ez, cz, es, cs, k)
                full_diff = single[(cfg, p)]["pt"] - spc_single[p][1]
                row.update(n_paired_frames=n, delta_pt_dB=f"{pt:.3f}", ci_lo=f"{lo:.3f}",
                           ci_hi=f"{hi:.3f}", bootstrap_se=f"{se:.3f}",
                           delta_fullrange_dB=f"{full_diff:.3f}",
                           zm1_rolloff_aligned_dB=f"{oz[0]-oz[3]:.3f}",
                           spcmic_rolloff_aligned_dB=f"{os_[0]-os_[3]:.3f}")
                print(f"         delta {pt:.3f} [{lo:.3f}, {hi:.3f}] se {se:.3f} n {n} "
                      f"(full-range diff {full_diff:.3f})")
            else:
                row.update(reason=f"xcorr peak {peak:.4f} at lag {k:+d} not unambiguous "
                                  f"(second {second:.4f} at {k2:+d}); no paired estimate")
                rows.append(row)
                # informational only: paired bootstrap at each of the two competing lags
                for kk in (k, k2):
                    pt, lo, hi, se, n, oz, os_ = paired(ez, cz, es, cs, kk)
                    rows.append(dict(kind="INFORMATIONAL_ambiguous_lag_do_not_cite", piece=p,
                                     config=cfg, offset_frames=kk,
                                     xcorr_peak=f"{table[kk][0]:.4f}", n_paired_frames=n,
                                     delta_pt_dB=f"{pt:.3f}", ci_lo=f"{lo:.3f}", ci_hi=f"{hi:.3f}",
                                     bootstrap_se=f"{se:.3f}",
                                     delta_fullrange_dB=f"{single[(cfg, p)]['pt'] - spc_single[p][1]:.3f}",
                                     block_s=rs.BLOCK_SECONDS, replicates=rs.N_BOOT, seed=rs.SEED))
                    print(f"         [informational lag {kk:+d}] delta {pt:.3f} [{lo:.3f}, {hi:.3f}] se {se:.3f} n {n}")
                continue
            rows.append(row)

    # one committed interval per quantity: the factory and Spcmic reference rows take the
    # intervals of revision_results/rolloff_bootstrap.csv (same design, shared generator
    # there versus a fresh one per file here; the point estimates are identical)
    for row in rows:
        src = None
        if row["kind"] == "single" and row["config"] == "factory":
            src = committed[f"rolloff_0_3_ZMOne{row['piece']}"]
        elif row["kind"] == "single" and row["config"] == "Spcmic3OA_corpus":
            src = committed[f"rolloff_0_3_SpcmicThreeOA{row['piece']}"]
        elif row["kind"] == "paired_vs_Spcmic3OA" and row["config"] == "factory":
            src = committed[f"ZM1_minus_Spcmic3OA_{row['piece']}"]
        if src is None:
            row["ci_source"] = "this script"
            continue
        row["ci_source"] = "rolloff_bootstrap.csv"
        if row["kind"] == "single":
            assert row["rolloff_0_3_dB"] == src["point_dB"], (row["config"], row["piece"])
            row.update(ci_lo=src["ci_lo"], ci_hi=src["ci_hi"], bootstrap_se=src["bootstrap_se"])
        else:
            assert int(src["pair_lag_frames"]) == row["offset_frames"], (row["piece"], row["offset_frames"])
            print(f"[paired] factory {row['piece']}: this script {row['delta_pt_dB']} "
                  f"[{row['ci_lo']}, {row['ci_hi']}] n {row['n_paired_frames']} -> "
                  f"rolloff_bootstrap.csv {src['point_dB']} [{src['ci_lo']}, {src['ci_hi']}] n {src['n_frames']}")
            row.update(delta_pt_dB=src["point_dB"], ci_lo=src["ci_lo"], ci_hi=src["ci_hi"],
                       bootstrap_se=src["bootstrap_se"], n_paired_frames=int(src["n_frames"]))

    keys = []
    for r in rows:
        for kk in r:
            if kk not in keys:
                keys.append(kk)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"[OK] wrote {out_csv}")


if __name__ == "__main__":
    main()
