#!/usr/bin/env python3
"""Scan a deposit checkout and write corpus_scan.csv for build_dataset_card.py.

Walks sessions/*/audio/*.wav and sessions/*/audio_a_format/*.wav under the deposit
root and writes one row per file: path (relative to the deposit root), session,
filename, bytes, sha256, frames, channels, duration_s. Frames and channels come
from the file header (soundfile), the hash from the file bytes, so the whole
deposit is read once.

    export HOA_CORPUS_DIR="/path/to/deposit"      # or pass --corpus-dir
    python3 pyscripts/scan_deposit.py corpus_scan.csv
"""
import argparse
import csv
import hashlib
import os
import sys
from pathlib import Path

import soundfile as sf

COLUMNS = ["path", "session", "filename", "bytes", "sha256", "frames", "channels", "duration_s"]


def sha256_of(path, chunk=1 << 24):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def scan(root):
    files = sorted(p for sub in ("audio", "audio_a_format")
                   for p in root.glob(f"sessions/*/{sub}/*.wav"))
    for p in files:
        info = sf.info(str(p))
        yield {
            "path": p.relative_to(root).as_posix(),
            "session": p.parents[1].name,
            "filename": p.name,
            "bytes": p.stat().st_size,
            "sha256": sha256_of(p),
            "frames": info.frames,
            "channels": info.channels,
            "duration_s": f"{info.frames / info.samplerate:.3f}",
        }


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("out", type=Path, help="CSV to write (corpus_scan.csv)")
    ap.add_argument("--corpus-dir", type=Path, default=os.environ.get("HOA_CORPUS_DIR"),
                    help="deposit root containing sessions/ (default: $HOA_CORPUS_DIR)")
    args = ap.parse_args()
    if args.corpus_dir is None or not (args.corpus_dir / "sessions").is_dir():
        sys.exit("set HOA_CORPUS_DIR or --corpus-dir to a deposit root holding sessions/ "
                 "(download from doi.org/10.34808/w8bx-2094)")
    n = 0
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for row in scan(args.corpus_dir):
            w.writerow(row)
            n += 1
            print(f"{row['sha256'][:12]}  {row['path']}")
    print(f"wrote {args.out}: {n} files")


if __name__ == "__main__":
    main()
