#!/usr/bin/env python3
"""
Render the Fig. 4 geographic maps on their own, without running the rest of the
audio-driven pipeline.

Reads plots/pub_fig04_geographic_map.csv by default, so it works from a clean
checkout. Pass --from-metadata to rebuild from data/metadata/<session>.yaml
instead; that directory is not part of this repository (the deposit ships one
metadata.yaml per session under sessions/<id>/).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from generate_all_figures import (OUTPUT_DIR, load_locations_from_csv,
                                  plot_geographic_map)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-metadata", action="store_true",
                        help="rebuild from data/metadata/*.yaml instead of the CSV")
    parser.add_argument("--output-dir", default=None,
                        help="where to write the PNGs (default: figures/)")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    out = Path(args.output_dir) if args.output_dir else repo_root / "figures"

    if args.from_metadata:
        plot_geographic_map(output_dir=out)
    else:
        csv_path = OUTPUT_DIR / "pub_fig04_geographic_map.csv"
        plot_geographic_map(locations=load_locations_from_csv(csv_path),
                            output_dir=out)


if __name__ == "__main__":
    main()
