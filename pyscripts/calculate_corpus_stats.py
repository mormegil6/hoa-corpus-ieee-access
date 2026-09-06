#!/usr/bin/env python3
"""Corpus size, duration and content-type counts from data/render_stats_all.csv.

Durations and file counts per Ambisonics order come from the CSV alone. With
HOA_CORPUS_DIR set to the deposit root, file sizes are read from
sessions/<session>/audio/<file> and the content-type table from each session's
metadata.yaml (content.type); without it, sizes are reported as unavailable and
the content-type table is skipped.
"""
import argparse
import csv
import os
import sys
from pathlib import Path

import yaml

DATA_DIR = Path(__file__).parent.parent / "data"
CORPUS_DIR = Path(os.environ["HOA_CORPUS_DIR"]) if os.environ.get("HOA_CORPUS_DIR") else None

# grouping of the manuscript's "Corpus Composition by Content Type" table
GROUPS = {
    "Solo piano": ["solo_piano", "piano_duet"],
    "Choir": ["choir", "choir_with_ensemble", "choir_with_orchestra", "choir_with_soloists", "orchestra"],
    "Chamber music": ["chamber", "ensemble"],
    "VR film production": ["vr_film_production"],
    "Outdoor/Ambient": ["ambient"],
}


def fmt_dur(s):
    return f"{int(s // 3600)}h {int((s % 3600) // 60)}min"


def main():
    rows = list(csv.DictReader(open(DATA_DIR / "render_stats_all.csv")))
    if CORPUS_DIR is not None and not CORPUS_DIR.is_dir():
        sys.exit(f"HOA_CORPUS_DIR does not exist: {CORPUS_DIR}")

    per_order = {}
    missing = []
    for row in rows:
        order = row["filename"][:3]
        d = per_order.setdefault(order, dict(files=0, seconds=0.0, bytes=0))
        d["files"] += 1
        d["seconds"] += float(row["duration_seconds"])
        if CORPUS_DIR is not None:
            wav = CORPUS_DIR / "sessions" / row["session"] / "audio" / row["filename"]
            if wav.exists():
                d["bytes"] += wav.stat().st_size
            else:
                missing.append(wav)

    print("=" * 60)
    print("CORPUS STATISTICS FROM render_stats_all.csv")
    if CORPUS_DIR is None:
        print("(file sizes not read: HOA_CORPUS_DIR is not set)")
    elif missing:
        print(f"(file sizes incomplete: {len(missing)} of {len(rows)} files not found under {CORPUS_DIR})")
    else:
        print(f"(file sizes read from {CORPUS_DIR})")
    print("=" * 60)
    for order in sorted(per_order):
        d = per_order[order]
        size = f"{d['bytes'] / 1e9:.1f} GB" if CORPUS_DIR is not None and not missing else "size n/a"
        print(f"{order}: {d['files']} files, {fmt_dur(d['seconds'])}, {size}")
    total_files = sum(d["files"] for d in per_order.values())
    total_sec = sum(d["seconds"] for d in per_order.values())
    total_bytes = sum(d["bytes"] for d in per_order.values())
    size = f"{total_bytes / 1e9:.1f} GB" if CORPUS_DIR is not None and not missing else "size n/a"
    print(f"\nTOTAL: {total_files} files, {fmt_dur(total_sec)} ({total_sec / 60:.1f} min), {size}")

    if CORPUS_DIR is None:
        print("\nContent-type table skipped: HOA_CORPUS_DIR is not set")
        return
    session_ct = {}
    for yaml_file in sorted((CORPUS_DIR / "sessions").glob("*/metadata.yaml")):
        with open(yaml_file) as f:
            meta = yaml.safe_load(f) or {}
        session_ct[yaml_file.parent.name] = (meta.get("content") or {}).get("type", "unknown")
    ct_files, ct_sessions = {}, {}
    for row in rows:
        ct = session_ct.get(row["session"], "unknown")
        ct_files[ct] = ct_files.get(ct, 0) + 1
        ct_sessions.setdefault(ct, set()).add(row["session"])
    print("\nCorpus composition by content type (manuscript table grouping):")
    print("-" * 50)
    grand_files = grand_sessions = 0
    for group, cts in GROUPS.items():
        files = sum(ct_files.get(ct, 0) for ct in cts)
        sessions = set().union(*(ct_sessions.get(ct, set()) for ct in cts))
        print(f"{group}: {len(sessions)} sessions, {files} files")
        grand_files += files
        grand_sessions += len(sessions)
    ungrouped = sorted(ct for ct in ct_files if not any(ct in cts for cts in GROUPS.values()))
    if ungrouped:
        print(f"(content types not in any group: {ungrouped})")
    print("-" * 50)
    print(f"TOTAL: {grand_sessions} sessions, {grand_files} files")


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    main()
