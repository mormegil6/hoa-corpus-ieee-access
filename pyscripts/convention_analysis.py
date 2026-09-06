#!/usr/bin/env python3
"""Per-order levels of the committed frame caches under two channel-combining
conventions - the linear mean of per-channel RMS used in the paper, and the
per-order energy sum - against the ideal SN3D diffuse-field profile.

Usage:
    python convention_analysis.py                 # writes revision_results/reencode/
    python convention_analysis.py --out /other/dir

Reads revision_results/cache/frames_<key>.npz (no audio needed); writes into --out
convention_table.csv (one row per cache: per-order levels under both conventions,
absolute and relative to W, the 0-3 and 0-5 rolloffs, the published rolloff and
the excess over the ideal diffuse-field profile) and convention_results.json (the
same values plus the paired ZM-1 minus Spcmic 3OA rolloff differences and the
ideal SN3D diffuse-field profile under both conventions).
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np

REPO_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_DIR / "revision_results" / "cache"
DEFAULT_OUT = REPO_DIR / "revision_results" / "reencode"
ORDER_RANGES = {0: (0, 1), 1: (1, 4), 2: (4, 9), 3: (9, 16), 4: (16, 25), 5: (25, 36)}
KEYS = ["ZMOneFranck", "ZMOneProkofiev", "SpcmicThreeOAFranck", "SpcmicThreeOAProkofiev",
        "SpcmicFiveOAFranck", "SpcmicFiveOAProkofiev", "SRVRMICFranck", "SRVRMICProkofiev"]
PUB = {"ZMOneFranck": 27.396, "ZMOneProkofiev": 26.003, "SpcmicThreeOAFranck": 8.438,
       "SpcmicThreeOAProkofiev": 8.480, "SpcmicFiveOAFranck": 15.102, "SpcmicFiveOAProkofiev": 15.487}
PUB_ORD = {"ZMOneFranck": [-23.216, -31.783, -42.925, -50.612],
           "SpcmicFiveOAFranck": [-26.202, -30.753, -37.949, -41.304, -44.383, -47.052]}
IDEAL = [10 * np.log10(1 / (2 * n + 1)) for n in range(6)]


def analyse():
    res = {}
    for k in KEYS:
        z = np.load(CACHE_DIR / f"frames_{k}.npz")
        E, C = z["energy"], z["counts"]
        rms = np.sqrt(E.sum(0) / C.sum())
        nch = len(rms)
        maxo = {1: 0, 4: 1, 9: 2, 16: 3, 25: 4, 36: 5}[nch]
        mean_dbfs = [20 * np.log10(np.mean(rms[s:e])) for o, (s, e) in ORDER_RANGES.items() if e <= nch]
        sum_dbfs = [10 * np.log10(np.sum(rms[s:e] ** 2)) for o, (s, e) in ORDER_RANGES.items() if e <= nch]
        mean_rel = [v - mean_dbfs[0] for v in mean_dbfs]
        sum_rel = [v - sum_dbfs[0] for v in sum_dbfs]
        r = dict(key=k, nch=nch, max_order=maxo, n_frames=len(C), n_samples=int(C.sum()),
                 mean_dbfs=mean_dbfs, sum_dbfs=sum_dbfs, mean_rel=mean_rel, sum_rel=sum_rel)
        if maxo >= 3:
            r["roll03_mean"] = mean_dbfs[0] - mean_dbfs[3]
            r["roll03_sum"] = sum_dbfs[0] - sum_dbfs[3]
            r["excess"] = r["roll03_mean"] - 8.45
            r["excess_exact"] = r["roll03_mean"] + IDEAL[3]
        if maxo >= 5:
            r["roll05_mean"] = mean_dbfs[0] - mean_dbfs[5]
            r["roll05_sum"] = sum_dbfs[0] - sum_dbfs[5]
        res[k] = r
        print(k, "nch", nch, "frames", len(C), "samples", int(C.sum()))
        print("  mean dBFS:", [round(v, 3) for v in mean_dbfs])
        print("  sum  dBFS:", [round(v, 3) for v in sum_dbfs])
        print("  mean rel W:", [round(v, 3) for v in mean_rel])
        print("  sum  rel W:", [round(v, 3) for v in sum_rel])
        if maxo >= 3:
            print(f"  roll03 mean={r['roll03_mean']:.3f} sum={r['roll03_sum']:.3f} published={PUB[k]} "
                  f"diff={r['roll03_mean'] - PUB[k]:+.4f} excess={r['excess']:.3f}")
        if maxo >= 5:
            print(f"  roll05 mean={r['roll05_mean']:.3f} sum={r['roll05_sum']:.3f}")
        if k in PUB_ORD:
            print("  published order dBFS diff:", [round(a - b, 4) for a, b in zip(mean_dbfs, PUB_ORD[k])])
    print("\nIDEAL mean-convention diffuse:", [round(v, 3) for v in IDEAL])
    for piece in ("Franck", "Prokofiev"):
        z, s = res["ZMOne" + piece], res["SpcmicThreeOA" + piece]
        print(f"paired ZM1-Spcmic3OA {piece}: mean {z['roll03_mean'] - s['roll03_mean']:.3f}  "
              f"sum {z['roll03_sum'] - s['roll03_sum']:.3f}")
    return res


def write_table(res, path):
    def pad(l):
        return [f"{v:.4f}" for v in l] + [""] * (6 - len(l))

    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key", "n_channels", "max_order", "n_frames", "n_samples"] +
                   [f"mean_o{o}_dBFS" for o in range(6)] + [f"sum_o{o}_dBFS" for o in range(6)] +
                   [f"mean_o{o}_relW_dB" for o in range(6)] + [f"sum_o{o}_relW_dB" for o in range(6)] +
                   ["rolloff_0_3_mean_dB", "rolloff_0_3_sum_dB", "rolloff_0_5_mean_dB", "rolloff_0_5_sum_dB",
                    "published_rolloff_0_3_dB", "excess_vs_ideal_diffuse_dB", "ideal_diffuse_mean_o3_dB"])
        for k in KEYS:
            r = res[k]
            w.writerow([k, r["nch"], r["max_order"], r["n_frames"], r["n_samples"]] + pad(r["mean_dbfs"]) + pad(r["sum_dbfs"])
                       + pad(r["mean_rel"]) + pad(r["sum_rel"]) +
                       [f"{r['roll03_mean']:.4f}" if "roll03_mean" in r else "", f"{r['roll03_sum']:.4f}" if "roll03_sum" in r else "",
                        f"{r['roll05_mean']:.4f}" if "roll05_mean" in r else "", f"{r['roll05_sum']:.4f}" if "roll05_sum" in r else "",
                        PUB.get(k, ""), f"{r['excess']:.4f}" if "excess" in r else "", f"{IDEAL[3]:.4f}"])


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT,
                    help="directory for convention_table.csv and convention_results.json "
                         "(default %(default)s)")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    res = analyse()
    write_table(res, args.out / "convention_table.csv")
    res["_paired_difference_rolloff_0_3_dB"] = {
        conv: {p: res["ZMOne" + p]["roll03_" + conv] - res["SpcmicThreeOA" + p]["roll03_" + conv]
               for p in ("Franck", "Prokofiev")}
        for conv in ("mean", "sum")}
    res["_ideal_diffuse_SN3D_relW_dB"] = {"mean_convention": IDEAL, "sum_convention": [0.0] * 6}
    with open(args.out / "convention_results.json", "w") as f:
        json.dump(res, f, indent=1, default=float)
        f.write("\n")


if __name__ == "__main__":
    main()
