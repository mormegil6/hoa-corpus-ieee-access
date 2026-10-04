#!/usr/bin/env python3
"""
Generate Session Inventory Table for LaTeX

Creates the LaTeX table of all recording sessions (data/session_inventory_table.tex,
read by the manuscript). Reads data/metadata/<session>.yaml, the authors'
per-session metadata files, which this repository does not ship; the deposit
carries one metadata.yaml per session under sessions/<id>/.

Author: Bartłomiej Mróz
Date: 2026-01-28
"""

import argparse
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent.parent
METADATA_DIR = SCRIPT_DIR / "data" / "metadata"
OUTPUT_DIR = Path(os.environ.get("IEEE_DATA_DIR", SCRIPT_DIR / "data"))


def load_all_metadata():
    """Load all session metadata files, excluding will_not_publish sessions."""
    sessions = []
    for yaml_file in sorted(METADATA_DIR.glob("*.yaml")):
        with open(yaml_file, 'r') as f:
            try:
                data = yaml.safe_load(f)
                if data:
                    pr = data.get('publication_readiness') or {}
                    if isinstance(pr, dict) and pr.get('status') == 'will_not_publish':
                        continue
                    sessions.append(data)
            except Exception as e:
                print(f"Error loading {yaml_file}: {e}")
    return sessions


def get_mic_abbreviation(mic_model):
    """Convert microphone model to abbreviation."""
    if not mic_model:
        return "-"
    mic_lower = mic_model.lower()
    if "zylia" in mic_lower or "zm-1" in mic_lower:
        return "ZM-1"
    elif "spcmic" in mic_lower or "harpex" in mic_lower:
        return "Spcmic"
    elif "saramonic" in mic_lower:
        return "SR-VRMIC"
    elif "nt-sf1" in mic_lower or "rode" in mic_lower:
        return "NT-SF1"
    else:
        return mic_model[:10]


def get_content_type_abbrev(content_type):
    """Convert content type to abbreviation."""
    mapping = {
        'solo_piano': 'Piano',
        'piano_duet': 'Piano duo',
        'choir': 'Choir',
        'choir_with_orchestra': 'Choir+Orch',
        'choir_with_soloists': 'Choir+Sol',
        'choir_with_ensemble': 'Choir+Ens',
        'orchestra': 'Orchestra',
        'ensemble': 'Ensemble',
        'chamber': 'Chamber',
        'ambient': 'Ambient',
        'ambience': 'Ambient',
        'vr_film_production': 'VR Prod',
    }
    return mapping.get(content_type, content_type or '-')


def get_venue_abbrev(venue_name, city):
    """Create abbreviated venue name."""
    if not venue_name:
        return city or "Unknown"

    # Known abbreviations
    if "Aula Politechniki" in venue_name:
        return "Aula PG"
    elif "Hol przed Aulą" in venue_name:
        return "PG Lobby"
    elif "Oliwa" in venue_name.lower() or ("Cathedral" in venue_name and "Gdańsk" in str(city)):
        return "Oliwa Cath."
    elif "Academy" in venue_name or "Moniuszko" in venue_name or "Akademia Muzyczna" in venue_name:
        return "AMuz Gdańsk"
    elif "pier" in venue_name.lower() or "Sopot" in venue_name:
        return "Sopot Pier"
    elif "quarry" in venue_name.lower() or "Piechcin" in venue_name:
        return "Piechcin"
    elif "cave" in venue_name.lower() or "Jędrzejewo" in venue_name:
        return "Jędrzejewo"
    elif "Fiqu" in venue_name:
        return "Fiqu Miqu"
    elif "Filharmoni" in venue_name:
        return "Philharmonic"
    elif "courtyard" in venue_name.lower():
        return "Courtyard"
    elif "Świętej Trójcy" in venue_name or "Trójcy" in venue_name:
        return "Holy Trinity"
    elif "Kościół" in venue_name:
        return "Church"
    else:
        # Truncate if too long
        if len(venue_name) > 15:
            return venue_name[:12] + "..."
        return venue_name


def escape_latex(text):
    """Escape special LaTeX characters."""
    if not text:
        return ""
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text


# Sessions with secondary microphones (for dagger footnote)
SESSIONS_WITH_SECONDARY_MIC = {
    3: 'NT-SF1',   # 2021-06-27 choir
    10: 'NT-SF1',  # 2023-06-03 Deus Ex Machina
    16: 'Spcmic',  # 2024-04-30 piano
    19: 'NT-SF1',  # 2024-12-10 piano
    21: 'NT-SF1',  # 2025-02-05 chamber
}

# Microphone comparison session
MIC_COMPARISON_SESSION = 18  # 2024-08-15


