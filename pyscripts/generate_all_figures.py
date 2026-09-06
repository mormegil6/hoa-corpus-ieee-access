#!/usr/bin/env python3
"""
Figure generation for the HOA corpus paper

Generates all figures with accompanying CSV files for data interpretation.

Figure numbering follows paper order (Fig 1-2 are placeholders):
- pub_fig04_geographic_map.png/.csv - Recording locations map (Fig 4 in paper)
- pub_fig05_timeline.png/.csv - Recording timeline (Fig 5 in paper)
- pub_fig06_lufs_corpus.png/.csv - LUFS for entire corpus (Fig 6 in paper)
- pub_fig08_lufs_mic_comparison.png/.csv - LUFS for mic comparison (Fig 8 in paper)
- pub_fig09_spatial_energy.png/.csv - Spatial energy distribution (Fig 9 in paper)
- pub_fig10_directional_distribution.png/.csv - Directional energy (Fig 10 in paper)
- fig_binaural_spectral_*.png/.csv - Binaural renders comparison (not in paper)

Usage:
    python generate_all_figures.py

Author: Bartłomiej Mróz
Date: 2026-01-26
"""

import argparse
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
import os
from pathlib import Path
from datetime import datetime
import csv
import yaml
import soundfile as sf
from scipy import signal
import warnings
warnings.filterwarnings('ignore')

# Try to import contextily for map background
try:
    import contextily as cx  # noqa: F401  (availability probe)
    HAS_CONTEXTILY = True
except ImportError:
    HAS_CONTEXTILY = False
    print("Note: Install contextily for map backgrounds: pip install contextily")

# Configuration
SCRIPT_DIR = Path(__file__).parent.parent
DATA_DIR = SCRIPT_DIR / "data"
METADATA_DIR = DATA_DIR / "metadata"
OUTPUT_DIR = SCRIPT_DIR / "plots"
OUTPUT_DIR.mkdir(exist_ok=True)

# Corpus and comparison session paths
# Audio location: HOA_CORPUS_DIR is the root of the deposit (the directory holding
# sessions/; download from doi.org/10.34808/w8bx-2094).
CORPUS_ROOT = Path(os.environ["HOA_CORPUS_DIR"]) if os.environ.get("HOA_CORPUS_DIR") else None
COMPARISON_SESSION = "2024-08-15_aula-pg_solo-piano-mic-comparison"
MIC_COMPARISON_SESSION = (CORPUS_ROOT / "sessions" / COMPARISON_SESSION / "audio"
                          if CORPUS_ROOT else None)


def comparison_dir():
    """The comparison session's audio folder; exits when HOA_CORPUS_DIR is not set."""
    if MIC_COMPARISON_SESSION is None or not MIC_COMPARISON_SESSION.is_dir():
        sys.exit(f"HOA_CORPUS_DIR is not set or holds no sessions/{COMPARISON_SESSION}/audio: "
                 "point it at the deposit root (download from doi.org/10.34808/w8bx-2094)")
    return MIC_COMPARISON_SESSION

# Microphone files - CORRECT ORDER: 1OA -> 3OA -> 3OA -> 5OA
MIC_ORDER = [
    ("SR-VRMIC (1OA)", "1OA_SRVRMIC_CFranck-PreludeChoralFugue.wav", "#d62728", 1),  # Red
    ("ZM-1 (3OA)", "3OA_ZM1_CFranck-PreludeChoralFugue.wav", "#1f77b4", 3),           # Blue
    ("Spcmic (3OA)", "3OA_Spcmic_CFranck-PreludeChoralFugue.wav", "#ff7f0e", 3),      # Orange
    ("Spcmic (5OA)", "5OA_Spcmic_CFranck-PreludeChoralFugue.wav", "#2ca02c", 5),      # Green
]

# Binaural files
BINAURAL_FILES = [
    ("SR-VRMIC (1OA)", "bin_1OA_SRVRMIC_CFranck-PreludeChoralFugue.wav"),
    ("ZM-1 (3OA)", "bin_3OA_ZM1_CFranck-PreludeChoralFugue.wav"),
    ("Spcmic (3OA)", "bin_3OA_Spcmic_CFranck-PreludeChoralFugue.wav"),
    ("Spcmic (5OA)", "bin_5OA_Spcmic_CFranck-PreludeChoralFugue.wav"),
]


def load_all_metadata():
    """Load all metadata YAML files, excluding will_not_publish sessions."""
    metadata = {}
    for yaml_file in METADATA_DIR.glob("*.yaml"):
        with open(yaml_file, 'r') as f:
            try:
                data = yaml.safe_load(f)
                if data:
                    pr = data.get('publication_readiness') or {}
                    if isinstance(pr, dict) and pr.get('status') == 'will_not_publish':
                        continue
                    metadata[yaml_file.stem] = data
            except Exception as e:
                print(f"  Warning: Error loading {yaml_file.name}: {e}")
    return metadata


def load_lufs_csv():
    """Load LUFS data from CSV, excluding NOT-TO-PUBLISH entries."""
    csv_path = DATA_DIR / "render_stats_all.csv"
    if not csv_path.exists():
        return []

    lufs_data = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip NOT-TO-PUBLISH sessions and files
            if 'NOT-TO-PUBLISH' in row.get('session', '') or 'NOT-TO-PUBLISH' in row.get('filename', ''):
                continue
            try:
                lufs_data.append({
                    'session': row['session'],
                    'filename': row['filename'],
                    'lufs_i': float(row['lufs_i']),
                })
            except (ValueError, KeyError):
                pass
    return lufs_data


