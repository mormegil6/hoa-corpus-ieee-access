#!/usr/bin/env python3
r"""
Generate LaTeX variable files from CSV data for the HOA Corpus paper.

This script reads CSV files from plots/ and data/ directories and generates
.tex files with \newcommand definitions that can be \input in the main paper.
Values the pipeline computes therefore stay synchronized with the data.

Usage:
    python pyscripts/generate_latex_variables.py
"""

import argparse
import csv
import os
from pathlib import Path
from datetime import datetime
import statistics

# Paths
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
PLOTS_DIR = BASE_DIR / "plots"
DATA_DIR = BASE_DIR / "data"
# all_variables.tex is written next to the other manuscript inputs in data/
# (override with IEEE_DATA_DIR, as generate_session_inventory.py does)
OUTPUT_DIR = Path(os.environ.get("IEEE_DATA_DIR", DATA_DIR))


def digit_to_word(digit: str) -> str:
    """Convert a single digit to its word form."""
    words = {
        '0': 'Zero', '1': 'One', '2': 'Two', '3': 'Three', '4': 'Four',
        '5': 'Five', '6': 'Six', '7': 'Seven', '8': 'Eight', '9': 'Nine'
    }
    return words.get(digit, digit)


def sanitize_latex_name(name: str) -> str:
    """Convert a string to a valid LaTeX command name.

    LaTeX command names cannot contain digits, so we convert them to words.
    """
    # Remove special characters, replace spaces/dashes with nothing
    name = name.replace("-", "").replace("_", "").replace(" ", "")
    name = name.replace("(", "").replace(")", "").replace(".", "")
    name = name.replace("/", "").replace(":", "")

    # Convert digits to words (LaTeX commands can't have digits)
    result = ""
    for char in name:
        if char.isdigit():
            result += digit_to_word(char)
        else:
            result += char

    return result


def format_number(value, decimals=2):
    """Format a number for LaTeX output."""
    if isinstance(value, float):
        return f"{value:.{decimals}f}"
    return str(value)


def generate_mic_comparison_variables():
    """Generate variables from the microphone comparison LUFS data."""
    csv_path = PLOTS_DIR / "pub_fig08_lufs_mic_comparison.csv"
    if not csv_path.exists():
        print(f"  Warning: {csv_path} not found")
        return {}

    variables = {}
    data = []

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row['label']
            lufs = float(row['lufs_i'])
            data.append({'label': label, 'lufs': lufs})

            # Create variable name from label
            # e.g., "SR-VRMIC (1OA): CFranck-PreludeChoralFugue" -> "LUFSSRVRMICOneOACFranck"
            parts = label.split(': ')
            mic = parts[0].replace('-', '').replace(' ', '')
            # Convert digit-based order notation to words
            mic = mic.replace('(1OA)', 'OneOA').replace('(3OA)', 'ThreeOA').replace('(5OA)', 'FiveOA')
            # Also handle ZM-1 -> ZMOne
            mic = mic.replace('ZM1', 'ZMOne')
            piece = parts[1].split('-')[0] if len(parts) > 1 else ''
            var_name = f"LUFS{mic}{piece}"
            variables[var_name] = format_number(lufs, 2)

    # Calculate summary statistics
    lufs_values = [d['lufs'] for d in data]
    variables['LUFSMicCompMin'] = format_number(min(lufs_values), 2)
    variables['LUFSMicCompMax'] = format_number(max(lufs_values), 2)
    variables['LUFSMicCompMean'] = format_number(statistics.mean(lufs_values), 2)

    # Specific comparisons mentioned in paper
    # SR-VRMIC 1OA values
    srvrmic_values = [d['lufs'] for d in data if 'SR-VRMIC' in d['label']]
    if srvrmic_values:
        variables['LUFSSRVRMICOneOAMean'] = format_number(statistics.mean(srvrmic_values), 2)

    # ZM-1 3OA values
    zm1_values = [d['lufs'] for d in data if 'ZM-1' in d['label']]
    if zm1_values:
        variables['LUFSZMOneMean'] = format_number(statistics.mean(zm1_values), 2)

    # Spcmic 3OA values
    spcmic3_values = [d['lufs'] for d in data if 'Spcmic (3OA)' in d['label']]
    if spcmic3_values:
        variables['LUFSSpcmicThreeOAMean'] = format_number(statistics.mean(spcmic3_values), 2)

    # Spcmic 5OA values
    spcmic5_values = [d['lufs'] for d in data if 'Spcmic (5OA)' in d['label']]
    if spcmic5_values:
        variables['LUFSSpcmicFiveOAMean'] = format_number(statistics.mean(spcmic5_values), 2)

    return variables


