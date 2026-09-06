#!/usr/bin/env python3
"""Build the dataset-card tables from the corpus metadata and a file scan.

Writes dataset_card/splits.csv and dataset_card/SHA256SUMS.txt and validates
every metadata.yaml against dataset_card/metadata_schema.json (jsonschema is a
hard requirement, see requirements.txt).

    export HOA_CORPUS_DIR="/path/to/deposit"      # or pass --corpus-dir
    python3 pyscripts/build_dataset_card.py --scan corpus_scan.csv

The scan CSV needs one row per WAV file with the columns path (relative to
the deposit root), session, filename, bytes, sha256, frames, channels and
duration_s.
"""
import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import jsonschema
import yaml

REPO_DIR = Path(__file__).parent.parent
CARD_DIR = REPO_DIR / "dataset_card"

# Session-level assignment; every session not listed here is train.
# Rationale and the leakage rule are in dataset_card/SPLITS.md.
PARTITIONS = {
    "test": [
        "2024-08-15_aula-pg_solo-piano-mic-comparison",
        "2024-03-09_fiqu-miqu-studio_folk-band",
        "2022-03-25_sopot-pier_outdoor-ambient",
    ],
    "validation": [
        "2023-10-12_baltic-philharmonic_choir",
        "2024-12-10_aula-pg_solo-piano-chopin",
        "2023-12-07_aula-pg_chamber-ensemble",
        "2025-09-28_jedrzejewo-cave_vr-production-indoor",
    ],
}

MIC_LABELS = {
    "ZM1": "ZM-1",
    "ZM1b": "ZM-1",
    "Spcmic": "Spcmic",
    "NTSF1": "NT-SF1",
    "SRVRMIC": "SR-VRMIC",
}

SPLIT_COLUMNS = [
    "session_id", "partition", "venue", "content_type", "primary_mic", "mics",
    "duration_min", "programme_min", "files", "a_format_files",
]


def load_scan(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def load_metadata(corpus_dir, session_dir):
    with open(corpus_dir / "sessions" / session_dir / "metadata.yaml") as f:
        return yaml.safe_load(f)


def partition_of(session_dir):
    for name, sessions in PARTITIONS.items():
        if session_dir in sessions:
            return name
    return "train"


def session_rows(scan):
    by_session = defaultdict(list)
    for row in scan:
        by_session[row["session"]].append(row)
    return by_session


def build_splits(scan, corpus_dir):
    rows = []
    for session_dir, files in sorted(session_rows(scan).items()):
        meta = load_metadata(corpus_dir, session_dir)
        renders = [r for r in files if not r["filename"].startswith("AFORMAT_")]
        mics = sorted({MIC_LABELS[r["filename"].split("_")[1]] for r in renders})
        rows.append({
            "session_id": session_dir,
            "partition": partition_of(session_dir),
            "venue": session_dir.split("_")[1],
            "content_type": meta["content"]["type"],
            "primary_mic": meta["equipment"]["primary_mic_model"],
            "mics": "+".join(mics),
            "duration_min": f"{sum(float(r['duration_s']) for r in renders) / 60:.1f}",
            "_duration_min_exact": sum(float(r["duration_s"]) for r in renders) / 60,
            "programme_min": meta["duration_minutes"],
            "files": len(renders),
            "a_format_files": len(files) - len(renders),
        })
    return rows


def write_splits(rows, path):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SPLIT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_checksums(scan, path):
    n_aformat = sum(1 for r in scan if r["filename"].startswith("AFORMAT_"))
    header = [
        f"# SHA-256 of every audio file in deposit v1.2 ({len(scan)} files: {len(scan) - n_aformat} B-format",
        f"# renders + {n_aformat} A-format masters). Paths are relative to the deposit root;",
        "# verify from the deposit root with: shasum -a 256 -c dataset_card/SHA256SUMS.txt",
        "# The two AFORMAT_Spcmic_* hashes are those of the v1.2 RF64 files (tag 'RF64',",
        "# size field 0xFFFFFFFF, ds64 chunk) and differ from the v1.1 'RIFF'-tagged files.",
    ]
    with open(path, "w") as f:
        f.write("\n".join(header) + "\n")
        for row in sorted(scan, key=lambda r: r["path"]):
            f.write(f"{row['sha256']}  {row['path']}\n")


def print_summary(rows):
    totals = defaultdict(lambda: [0, 0, 0.0, 0.0])
    for row in rows:
        t = totals[row["partition"]]
        t[0] += 1
        t[1] += row["files"]
        t[2] += row["_duration_min_exact"]
        t[3] += float(row["programme_min"])
    grand = sum(t[2] for t in totals.values())
    grand_prog = sum(t[3] for t in totals.values())
    for name in ("train", "validation", "test"):
        n, files, minutes, prog = totals[name]
        print(f"{name:11s} {n:2d} sessions {files:2d} files "
              f"{minutes:6.1f} min ({100 * minutes / grand:4.1f}%) "
              f"programme {prog:6.1f} min ({100 * prog / grand_prog:4.1f}%)")


def validate_metadata(corpus_dir, session_dirs):
    with open(CARD_DIR / "metadata_schema.json") as f:
        validator = jsonschema.Draft202012Validator(json.load(f))
    ok = True
    for session_dir in session_dirs:
        errors = sorted(validator.iter_errors(load_metadata(corpus_dir, session_dir)),
                        key=lambda e: list(e.path))
        for err in errors:
            ok = False
            print(f"{session_dir}: {'/'.join(map(str, err.path))}: {err.message}")
    print(f"metadata validation: {'OK' if ok else 'FAILED'} ({len(session_dirs)} files)")
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--scan", required=True, help="scan CSV with sha256 per file")
    parser.add_argument("--corpus-dir", type=Path, default=os.environ.get("HOA_CORPUS_DIR"),
                        help="deposit root containing sessions/ (default: $HOA_CORPUS_DIR)")
    parser.add_argument("--out-dir", default=CARD_DIR, type=Path)
    args = parser.parse_args()
    if args.corpus_dir is None:
        sys.exit("set HOA_CORPUS_DIR or pass --corpus-dir (the deposit root holding sessions/)")

    scan = load_scan(args.scan)
    rows = build_splits(scan, args.corpus_dir)
    write_splits(rows, args.out_dir / "splits.csv")
    write_checksums(scan, args.out_dir / "SHA256SUMS.txt")
    print_summary(rows)
    if not validate_metadata(args.corpus_dir, [row["session_id"] for row in rows]):
        sys.exit(1)


if __name__ == "__main__":
    main()