def save_csv(data, fieldnames, output_path):
    """Save data to CSV file."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"    CSV: {output_path}")


# =============================================================================
# FIGURE 8: LUFS Distribution - Microphone Comparison Only
# =============================================================================
def plot_lufs_mic_comparison():
    """LUFS comparison for the 2024-08-15 microphone comparison session only."""
    print("\n[Figure 8] LUFS - Microphone Comparison Session")

    lufs_data = load_lufs_csv()
    mic_session_data = [d for d in lufs_data if d['session'].startswith("2024-08-15")]

    if not mic_session_data:
        print("  No data for mic comparison session")
        return

    # Sort by microphone order (1OA, 3OA ZM1, 3OA Spcmic, 5OA)
    def sort_key(d):
        fname = d['filename']
        if fname.startswith('1OA_'): return (0, fname)
        if fname.startswith('3OA_ZM1'): return (1, fname)
        if fname.startswith('3OA_Spcmic'): return (2, fname)
        if fname.startswith('5OA_'): return (3, fname)
        return (9, fname)

    sorted_data = sorted(mic_session_data, key=sort_key)

    # Prepare plot data
    labels = []
    values = []
    colors = []
    for d in sorted_data:
        fname = d['filename']
        # Skip binaural files if present
        if fname.startswith('bin_'):
            continue

        # Create readable label
        if '1OA_SRVRMIC' in fname:
            label = fname.replace('1OA_SRVRMIC_', 'SR-VRMIC (1OA): ').replace('.wav', '')
            color = '#d62728'
        elif '3OA_ZM1' in fname:
            label = fname.replace('3OA_ZM1_', 'ZM-1 (3OA): ').replace('.wav', '')
            color = '#1f77b4'
        elif '3OA_Spcmic' in fname:
            label = fname.replace('3OA_Spcmic_', 'Spcmic (3OA): ').replace('.wav', '')
            color = '#ff7f0e'
        elif '5OA_Spcmic' in fname:
            label = fname.replace('5OA_Spcmic_', 'Spcmic (5OA): ').replace('.wav', '')
            color = '#2ca02c'
        else:
            label = fname.replace('.wav', '')
            color = '#7f7f7f'

        labels.append(label)
        values.append(d['lufs_i'])
        colors.append(color)

    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, values, color=colors, alpha=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel('LUFS-I (Integrated Loudness)', fontsize=11)
    # No title for publication (caption in paper)
    ax.axvline(-23, color='green', linestyle='--', alpha=0.7, label='EBU R128 (-23 LUFS)')
    ax.legend(loc='upper left')
    ax.grid(True, axis='x', alpha=0.3)

    # Add value labels
    for i, (val, bar) in enumerate(zip(values, bars)):
        ax.text(val + 0.3, i, f'{val:.1f}', va='center', fontsize=8)

    plt.tight_layout()
    output_png = OUTPUT_DIR / "pub_fig08_lufs_mic_comparison.png"
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"    PNG: {output_png}")

    # Save CSV
    csv_data = [{'label': l, 'lufs_i': v} for l, v in zip(labels, values)]
    save_csv(csv_data, ['label', 'lufs_i'], OUTPUT_DIR / "pub_fig08_lufs_mic_comparison.csv")


# =============================================================================
# FIGURE 6: LUFS Distribution - Entire Corpus (Histogram)
# =============================================================================
def plot_lufs_corpus():
    """LUFS distribution across entire corpus as histogram."""
    print("\n[Figure 6] LUFS - Entire Corpus (Histogram)")

    lufs_data = load_lufs_csv()
    if not lufs_data:
        print("  No LUFS data available")
        return


    # Extract LUFS values
    values = [d['lufs_i'] for d in lufs_data]

    # Plot histogram
    fig, ax = plt.subplots(figsize=(10, 6))

    # Determine bin edges (2 LUFS wide bins)
    min_val = np.floor(min(values) / 2) * 2
    max_val = np.ceil(max(values) / 2) * 2
    bins = np.arange(min_val, max_val + 2, 2)

    # Create histogram
    n, bins_out, patches = ax.hist(values, bins=bins, color='#1f77b4',
                                    edgecolor='white', alpha=0.8)

    ax.set_xlabel('LUFS-I (Integrated Loudness)', fontsize=12)
    ax.set_ylabel('Number of Files', fontsize=12)
    ax.grid(True, axis='y', alpha=0.3)

    # Add statistics annotation
    mean_val = np.mean(values)
    median_val = np.median(values)
    std_val = np.std(values)
    ax.axvline(mean_val, color='#d62728', linestyle='--', linewidth=2,
               label=f'Mean: {mean_val:.1f} LUFS')
    ax.axvline(median_val, color='#2ca02c', linestyle=':', linewidth=2,
               label=f'Median: {median_val:.1f} LUFS')
    ax.legend(loc='upper left', fontsize=10)

    plt.tight_layout()
    output_png = OUTPUT_DIR / "pub_fig06_lufs_corpus.png"
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"    PNG: {output_png}")

    # Save CSV with histogram data
    csv_data = [{'bin_center': (bins_out[i] + bins_out[i+1])/2,
                 'count': int(n[i]),
                 'bin_start': bins_out[i],
                 'bin_end': bins_out[i+1]}
                for i in range(len(n))]
    save_csv(csv_data, ['bin_center', 'count', 'bin_start', 'bin_end'],
             OUTPUT_DIR / "pub_fig06_lufs_corpus.csv")

    # Print summary
    print(f"    Range: {min(values):.1f} to {max(values):.1f} LUFS")
    print(f"    Mean: {mean_val:.1f} LUFS, Median: {median_val:.1f} LUFS")
    print(f"    Std: {std_val:.1f} LUFS, N={len(values)}")


# =============================================================================
# FIGURE 4: Geographic Map (with and without outliers)
# =============================================================================
def load_locations_from_csv(csv_path):
    """Read the Fig. 4 location table, the publishable stand-in for the session
    metadata YAMLs (which carry unpublished fields and are not distributed)."""
    locations = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            locations.append({
                'session': row['venue'],
                'venue': row['venue'],
                'city': row['city'],
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude']),
                'content_type': row['content_type'],
                'is_outdoor': str(row.get('is_outdoor', '')).strip().lower() == 'true',
            })
    return locations


def plot_geographic_map(locations=None, output_dir=None):
    """Geographic distribution of recording locations - using timeline-consistent markers."""
    print("\n[Figure 4] Geographic Map")

    output_dir = OUTPUT_DIR if output_dir is None else Path(output_dir)
    if locations is not None:
        return _render_geographic_map(locations, output_dir, write_csv=False)

    metadata = load_all_metadata()

    # Extract all session data with GPS
    locations = []
    for session_name, data in metadata.items():
        lat = data.get('gps_latitude')
        lon = data.get('gps_longitude')
        venue = data.get('venue_name', 'Unknown')
        city = data.get('city', 'Unknown')
        content_type = data.get('content_type', 'unknown')
        venue_type = data.get('venue_type', '')
        is_outdoor = 'outdoor' in str(venue_type).lower()

        if lat and lon and lat != 0 and lon != 0:
            locations.append({
                'session': session_name,
                'venue': venue,
                'city': city,
                'latitude': lat,
                'longitude': lon,
                'content_type': content_type,
                'is_outdoor': is_outdoor,
            })

    if not locations:
        print("  No GPS data available")
        return

    return _render_geographic_map(locations, output_dir, write_csv=True)


def _render_geographic_map(locations, output_dir, write_csv=True):
    # Content type styling - SAME as timeline for consistency
    type_styles = {
        'solo_piano': ('#1f77b4', 'o'),       # Blue circle
        'piano_duet': ('#1f77b4', 'o'),
        'choir': ('#2ca02c', 's'),            # Green square
        'choir_with_orchestra': ('#2ca02c', 's'),
        'choir_with_soloists': ('#2ca02c', 's'),
        'choir_with_ensemble': ('#2ca02c', 's'),
        'orchestra': ('#d62728', 'D'),        # Red diamond
        'ensemble': ('#d62728', 'D'),
        'chamber': ('#9467bd', '^'),          # Purple triangle up
        'ambient': ('#e377c2', '*'),          # Pink star
        'ambience': ('#e377c2', '*'),
        'vr_film_production': ('#17becf', 'v'),  # Cyan triangle down
        'unknown': ('#7f7f7f', 'x'),          # Gray X
    }

    # Venue name abbreviations (English, short) - must match EXACT names from metadata
    venue_abbrev = {
        'Aula Politechniki Gdańskiej (Main Aula of Gdańsk University of Technology)': 'Gdańsk Tech Aula',
        'Hol przed Aulą Politechniki Gdańskiej (Hall in front of Main Aula, Gdańsk University of Technology)': 'Gdańsk Tech Hall',
        'Front courtyard (dziedziniec) of Main Building, Gdańsk University of Technology': 'Gdańsk Tech Courtyard',
        'Akademia Muzyczna im. Stanisława Moniuszki w Gdańsku - Sala Koncertowa (aMuz Main Concert Hall)': 'Music Academy',
        'Archikatedra Oliwska (Oliwa Cathedral)': 'Oliwa Cathedral',
        'Kościół Świętej Trójcy (Holy Trinity Church)': 'Holy Trinity Church',
        'Polska Filharmonia Bałtycka (Polish Baltic Philharmonic)': 'Baltic Philharmonic',
        'Baltic Sea Pier': 'Sopot Pier',
        'Fiqu Miqu Studio': 'Fiqu Miqu Studio',
        'Kamieniołom Piechcin (Piechcin Quarry)': 'Piechcin Quarry',
        'Agrotourism barn - styrofoam cave film set': 'Jędrzejewo (artificial cave)',
    }

    def _plot_map(locations_subset, show_venue_labels=False, suffix=''):
        """Helper to plot map with timeline-consistent markers."""
        import contextily as cx
        from shapely.geometry import Point
        import geopandas as gpd
        from matplotlib.lines import Line2D


        # Create figure
        fig, ax = plt.subplots(figsize=(10, 10))

        # Create GeoDataFrame with all locations
        points = [Point(loc['longitude'], loc['latitude']) for loc in locations_subset]
        gdf = gpd.GeoDataFrame({
            'geometry': points,
            'venue': [loc['venue'] for loc in locations_subset],
            'city': [loc['city'] for loc in locations_subset],
            'content_type': [loc['content_type'] for loc in locations_subset],
            'is_outdoor': [loc['is_outdoor'] for loc in locations_subset],
        }, crs="EPSG:4326")

        # Convert to Web Mercator for contextily
        gdf_merc = gdf.to_crs(epsg=3857)

        # Get bounds and make square
        minx, miny, maxx, maxy = gdf_merc.total_bounds
        cx_m = (minx + maxx) / 2
        cy_m = (miny + maxy) / 2
        range_x = maxx - minx
        range_y = maxy - miny
        max_range_m = max(range_x, range_y)
        padding_m = max(5000, max_range_m * 0.5)
        half_m = (max_range_m + padding_m) / 2

        ax.set_xlim(cx_m - half_m, cx_m + half_m)
        ax.set_ylim(cy_m - half_m, cy_m + half_m)

        # Add basemap tiles
        try:
            cx.add_basemap(ax, source=cx.providers.CartoDB.Positron, zoom='auto')
        except Exception as e:
            print(f"    Warning: Could not load map tiles: {e}")
            ax.set_facecolor('#e8f4f8')

        # Plot each location with timeline-consistent markers
        for idx, row in gdf_merc.iterrows():
            x, y = row.geometry.x, row.geometry.y
            ctype = row['content_type']
            color, marker = type_styles.get(ctype, ('#7f7f7f', 'x'))

            # Main marker
            ax.scatter(x, y, s=150, c=color, marker=marker,
                       alpha=0.9, edgecolors='none', zorder=5)

            # Orange ring for outdoor
            if row['is_outdoor']:
                ax.scatter(x, y, s=400, facecolors='none',
                           edgecolors='#ff7f0e', linewidth=2.5, zorder=4)

        # Add labels - UNIQUE venues only, with leader lines
        if show_venue_labels:
            import random

            # Group by venue to avoid duplicate labels
            venue_coords = {}  # venue_short -> (x, y) - use first occurrence
            for idx, row in gdf_merc.iterrows():
                x, y = row.geometry.x, row.geometry.y
                venue = row['venue']
                venue_short = venue_abbrev.get(venue, venue)

                if venue_short not in venue_coords:
                    venue_coords[venue_short] = (x, y)

            # Calculate offset distance based on map extent
            label_offset = half_m * 0.15  # 15% of map half-size

            # Manual direction overrides for specific venues (angle in radians)
            # Angles: 0=right, π/2~1.57=up, π~3.14=left, -π/2~-1.57=down
            # Different directions for each map version
            if suffix == '_tricity':
                # Small tri-city map directions
                manual_directions = {
                    "Fiqu Miqu Studio": np.pi / 4,           # up-right
                    "Sopot Pier": np.pi / 4,                 # up-right
                    "Gdańsk Tech Aula": 85 * np.pi / 180,    # 85° counterclockwise (user: +80 deg up)
                    "Oliwa Cathedral": np.pi / 4,            # up-right
                    "Gdańsk Tech Hall": np.pi / 6,           # 30° counterclockwise
                    "Gdańsk Tech Courtyard": 2 * np.pi / 180,  # 2° counterclockwise (user: 2 deg ccw)
                    "Holy Trinity Church": -2 * np.pi / 3,   # 120° clockwise
                    "Baltic Philharmonic": 15 * np.pi / 180, # 15° counterclockwise
                    "Music Academy": -np.pi / 2,             # down
                }
            else:
                # Big map with all venues directions
                manual_directions = {
                    "Fiqu Miqu Studio": 3 * np.pi / 4,       # up-left
                    "Gdańsk Tech Aula": np.pi / 4,           # up-right
                    "Oliwa Cathedral": np.pi,                # 180°
                    "Gdańsk Tech Hall": 25 * np.pi / 180,    # 25° up
                    "Gdańsk Tech Courtyard": 3 * np.pi / 180,  # 3° up
                    "Holy Trinity Church": -2 * np.pi / 3,   # 120° clockwise
                    "Music Academy": -np.pi / 2,             # 90° clockwise (user: 90 deg cw)
                    "Baltic Philharmonic": -10 * np.pi / 180, # 10° down
                    "Sopot Pier": 60 * np.pi / 180,          # 60° up
                    "Piechcin Quarry": np.pi / 4,            # up-right
                    "Jędrzejewo (artificial cave)": -np.pi / 4,  # down-right
                }

            for i, (venue_short, (x, y)) in enumerate(venue_coords.items()):
                # Check if there's a manual direction for this venue
                if venue_short in manual_directions:
                    angle = manual_directions[venue_short]
                else:
                    # Use deterministic random based on venue name for reproducibility
                    rng = random.Random(hash(venue_short) % (2**31))
                    angle = rng.uniform(0, 2 * np.pi)

                dx = np.cos(angle)
                dy = np.sin(angle)

                # Apply offset
                offset_x = dx * label_offset
                offset_y = dy * label_offset

                label_x = x + offset_x
                label_y = y + offset_y

                # Determine text alignment based on offset direction
                ha = 'left' if offset_x > 0 else 'right' if offset_x < 0 else 'center'
                va = 'bottom' if offset_y > 0 else 'top' if offset_y < 0 else 'center'

                # Use annotate with arrow connecting label to point
                ax.annotate(venue_short, xy=(x, y), xytext=(label_x, label_y),
                            fontsize=8, ha=ha, va=va, fontweight='bold',
                            bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                                      alpha=0.9, edgecolor='gray', linewidth=0.5),
                            arrowprops=dict(arrowstyle='-', color='black', alpha=0.6, lw=0.8),
                            zorder=6)

        # Add legend for marker types
        legend_categories = [
            ('Piano', '#1f77b4', 'o'),
            ('Choir', '#2ca02c', 's'),
            ('Orchestra/Ensemble', '#d62728', 'D'),
            ('Chamber', '#9467bd', '^'),
            ('Ambient', '#e377c2', '*'),
            ('VR Production', '#17becf', 'v'),
        ]
        legend_handles = [Line2D([0], [0], marker=m, color='w', markerfacecolor=c,
                                 markersize=8, markeredgecolor='none', label=label)
                          for label, c, m in legend_categories]
        # Add outdoor indicator
        legend_handles.append(Line2D([0], [0], marker='o', color='w', markerfacecolor='none',
                                     markersize=10, markeredgecolor='#ff7f0e', markeredgewidth=2,
                                     label='Outdoor'))
        ax.legend(handles=legend_handles, loc='best', fontsize=8, framealpha=0.95)

        # Force equal aspect
        ax.set_aspect('equal')

        # Clean axes
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_xticks([])
        ax.set_yticks([])

        plt.tight_layout()
        return fig

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Version 1: All locations - with labels (city name for Piechcin since it's remote)
    fig = _plot_map(locations, show_venue_labels=True)
    output_png = output_dir / "pub_fig04_geographic_map.png"
    fig.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"    PNG: {output_png}")

    # Version 2: Tri-City area - with venue labels
    tricity_locs = [loc for loc in locations if loc['city'] in ['Gdańsk', 'Gdynia', 'Sopot']]
    if len(tricity_locs) > 0 and len(tricity_locs) < len(locations):
        fig = _plot_map(tricity_locs, show_venue_labels=True, suffix='_tricity')
        output_png_tricity = output_dir / "pub_fig04_geographic_map_tricity.png"
        fig.savefig(output_png_tricity, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f"    PNG: {output_png_tricity}")

    if write_csv:
        # is_outdoor is included so the CSV alone can drive a re-render
        csv_data = [{'venue': loc['venue'], 'city': loc['city'],
                     'latitude': loc['latitude'], 'longitude': loc['longitude'],
                     'content_type': loc['content_type'],
                     'is_outdoor': loc['is_outdoor']}
                    for loc in locations]
        save_csv(csv_data,
                 ['venue', 'city', 'latitude', 'longitude', 'content_type', 'is_outdoor'],
                 output_dir / "pub_fig04_geographic_map.csv")


# =============================================================================
# FIGURE 5: Timeline with Different Markers + Outdoor Indicator
# =============================================================================
def plot_timeline():
    """Recording timeline visualization with different markers per content type and outdoor indicator."""
    print("\n[Figure 5] Timeline")

    metadata = load_all_metadata()

    # Extract dates, content types, and venue types
    events = []
    for session_name, data in metadata.items():
        # Prefer 'recording_date' (singular) if it exists, otherwise use first of 'recording_dates'
        date_str = data.get('recording_date')
        if not date_str:
            recording_dates = data.get('recording_dates')
            if recording_dates and isinstance(recording_dates, list) and len(recording_dates) > 0:
                date_str = recording_dates[0]  # Use first date for timeline
        if not date_str:
            continue

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            continue

        content_type = data.get('content_type', 'unknown')
        venue = data.get('venue_name', 'Unknown')
        venue_type = data.get('venue_type', '')
        is_outdoor = 'outdoor' in str(venue_type).lower()

        events.append({
            'session': session_name,
            'date': date,
            'date_str': date_str,
            'content_type': content_type,
            'venue': venue,
            'venue_type': venue_type,
            'is_outdoor': is_outdoor,
        })

    if not events:
        print("  No date data available")
        return

    events = sorted(events, key=lambda x: x['date'])

    # Content type styling: (color, marker shape)
    # Map various content types to standard categories with DISTINCT colors
    type_styles = {
        # Piano - Blue
        'solo_piano': ('#1f77b4', 'o'),       # Blue circle
        'piano_duet': ('#1f77b4', 'o'),
        # Choir - Green
        'choir': ('#2ca02c', 's'),            # Green square
        'choir_with_orchestra': ('#2ca02c', 's'),
        'choir_with_soloists': ('#2ca02c', 's'),
        'choir_with_ensemble': ('#2ca02c', 's'),
        # Orchestra/Ensemble - Red
        'orchestra': ('#d62728', 'D'),        # Red diamond
        'ensemble': ('#d62728', 'D'),
        # Chamber - Purple
        'chamber': ('#9467bd', '^'),          # Purple triangle up
        # Ambient - Pink
        'ambient': ('#e377c2', '*'),          # Pink star
        'ambience': ('#e377c2', '*'),
        # VR Production - Cyan
        'vr_film_production': ('#17becf', 'v'),  # Cyan triangle down
        'unknown': ('#7f7f7f', 'x'),          # Gray X
    }

    # Plot
    fig, ax = plt.subplots(figsize=(14, 5))

    # Plot each event individually to handle outdoor ring
    for i, event in enumerate(events):
        ctype = event['content_type']
        color, marker = type_styles.get(ctype, ('#7f7f7f', 'x'))
        y_pos = (i % 3) * 0.25

        # Plot main marker
        ax.scatter(event['date'], y_pos, s=120, c=color, marker=marker,
                   alpha=0.85, edgecolors='none', zorder=3)

        # Add orange ring for outdoor recordings
        if event['is_outdoor']:
            ax.scatter(event['date'], y_pos, s=300, facecolors='none',
                       edgecolors='#ff7f0e', linewidth=2.5, zorder=2)

    # Format x-axis
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))

    ax.set_ylim(-0.15, 0.65)  # Reduced whitespace (~20% less) ## HERE
    ax.set_yticks([])
    ax.set_xlabel('Recording Date', fontsize=11)
    # No title for publication (caption in paper)
    ax.grid(True, axis='x', alpha=0.3, linestyle='--')

    # Legend with markers - show main categories only with distinct colors
    legend_categories = [
        ('Solo Piano', '#1f77b4', 'o'),
        ('Choir', '#2ca02c', 's'),
        ('Orchestra/Ensemble', '#d62728', 'D'),
        ('Chamber', '#9467bd', '^'),
        ('Ambient', '#e377c2', '*'),
        ('VR Production', '#17becf', 'v'),
    ]
    legend_handles = [Line2D([0], [0], marker=m, color='w', markerfacecolor=c,
                             markersize=10, markeredgecolor='none', label=label)
                      for label, c, m in legend_categories]
    # Add outdoor indicator to legend
    legend_handles.append(Line2D([0], [0], marker='o', color='w', markerfacecolor='white',
                                  markersize=12, markeredgecolor='#ff7f0e', markeredgewidth=2.5,
                                  label='Outdoor (ring)'))
    ax.legend(handles=legend_handles, loc='upper left', fontsize=9, ncol=2, framealpha=0.9)

    plt.tight_layout()
    output_png = OUTPUT_DIR / "pub_fig05_timeline.png"
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"    PNG: {output_png}")

    # Save CSV
    csv_data = [{'session': e['session'], 'date': e['date_str'],
                 'content_type': e['content_type'], 'venue': e['venue'],
                 'venue_type': e['venue_type'], 'is_outdoor': e['is_outdoor']}
                for e in events]
    save_csv(csv_data, ['session', 'date', 'content_type', 'venue', 'venue_type', 'is_outdoor'],
             OUTPUT_DIR / "pub_fig05_timeline.csv")


# =============================================================================
# FIGURE 9: SPATIAL ENERGY DISTRIBUTION - Absolute Energy per Order
# =============================================================================
def compute_spatial_energy_absolute(audio_path, max_order):
    """Compute absolute RMS energy per ambisonics order (not relative to W)."""
    data, sr = sf.read(audio_path)

    if data.ndim == 1:
        return {}

    n_channels = data.shape[1]

    # Channel ranges for each order (ACN ordering)
    order_ranges = {
        0: (0, 1),     # W only
        1: (1, 4),     # Y, Z, X
        2: (4, 9),     # 5 channels
        3: (9, 16),    # 7 channels
        4: (16, 25),   # 9 channels
        5: (25, 36),   # 11 channels
    }

    # Compute RMS energy per order (in dB, absolute)
    energies = {}

    for ord_num in range(max_order + 1):
        start, end = order_ranges[ord_num]
        if end <= n_channels:
            order_data = data[:, start:end]
            # Average RMS across channels in this order
            rms_per_channel = np.sqrt(np.mean(order_data ** 2, axis=0))
            avg_rms = np.mean(rms_per_channel)
            energies[ord_num] = 20 * np.log10(avg_rms + 1e-10)  # dBFS

    return energies


def plot_spatial_energy():
    """Spatial energy distribution: RMS level per Ambisonics order."""
    print("\n[Figure: Spatial Energy Distribution]")

    mic_data = []

    for mic_name, filename, color, max_order in MIC_ORDER:
        audio_path = comparison_dir() / filename
        if not audio_path.exists():
            print(f"    Warning: {filename} not found")
            continue

        print(f"    Analyzing: {mic_name}...")
        energies = compute_spatial_energy_absolute(audio_path, max_order)
        mic_data.append({
            'name': mic_name,
            'color': color,
            'max_order': max_order,
            'energies': energies,
        })

    if not mic_data:
        print("  No audio files found")
        return

    # Plot: Line plot showing energy per order for each microphone
    fig, ax = plt.subplots(figsize=(10, 6))

    markers = ['o', 's', '^', 'D']  # Different markers for each mic
    # All lines dashed with same style (differ by marker and color)

    for i, m in enumerate(mic_data):
        orders = sorted(m['energies'].keys())
        values = [m['energies'][o] for o in orders]

        ax.plot(orders, values, marker=markers[i], markersize=10, linewidth=2.5,
                linestyle='--', color=m['color'], label=m['name'], alpha=0.9)

    ax.set_xlabel('Ambisonics Order', fontsize=11)
    ax.set_ylabel('RMS Level (dB re. full scale)', fontsize=11)
    # No title for publication (caption in paper)
    ax.set_xticks(range(6))
    ax.set_xticklabels(['0th (W)\nOmni', '1st\nDipole', '2nd', '3rd', '4th', '5th'])
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle=':')
    ax.set_xlim(-0.3, 5.3)

    plt.tight_layout()
    output_png = OUTPUT_DIR / "pub_fig09_spatial_energy.png"
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"    PNG: {output_png}")

    # Save CSV
    csv_data = []
    for m in mic_data:
        row = {'microphone': m['name'], 'max_order': m['max_order']}
        for ord_num in range(6):
            row[f'order_{ord_num}_dBFS'] = m['energies'].get(ord_num, '')
        csv_data.append(row)

    fieldnames = ['microphone', 'max_order'] + [f'order_{i}_dBFS' for i in range(6)]
    save_csv(csv_data, fieldnames, OUTPUT_DIR / "pub_fig09_spatial_energy.csv")


# =============================================================================
# FIGURE 10: DIRECTIONAL DISTRIBUTION - Intensity Vector Analysis
# =============================================================================
def compute_directional_intensity(audio_path):
    """Compute average intensity vector direction from 1st order channels."""
    data, sr = sf.read(audio_path)

    if data.ndim == 1 or data.shape[1] < 4:
        return None

    # Extract first-order channels: W(0), Y(1), Z(2), X(3) - ACN ordering
    w = data[:, 0]  # Omnidirectional (pressure)
    y = data[:, 1]  # Left-Right
    z = data[:, 2]  # Up-Down
    x = data[:, 3]  # Front-Back

    # Compute instantaneous intensity vectors (W * X, W * Y, W * Z)
    # Then average to get dominant direction
    ix = np.mean(w * x)  # Front-back intensity
    iy = np.mean(w * y)  # Left-right intensity
    iz = np.mean(w * z)  # Up-down intensity

    # Compute magnitude
    i_mag = np.sqrt(ix**2 + iy**2 + iz**2)

    # Compute RMS values for energy distribution
    w_rms = np.sqrt(np.mean(w ** 2))
    x_rms = np.sqrt(np.mean(x ** 2))
    y_rms = np.sqrt(np.mean(y ** 2))
    z_rms = np.sqrt(np.mean(z ** 2))

    # Direction in horizontal plane (azimuth)
    azimuth = np.arctan2(iy, ix)  # Radians, 0 = front

    return {
        'W_rms': w_rms, 'X_rms': x_rms, 'Y_rms': y_rms, 'Z_rms': z_rms,
        'Ix': ix, 'Iy': iy, 'Iz': iz, 'I_mag': i_mag,
        'azimuth_rad': azimuth, 'azimuth_deg': np.degrees(azimuth)
    }


def plot_directional_distribution():
    """Spatial intensity analysis - bar chart of channel energies and azimuth indicator."""
    print("\n[Figure: Directional Distribution]")

    mic_data = []

    for mic_name, filename, color, max_order in MIC_ORDER:
        audio_path = comparison_dir() / filename
        if not audio_path.exists():
            continue

        print(f"    Analyzing: {mic_name}...")
        result = compute_directional_intensity(audio_path)
        if result:
            mic_data.append({
                'name': mic_name,
                'color': color,
                'data': result,
            })

    if not mic_data:
        print("  No audio files found")
        return

    # Create figure: Bar chart of channel RMS + azimuth info
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Left: Bar chart of normalized channel energies
    x = np.arange(len(mic_data))
    width = 0.2
    channels = ['W', 'X', 'Y', 'Z']
    channel_colors = ['#1f77b4', '#d62728', '#2ca02c', '#ff7f0e']

    for i, ch in enumerate(channels):
        values = []
        for m in mic_data:
            w_rms = m['data']['W_rms']
            ch_rms = m['data'][f'{ch}_rms']
            # Normalize to W (except W itself shows absolute)
            if ch == 'W':
                values.append(20 * np.log10(ch_rms + 1e-10))  # dBFS
            else:
                values.append(ch_rms / w_rms if w_rms > 0 else 0)  # Ratio

        if ch == 'W':
            ax1.bar(x + (i - 1.5) * width, values, width, label=f'{ch} (dBFS)',
                    color=channel_colors[i], alpha=0.8, edgecolor='black')
        else:
            pass  # We'll do the directional channels on ax2

    ax1.set_xlabel('Microphone', fontsize=11)
    ax1.set_ylabel('W Channel Level (dBFS)', fontsize=11)
    # No title for publication (caption in paper)
    ax1.set_xticks(x)
    ax1.set_xticklabels([m['name'] for m in mic_data], fontsize=9)
    ax1.grid(True, axis='y', alpha=0.3, linestyle=':')

    # Right: Directional channels normalized to W
    for i, ch in enumerate(['X', 'Y', 'Z']):
        values = [m['data'][f'{ch}_rms'] / m['data']['W_rms'] for m in mic_data]
        ax2.bar(x + (i - 1) * width, values, width, label=f'{ch} ({["Front-Back", "Left-Right", "Up-Down"][i]})',
                color=channel_colors[i+1], alpha=0.8, edgecolor='black')

    ax2.set_xlabel('Microphone', fontsize=11)
    ax2.set_ylabel('Normalized to W Channel', fontsize=11)
    # No title for publication (caption in paper)
    ax2.set_xticks(x)
    ax2.set_xticklabels([m['name'] for m in mic_data], fontsize=9)
    # Legend positioned at center of second quarter (above second bar group), same y as upper right
    ax2.legend(loc='upper left', bbox_to_anchor=(0.25, 1.0), fontsize=9, framealpha=0.9)
    ax2.grid(True, axis='y', alpha=0.3, linestyle=':')

    # No suptitle for publication
    plt.tight_layout()

    output_png = OUTPUT_DIR / "pub_fig10_directional_distribution.png"
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"    PNG: {output_png}")

    # Save CSV
    csv_data = []
    for m in mic_data:
        row = {'microphone': m['name']}
        for key, val in m['data'].items():
            row[key] = val
        csv_data.append(row)

    fieldnames = ['microphone'] + list(mic_data[0]['data'].keys())
    save_csv(csv_data, fieldnames, OUTPUT_DIR / "pub_fig10_directional_distribution.csv")


# =============================================================================
# BINAURAL SPECTRAL COMPARISON - Full + Excerpt versions
# =============================================================================
def compute_spectral_welch(audio_path, excerpt_seconds=None):
    """Compute smoothed frequency response using Welch's method."""
    data, sr = sf.read(audio_path)

    # For stereo binaural, average L+R; for HOA, use W channel
    if data.ndim > 1:
        if data.shape[1] == 2:
            channel = (data[:, 0] + data[:, 1]) / 2  # Stereo average
        else:
            channel = data[:, 0]  # W channel for HOA
    else:
        channel = data

    # Take excerpt from middle if specified
    if excerpt_seconds:
        samples = int(excerpt_seconds * sr)
        start = max(0, (len(channel) - samples) // 2)
        end = min(len(channel), start + samples)
        channel = channel[start:end]

    # Use Welch's method for smoother spectrum
    nperseg = min(8192, len(channel) // 8)
    freqs, psd = signal.welch(channel, sr, nperseg=nperseg, noverlap=nperseg//2)

    # Convert to dB (power spectral density)
    psd_db = 10 * np.log10(psd + 1e-12)

    # Additional 1/3 octave smoothing for publication quality
    smoothed_db = np.copy(psd_db)
    for i in range(len(freqs)):
        if freqs[i] > 0:
            # 1/6 octave window
            f_low = freqs[i] / (2 ** (1/12))
            f_high = freqs[i] * (2 ** (1/12))
            mask = (freqs >= f_low) & (freqs <= f_high)
            if np.sum(mask) > 0:
                smoothed_db[i] = np.mean(psd_db[mask])

    return freqs, smoothed_db


def _plot_binaural_spectral(excerpt_seconds, suffix, title_suffix):
    """Helper to plot binaural spectral comparison."""
    mic_colors = {
        "SR-VRMIC (1OA)": "#d62728",
        "ZM-1 (3OA)": "#1f77b4",
        "Spcmic (3OA)": "#ff7f0e",
        "Spcmic (5OA)": "#2ca02c",
    }

    # Line widths - make them distinguishable
    linewidths = {
        "SR-VRMIC (1OA)": 2.0,
        "ZM-1 (3OA)": 1.8,
        "Spcmic (3OA)": 1.6,
        "Spcmic (5OA)": 1.4,
    }

    fig, ax = plt.subplots(figsize=(12, 6))

    all_data = []
    csv_data = []

    for mic_name, filename in BINAURAL_FILES:
        audio_path = comparison_dir() / filename
        if not audio_path.exists():
            print(f"    Warning: {filename} not found")
            continue

        print(f"    Processing: {mic_name}...")
        freqs, magnitude_db = compute_spectral_welch(audio_path, excerpt_seconds=excerpt_seconds)
        all_data.append((mic_name, freqs, magnitude_db))

    if not all_data:
        return None

    # Find common y-axis range from all data
    all_mags = []
    for _, freqs, mags in all_data:
        mask = (freqs >= 20) & (freqs <= 20000)
        all_mags.extend(mags[mask])
    all_mags = np.array(all_mags)
    valid_mags = all_mags[np.isfinite(all_mags)]
    y_min = np.min(valid_mags)
    y_max = np.max(valid_mags)
    y_range = y_max - y_min

    # Plot each microphone - reverse order so Spcmic 3OA (orange) is on top
    for mic_name, freqs, magnitude_db in reversed(all_data):
        mask = (freqs >= 20) & (freqs <= 20000)
        freqs_plot = freqs[mask]
        mag_plot = magnitude_db[mask]

        ax.semilogx(freqs_plot, mag_plot,
                    label=mic_name,
                    color=mic_colors.get(mic_name, '#7f7f7f'),
                    linestyle='-',
                    alpha=0.9,
                    linewidth=linewidths.get(mic_name, 1.5))

        # CSV: subsample to ~200 log-spaced points
        log_indices = np.unique(np.geomspace(1, len(freqs_plot)-1, 200).astype(int))
        for idx in log_indices:
            csv_data.append({
                'frequency_hz': round(freqs_plot[idx], 1),
                'microphone': mic_name,
                'magnitude_db': round(mag_plot[idx], 2)
            })

    ax.set_xlabel('Frequency (Hz)', fontsize=11)
    ax.set_ylabel('Power Spectral Density (dB)', fontsize=11)
    # No title for publication (caption in paper)
    ax.set_xlim(20, 20000)
    ax.set_ylim(y_min - 0.15 * y_range, y_max + 0.15 * y_range)
    ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
    ax.grid(True, which='major', alpha=0.4, linestyle='-')
    ax.grid(True, which='minor', alpha=0.2, linestyle=':')

    plt.tight_layout()
    output_png = OUTPUT_DIR / f"fig_binaural_spectral{suffix}.png"
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"    PNG: {output_png}")

    # Save CSV
    save_csv(csv_data, ['frequency_hz', 'microphone', 'magnitude_db'],
             OUTPUT_DIR / f"fig_binaural_spectral{suffix}.csv")

    return True


def plot_binaural_spectral_comparison():
    """Spectral comparison of binaural renders - both full and excerpt versions."""
    print("\n[Figure: Binaural Spectral Comparison]")

    # Version 1: 30-second excerpt
    print("  Generating excerpt version...")
    _plot_binaural_spectral(excerpt_seconds=30, suffix="_excerpt", title_suffix="30s excerpt")

    # Version 2: Full recording
    print("  Generating full version...")
    _plot_binaural_spectral(excerpt_seconds=None, suffix="_full", title_suffix="full")


# =============================================================================
# MAIN
# =============================================================================
def main():
    print("=" * 70)
    print("HOA CORPUS FIGURE GENERATION")
    print("=" * 70)
    print(f"Output directory: {OUTPUT_DIR}")

    # Generate all figures
    plot_lufs_mic_comparison()
    plot_lufs_corpus()
    plot_geographic_map()
    plot_timeline()
    plot_spatial_energy()
    plot_directional_distribution()  # New supplementary figure
    plot_binaural_spectral_comparison()

    print("\n" + "=" * 70)
    print("COMPLETE - All figures and CSV files generated")
    print("=" * 70)

    # List outputs
    print("\nGenerated files:")
    for f in sorted(OUTPUT_DIR.glob("pub_fig*")):
        print(f"  {f.name}")


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    main()