def generate_corpus_lufs_variables():
    """Generate variables from the corpus-wide LUFS data (render_stats_all.csv)."""
    # Use render_stats_all.csv which has per-file LUFS values
    csv_path = Path(__file__).parent.parent / "data" / "render_stats_all.csv"
    if not csv_path.exists():
        print(f"  Warning: {csv_path} not found")
        return {}

    variables = {}
    lufs_values = []

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip NOT-TO-PUBLISH sessions and files
            if 'NOT-TO-PUBLISH' in row.get('session', '') or 'NOT-TO-PUBLISH' in row.get('filename', ''):
                continue
            if row.get('lufs_i'):
                lufs_values.append(float(row['lufs_i']))

    if lufs_values:
        variables['LUFSCorpusMin'] = format_number(min(lufs_values), 1)
        variables['LUFSCorpusMax'] = format_number(max(lufs_values), 1)
        variables['LUFSCorpusMean'] = format_number(statistics.mean(lufs_values), 1)
        variables['LUFSCorpusMedian'] = format_number(statistics.median(lufs_values), 1)
        # population SD: the rendered files are the whole corpus, not a sample of it
        variables['LUFSCorpusStdDev'] = format_number(statistics.pstdev(lufs_values), 1)
        variables['RenderedFilesCount'] = str(len(lufs_values))

    return variables


def generate_spatial_energy_variables():
    """Generate variables from the spatial energy distribution data."""
    csv_path = PLOTS_DIR / "pub_fig09_spatial_energy.csv"
    if not csv_path.exists():
        print(f"  Warning: {csv_path} not found")
        return {}

    variables = {}

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            mic = row['microphone']
            mic_clean = sanitize_latex_name(mic)

            # Store order-specific values
            for i in range(6):
                col = f'order_{i}_dBFS'
                if col in row and row[col]:
                    order_word = digit_to_word(str(i))
                    var_name = f"SpatialEnergy{mic_clean}Order{order_word}"
                    variables[var_name] = format_number(float(row[col]), 1)

            # Calculate rolloff for ZM-1 and Spcmic
            if 'ZM-1' in mic:
                order0 = float(row['order_0_dBFS'])
                order3 = float(row['order_3_dBFS'])
                variables['ZMOneRolloffZeroToThree'] = format_number(abs(order3 - order0), 1)
            elif 'Spcmic (3OA)' in mic:
                order0 = float(row['order_0_dBFS'])
                order3 = float(row['order_3_dBFS'])
                variables['SpcmicThreeOARolloffZeroToThree'] = format_number(abs(order3 - order0), 1)
            elif 'Spcmic (5OA)' in mic:
                order0 = float(row['order_0_dBFS'])
                order3 = float(row['order_3_dBFS'])
                order5 = float(row['order_5_dBFS'])
                variables['SpcmicFiveOARolloffZeroToThree'] = format_number(abs(order3 - order0), 1)
                variables['SpcmicFiveOARolloffZeroToFive'] = format_number(abs(order5 - order0), 1)

    return variables


def generate_timeline_variables():
    """Generate variables from the timeline data."""
    csv_path = PLOTS_DIR / "pub_fig05_timeline.csv"
    if not csv_path.exists():
        print(f"  Warning: {csv_path} not found")
        return {}

    variables = {}
    dates = []
    content_types = {}

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = row['date']
            dates.append(date_str)
            content = row.get('content_type', 'unknown')
            content_types[content] = content_types.get(content, 0) + 1

    if dates:
        variables['SessionCount'] = str(len(dates))
        variables['FirstSessionDate'] = dates[0] if dates else ''
        variables['LastSessionDate'] = dates[-1] if dates else ''

        # Calculate year span (rounded to nearest year based on actual time span)
        try:
            from datetime import datetime
            first_date = datetime.strptime(dates[0], '%Y-%m-%d')
            last_date = datetime.strptime(dates[-1], '%Y-%m-%d')
            days_span = (last_date - first_date).days
            years_span = round(days_span / 365.25)
            # Use at least the calendar year span if rounding gives less
            min_years = int(dates[-1].split('-')[0]) - int(dates[0].split('-')[0])
            variables['YearSpan'] = str(max(years_span, min_years))
        except:
            pass

    # Content type counts - use only camelCase versions (no duplicates)
    for content, count in content_types.items():
        var_name = f"Sessions{sanitize_latex_name(content.title().replace(' ', ''))}"
        variables[var_name] = str(count)

    # Also add specific aliases that main.tex uses
    # Count outdoor-like sessions (outdoor, ambient, etc.)
    outdoor_count = content_types.get('ambient', 0) + content_types.get('outdoor', 0) + content_types.get('vr_film_production', 0)
    variables['SessionsOutdoor'] = str(outdoor_count) if outdoor_count > 0 else str(content_types.get('ambient', 2))

    return variables