def generate_latex_table(sessions):
    """Generate LaTeX table for session inventory."""

    # Sort by date
    def get_date(s):
        # Handle both 'recording_date' and 'recording_dates' fields
        date_str = s.get('recording_date')
        if not date_str:
            dates = s.get('recording_dates', [])
            if dates and isinstance(dates, list):
                date_str = dates[0]
            else:
                date_str = '1900-01-01'
        try:
            return datetime.strptime(str(date_str), '%Y-%m-%d')
        except:
            return datetime(1900, 1, 1)

    sessions_sorted = sorted(sessions, key=get_date)

    # Generate table
    lines = []
    lines.append(r"% Session Inventory Table - Auto-generated")
    lines.append(r"% Generated: " + datetime.now().strftime('%Y-%m-%d %H:%M'))
    lines.append(r"")
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"    \centering")
    lines.append(r"    \caption{Complete Session Inventory}\label{tab:session_inventory}")
    lines.append(r"    \small")
    lines.append(r"    \setlength{\tabcolsep}{4pt}")
    lines.append(r"    \begin{tabular}{@{}rlll l@{\hspace{4pt}}r@{}}")
    lines.append(r"        \toprule")
    lines.append(r"        No. & Date & Venue & Content & Mic & Dur. \\")
    lines.append(r"        \midrule")

    for i, session in enumerate(sessions_sorted, 1):
        # Handle both 'recording_date' and 'recording_dates' fields
        date = session.get('recording_date')
        if not date:
            dates = session.get('recording_dates', [])
            if dates and isinstance(dates, list):
                date = dates[0]

        if date:
            try:
                dt = datetime.strptime(str(date), '%Y-%m-%d')
                date_fmt = dt.strftime('%Y-%m-%d')
            except:
                date_fmt = str(date)
        else:
            date_fmt = '-'

        venue = get_venue_abbrev(session.get('venue_name', ''), session.get('city', ''))
        content = get_content_type_abbrev(session.get('content_type', ''))
        mic = get_mic_abbreviation(session.get('primary_mic_model', ''))
        duration = session.get('published_content_duration_minutes', 0)
        if duration:
            dur_str = f"{duration:.0f}"
        else:
            dur_str = "-"

        # Handle special cases
        # Microphone comparison session
        if i == MIC_COMPARISON_SESSION:
            content = "Comparison*"
            mic = "Multi"

        # Add dagger for sessions with secondary microphones
        if i in SESSIONS_WITH_SECONDARY_MIC:
            content = content + r"$^\dagger$"

        # Escape LaTeX special chars (but not our added LaTeX commands)
        venue = escape_latex(venue)
        # Don't escape content if it has our LaTeX commands
        if r"$^\dagger$" not in content:
            content = escape_latex(content)

        lines.append(f"        {i} & {date_fmt} & {venue} & {content} & {mic} & {dur_str} \\\\")

    lines.append(r"        \botrule")
    lines.append(r"    \end{tabular}")
    lines.append(r"")
    lines.append(r"    \smallskip")

    # Build footnote with secondary mic sessions grouped
    ntsf1_sessions = [str(s) for s in sorted(SESSIONS_WITH_SECONDARY_MIC.keys()) if SESSIONS_WITH_SECONDARY_MIC[s] == 'NT-SF1']
    spcmic_sessions = [str(s) for s in sorted(SESSIONS_WITH_SECONDARY_MIC.keys()) if SESSIONS_WITH_SECONDARY_MIC[s] == 'Spcmic']

    footnote = r"    \footnotesize{Duration in minutes. Mic: ZM-1 = Zylia ZM-1, Spcmic = Harpex Spcmic, Multi = ZM-1 + Spcmic + SR-VRMIC. *Microphone comparison session (Section~\ref{sec:comparison}). $^\dagger$ Secondary microphone: "
    if ntsf1_sessions:
        footnote += f"NT-SF1 (sessions {', '.join(ntsf1_sessions)})"
    if spcmic_sessions:
        if ntsf1_sessions:
            footnote += " or "
        footnote += f"Spcmic (session {', '.join(spcmic_sessions)})"
    footnote += ".}"

    lines.append(footnote)
    lines.append(r"\end{table}")

    return '\n'.join(lines)


def main():
    print("="*60)
    print("GENERATING SESSION INVENTORY TABLE")
    print("="*60)

    sessions = load_all_metadata()
    print(f"Loaded {len(sessions)} sessions")
    if not sessions:
        sys.exit(f"no session metadata found in {METADATA_DIR}; the committed "
                 "data/session_inventory_table.tex is left untouched")

    latex_table = generate_latex_table(sessions)

    # Save to file
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "session_inventory_table.tex"
    with open(output_path, 'w') as f:
        f.write(latex_table if latex_table.endswith("\n") else latex_table + "\n")

    print(f"\nGenerated: {output_path}")
    print("\nTo include in main.tex, add:")
    print(r"    \input{session_inventory_table.tex}")

    # Also print to console for review
    print("\n" + "="*60)
    print("GENERATED TABLE:")
    print("="*60)
    print(latex_table)


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    main()