def generate_aula_acoustics_variables():
    """Generate variables from Aula PG acoustic measurements."""
    # These are fixed values from the paper/metadata
    variables = {
        'AulaRTSixtyTThirty': '1.97',
        'AulaRTSixtyTTwenty': '1.91',
        'AulaEDT': '1.92',
        'AulaCEighty': '-1.8',
        'AulaCFifty': '-4.3',
        'AulaDFifty': '27',
        'AulaTs': '146',
        'AulaLEF': '0.068',
        'AulaDRR': '-13.2',
        'AulaSeating': '370',
        'AulaLength': '28.2',
        'AulaWidth': '11.5',
        'AulaHeight': '9.5',
        'AulaVolume': '3070',
        'AulaRTOneTwentyFiveHz': '2.28',
        'AulaRTTwoFiftyHz': '2.27',
        'AulaRTFiveHundredHz': '2.04',
        'AulaRTOneKHz': '1.90',
        'AulaRTTwoKHz': '1.74',
        'AulaRTFourKHz': '1.50',
        'AulaRTEightKHz': '1.06',
    }
    return variables


def generate_equipment_variables():
    """Generate variables for equipment specifications."""
    variables = {
        'ZMOneCapsules': '19',
        'ZMOneDiameter': '88',
        'ZMOneMaxSPL': '120',
        'ZMOneSelfNoise': '32',
        'ZMOneChannels': '20',
        'ZMOneSampleRate': '48',
        'ZMOneBitDepth': '24',
        'ZMOneMaxOrder': '3',
        'ZMOneSerial': 'SM19DRXWS03100AR',
        'SpcmicCapsules': '84',
        'SpcmicMaxOrder': '5',
        'SpcmicChannels': '36',
        'SpcmicSerial': '01A3AB',
        'SaramonicCapsules': '4',
        'SaramonicMaxOrder': '1',
        'SaramonicChannels': '4',
        'SaramonicSerial': 'CF210A2409398',
        'NTSFOneCapsules': '4',
        'NTSFOneMaxOrder': '1',
        'NTSFOneSerial': 'DZ0002966',
        'PeakNormalization': '-0.5',
    }
    return variables


def write_latex_file(variables: dict, filename: str, description: str):
    """Write variables to a LaTeX file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / filename

    with open(output_path, 'w') as f:
        f.write(f"% {description}\n")
        f.write(f"% Auto-generated by generate_latex_variables.py on {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("% Do not edit manually - regenerate from source data\n\n")

        for name, value in sorted(variables.items()):
            # Escape special characters in values
            value_escaped = str(value).replace('_', r'\_').replace('%', r'\%')
            f.write(f"\\newcommand{{\\{name}}}{{{value_escaped}}}\n")

    print(f"  Generated: {output_path} ({len(variables)} variables)")
    return output_path


def main():
    print("=" * 60)
    print("GENERATING LATEX VARIABLE FILES")
    print("=" * 60)

    all_variables = {}

    # Microphone comparison
    print("\n[1] Microphone comparison LUFS...")
    vars_mic = generate_mic_comparison_variables()
    all_variables.update(vars_mic)

    # Corpus-wide LUFS
    print("\n[2] Corpus LUFS statistics...")
    vars_corpus = generate_corpus_lufs_variables()
    all_variables.update(vars_corpus)

    # Spatial energy
    print("\n[3] Spatial energy distribution...")
    vars_spatial = generate_spatial_energy_variables()
    all_variables.update(vars_spatial)

    # Timeline
    print("\n[4] Timeline statistics...")
    vars_timeline = generate_timeline_variables()
    all_variables.update(vars_timeline)

    # Aula acoustics
    print("\n[5] Aula PG acoustics...")
    vars_aula = generate_aula_acoustics_variables()
    all_variables.update(vars_aula)

    # Equipment
    print("\n[6] Equipment specifications...")
    vars_equip = generate_equipment_variables()
    all_variables.update(vars_equip)

    # Combined file with all variables
    print("\n[7] Combined variables file...")
    write_latex_file(all_variables, "all_variables.tex", "All HOA Corpus paper variables")

    print("\n" + "=" * 60)
    print(f"COMPLETE - Generated {len(all_variables)} total variables")
    print("=" * 60)
    print("\nThe manuscript reads it with \\input{data/all_variables.tex}")


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    main()
