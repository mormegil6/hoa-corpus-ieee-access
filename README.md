[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.21789163-blue.svg)](https://doi.org/10.5281/zenodo.21789163) ![Python](https://img.shields.io/badge/Python-3.9+-blue.svg) ![numpy](https://img.shields.io/badge/numpy-1.24+-blue.svg) ![scipy](https://img.shields.io/badge/scipy-1.11+-blue.svg) ![soundfile](https://img.shields.io/badge/soundfile-0.12+-blue.svg) ![matplotlib](https://img.shields.io/badge/matplotlib-3.7+-blue.svg) [![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

# HOA Seven-Year Corpus - IEEE Access Analysis Pipeline

Supplementary materials for the paper:

***"A Seven-Year Higher-Order Ambisonics Recording Corpus: Dataset, Methodology, and a Co-Located Spherical Microphone Array Comparison"***
Bartłomiej Mróz, Szymon Zaporowski · *IEEE Access* (under review)

This repository contains:
- The corpus-wide figure and LaTeX-macro pipeline (geographic distribution, recording timeline, room acoustics, loudness distribution, session inventory)
- The microphone-comparison bootstrap uncertainty analysis (confidence intervals on the per-order energy rolloff) and the open re-encoding of the ZM-1 capsule signals
- The dataset card of the deposited corpus (datasheet, metadata schema, partition table, checksums)
- Pre-computed results (CSV tables, LaTeX macros, publication figures), so most of the repository reproduces without downloading any audio

Methodology, interpretation and discussion of results are in the manuscript. The comparison session's core signal analysis (per-order RMS, LUFS, spectral, directional metrics) was first published for the companion AES Copenhagen paper; see [hoa-mic-comparison-aes2026](https://github.com/mormegil6/hoa-mic-comparison-aes2026) for that repository. `revision_stats.py` here reimplements the same per-order metric definition rather than depending on that repo, so this repository is self-contained.

## Repository Structure

```
.
├── pyscripts/
│   ├── analysis_utils.py             # Shared config, spectral helpers, mic definitions
│   ├── generate_all_figures.py       # Audio-driven: computes the Fig. 6-10 CSVs
│   ├── render_ieee_figures.py        # CSV-driven: renders Figs 3-10 at IEEE column width
│   ├── generate_latex_variables.py   # CSV -> data/all_variables.tex (\newcommand macros for the manuscript)
│   ├── parse_render_stats.py         # REAPER render reports -> data/render_stats_all.csv
│   ├── analyze_aula_acoustics.py     # Room-acoustic parameters (RT60, C80, ...)
│   ├── calculate_corpus_stats.py     # Corpus size/duration/content-type inventory
│   ├── generate_session_inventory.py # Session inventory LaTeX table
│   ├── generate_map_only.py          # Fig. 4 maps standalone (from CSV)
│   ├── plot_rt60.py                  # Fig. 3 standalone
│   ├── plot_lufs_distribution.py     # Per-file LUFS-I bar chart (not a manuscript figure)
│   ├── plot_spectral_comparison.py   # Fig. 7 standalone (needs audio)
│   ├── revision_stats.py             # Paired moving-block bootstrap (confidence intervals)
│   ├── revision_figures.py           # Two-piece Fig. 9, Figs 10a/10b with CI whiskers
│   ├── reencode_zm1.py               # Open re-encoding of the ZM-1 A-format
│   ├── reencode_bootstrap.py         # Bootstrap CIs for the re-encoded rolloffs (from caches)
│   ├── convention_analysis.py        # Per-order levels, mean-RMS vs energy-sum convention (from caches)
│   ├── make_reencode_variables.py    # reencode_bootstrap.csv -> LaTeX macros
│   ├── scan_deposit.py               # Deposit checkout -> corpus_scan.csv (sizes, hashes, durations)
│   ├── build_dataset_card.py         # corpus_scan.csv -> dataset_card/ partition table and checksums; metadata validation
│   └── make_spcmic.py                # Raw 84-channel capture -> .spcmic container the Harpex app reads
├── plots/                            # Figure inputs (CSV)
├── figures/                          # Rendered corpus figures (Figs 3-10)
├── data/                             # Render statistics, aggregated LaTeX macros, session inventory
├── dataset_card/                     # Datasheet, metadata schema, partition table, deposit checksums
├── revision_results/                 # Bootstrap and re-encoding outputs - see revision_results/README.md
│   ├── *.csv, *.tex                  #   Per-order levels, rolloffs and CIs, frame-level tables, LaTeX macros
│   ├── cache/frames_*.npz            #   Frame-energy caches (reproduce without audio)
│   ├── reencode/                     #   Open re-encoding: banks/, cache/, CSV/JSON, LaTeX macros
│   ├── figures/                      #   Figs 9, 10a, 10b with CI whiskers
│   └── SHA256SUMS                    #   Checksums of everything above
├── requirements.txt                  # Version ranges
├── requirements-lock.txt             # Exact versions behind the committed outputs (Python 3.14.7)
├── LICENSE
└── README.md
```

## Recordings

**Recording corpus**: *A Seven-Year Corpus of Higher-Order Ambisonics Recordings*, deposited at *Bridge of Data* (Most Danych), Gdańsk University of Technology, [doi.org/10.34808/w8bx-2094](https://doi.org/10.34808/w8bx-2094) (CC BY-NC-SA 4.0). That DOI resolves to the latest version; the analyses here use v1.2 (2026-09-04).

The recordings are not included in this repository. Every script that opens audio reads the deposit as downloaded: set `HOA_CORPUS_DIR` to the deposit root (the directory holding `sessions/`).

## Setup

```sh
pip install -r requirements.txt
```

`requirements.txt` gives version ranges. `requirements-lock.txt` is the `pip freeze` of the Python 3.14.7 environment that produced the committed outputs (numpy 2.5.2, scipy 1.18.1, soundfile 0.14.0, matplotlib 3.11.1, PyYAML 6.0.3, jsonschema 4.26.0); `python3.14 -m venv .venv && pip install -r requirements-lock.txt` recreates it. Matplotlib releases move the canvas by a pixel or two, so the same figure from another version is visually equal but not byte-identical.

## Corpus Figures

| Figure | Source | Regenerate with |
|---|---|---|
| 1 (photo collage), 2 (pipeline diagram) | Static artwork, kept with the manuscript | not generated |
| 3 (RT60), 5 (timeline), 6 (LUFS histogram), 8 (LUFS mic comparison), 9, 10 | `plots/*.csv` | `render_ieee_figures.py` |
| 4 (maps) | `plots/pub_fig04_geographic_map.csv` + OpenStreetMap/CARTO tiles | `render_ieee_figures.py 04` or `generate_map_only.py`, with `pip install contextily geopandas` and network access; skipped with a notice otherwise |
| 7 (spectral comparison) | The four comparison-session renders | `render_ieee_figures.py 07` with `HOA_CORPUS_DIR` set; skipped otherwise, leaving the committed render in place |
| 9, 10a, 10b as printed (with CI whiskers) | `revision_results/*.csv` | `revision_figures.py` |

```sh
python3 pyscripts/render_ieee_figures.py          # all figures -> figures/
python3 pyscripts/render_ieee_figures.py 09 10    # selected figure numbers
```

Set `IEEE_FIG_DIR` to render somewhere else; `IEEE_DATA_DIR` does the same for `generate_session_inventory.py`, `generate_latex_variables.py` and `parse_render_stats.py`. The Fig. 6 and 8-10 CSVs in `plots/` are recomputed from the deposit audio by `generate_all_figures.py`; the Fig. 3 CSV holds the measured RT60 values (`plot_rt60.py`), and the Fig. 4 and 5 CSVs and `data/session_inventory_table.tex` are built from the authors' per-session metadata files, which are not part of this repository, so those three are committed as inputs.

## Numeric Claims in the Manuscript

Every number the pipeline computes enters the manuscript as a LaTeX macro, not a typed literal:

```
data/render_stats_all.csv, plots/*.csv  ->  generate_latex_variables.py  ->  data/all_variables.tex                          ->  \input{} in the manuscript
revision_results/cache/frames_*.npz     ->  revision_stats.py            ->  revision_results/revision_stats_variables.tex   ->  \input{}
reencode/reencode_bootstrap.csv         ->  make_reencode_variables.py   ->  revision_results/reencode/reencode_variables.tex -> \input{}
```

[`data/render_stats_all.csv`](data/render_stats_all.csv) is what `parse_render_stats.py` writes from the REAPER render reports that sit next to each render in the deposit (`sessions/<session>/audio/*.render_stats.html`); `calculate_corpus_stats.py` prints the per-order and content-type counts of the manuscript's corpus tables from it and from the deposit's `metadata.yaml` files.

Values that the manuscript quotes but that are documented rather than computed here: the inter-device alignment of the A-format captures ([`revision_results/aformat_alignment.csv`](revision_results/aformat_alignment.csv), transcribed from the deposit's `audio_a_format/AFORMAT_README.md`), the Ginastera cross-session rolloffs (2024-04-30 session), the per-array normalization gains of the renders, and the capsule peak levels of the A-format masters (deposit metadata, summarised in [`dataset_card/DATASHEET.md`](dataset_card/DATASHEET.md)). No script in this repository produces those numbers.

## Uncertainty Analysis (Bootstrap Confidence Intervals)

`revision_stats.py` attaches confidence intervals to the microphone-comparison results. Each recording of the co-located comparison session (2024-08-15) is analysed in 1-second frames; because all arrays captured the same performance simultaneously, frames are paired across arrays by wall-clock time, so the between-array rolloff difference is resampled as a paired statistic and the programme-level variance shared by both arrays cancels. Resampling uses a moving-block bootstrap (30-second blocks, 2000 replicates, fixed seed) to respect the temporal correlation of musical material. Every rolloff estimate is reported with its percentile 95% CI and bootstrap standard error; `--block-seconds` changes the block length and `--block-sweep` repeats the rolloff bootstraps at several block lengths so the sensitivity of the intervals to that choice can be cited.

```sh
python3 pyscripts/revision_stats.py --base-dir /path/to/deposit --block-sweep 10,20,30,60,120   # frame caches + CIs + sensitivity
python3 pyscripts/revision_figures.py                                                          # figures with CI whiskers
```

The frame-energy caches in `revision_results/cache/` are committed (~1.1 MB), so both commands reproduce every statistic and figure of this analysis without downloading the ~38 GB of session audio: `revision_stats.py` only reads WAV files whose cache is missing, so `--base-dir` may be any path when the caches are present. Full details, the resampling rationale, the frame alignment of the two renders, and the headline numbers are in [`revision_results/README.md`](revision_results/README.md).

## Open re-encoding of the ZM-1 A-format

`reencode_zm1.py` re-encodes the deposited raw ZM-1 capsule signals of the comparison session with an open, measurement-model-based encoder instead of the factory Zylia Ambisonics Converter, so the per-order rolloff can be compared across regularization strategies. Six FIR banks (16 x 19 x 512 taps: Tikhonov with and without order limiting, soft-limit at 20/30/40 dB, MMSE at a 20-dB SNR prior against a simulated, not measured, capsule-noise spectrum) are built from the `zm1_encoder` package, streamed over the A-format files with an overlap-add FFT convolver, and reduced to the same per-1-s-frame energy caches that `revision_stats.py` uses; no B-format audio is written. `reencode_bootstrap.py` attaches the single-array and paired block-bootstrap intervals, `convention_analysis.py` tabulates the committed caches under the mean-RMS and energy-sum conventions, and `make_reencode_variables.py` emits the `\Reenc...` macros.

```sh
export HOA_CORPUS_DIR="/path/to/deposit"           # or --corpus-dir
export HOA_ARRAY_CAL_DIR="/path/to/hoa-array-cal"   # banks and validate only
python3 pyscripts/reencode_zm1.py banks        # six FIR banks -> revision_results/reencode/banks/
python3 pyscripts/reencode_zm1.py validate     # streaming convolver vs zm1_encoder.validate.apply_fir_bank (60 s)
python3 pyscripts/reencode_zm1.py factory      # frame caches + levels of the factory 3OA renders
python3 pyscripts/reencode_zm1.py sweep        # six configs x two pieces -> cache/, results_sweep.json
python3 pyscripts/reencode_zm1.py summary      # reencode_summary.csv
python3 pyscripts/reencode_bootstrap.py        # reencode_bootstrap.csv (CIs, lag tables)
python3 pyscripts/convention_analysis.py       # convention_table.csv, convention_results.json
python3 pyscripts/make_reencode_variables.py   # reencode_variables.tex
```

What each step needs:

- `factory` and `sweep` read the deposit's `sessions/2024-08-15_aula-pg_solo-piano-mic-comparison/` (`audio_a_format/AFORMAT_ZM1_*.wav`, ~6.1 GB, and `audio/3OA_ZM1_*.wav`, ~4.9 GB) and the committed banks; `summary` and the last three commands run from the committed `reencode/` alone.
- `banks` and `validate` import the `zm1_encoder` package from hoa-array-cal, a separate repository of the first author that is not yet publicly released (commit `a6a4e171bc35f0493447651c5c3ff414b66e226d`; `validate` also needs pandas). Until that release, readers cannot rebuild the banks or run the convolver check; the six banks are committed, together with `banks/capsule_noise_psd_simulated.npy`, the simulated per-capsule noise PSD the MMSE bank regularizes against (`zm1_encoder.simulate.simulated_capsule_noise(5.0, seed=0)` through `scipy.signal.welch`, nperseg 8192; its sha256 is recorded in `banks/mmse_20.json`).

What it produces, all committed under `revision_results/reencode/` (~6.2 MB):

| File | Contents |
|---|---|
| `banks/<config>.npy`, `banks/<config>.json` | FIR bank (16, 19, 512) float32 and its build parameters |
| `banks/capsule_noise_psd_simulated.npy` | Simulated capsule-noise PSD used by the `mmse_20` bank |
| `cache/frames_ZMOne_<config>_<piece>.npz` | Per-frame per-channel energies of each re-encoding (and of the factory renders) |
| `validation.json` | Streaming convolver vs reference convolution on 60 s of Franck (sample and per-order energy agreement: `max_abs_sample_diff_rel_to_peak` 4.9e-7, `max_rel_per_order_energy_diff` 1.9e-7) |
| `results_factory.json`, `results_sweep.json` | Per-order levels and 0-3 rolloffs (mean-RMS and energy-sum) per run |
| `reencode_summary.csv` | The same as one table |
| `reencode_bootstrap.csv` | Single-array 95% CIs per config and piece; paired-vs-Spcmic rows with the lag table and, where the lag is unambiguous, the paired CI; column semantics in [`revision_results/README.md`](revision_results/README.md#re-encoding-bootstrap-table) |
| `convention_table.csv`, `convention_results.json` | Committed caches under both conventions; the JSON adds the paired differences and the ideal SN3D diffuse-field profile |
| `reencode_variables.tex` | `\Reenc...` macros consumed by the manuscript |

Paths recorded in these files are relative to `revision_results/reencode/` and to the deposit root. The factory ZM-1 and Spcmic 3OA rows of `reencode_bootstrap.csv` carry the intervals of `revision_results/rolloff_bootstrap.csv` (`ci_source` column), so each of those quantities has one committed interval.

## Rebuilding a `.spcmic` file from a raw 84-channel capture

`pyscripts/make_spcmic.py` rewrites an 84-channel Harpex Spcmic capture into the container the manufacturer's application reads, so that a recording made outside that application, for example through a DAW, can be loaded back into it and encoded with the factory converter. Without this, a capture taken through a DAW can only be encoded with open encoders, and its per-order energy is not comparable with the factory renders in the corpus.

```sh
python3 pyscripts/make_spcmic.py IN.wav OUT.spcmic                    # whole file
python3 pyscripts/make_spcmic.py IN.wav OUT.spcmic --start 300 --seconds 60   # a test excerpt
```

The input may be Wave64 or RIFF/RF64 and must be 84-channel 48 kHz 24-bit PCM; anything else is refused rather than converted. Only the wrapper changes. Sample data is copied verbatim, with no resampling, requantisation or channel reordering.

The output reproduces the application's own layout: a `RIFF` tag with the 32-bit size fields saturated to `0xFFFFFFFF` and the true lengths carried in a `ds64` chunk, followed by `fmt ` (18 bytes), `fact` and `data`, giving a 94-byte header. That hybrid is not what the RF64 specification permits above 4 GiB, which is why libsndfile, CoreAudio, SoX and Python's `wave` all report such files as 355 s (the saturated size field divided by the 84-channel data rate) and raise no error, while FFmpeg reads them correctly. The layout is reproduced deliberately, because it is what the application accepts. Round-tripping a 60-s excerpt of a native `.spcmic` reproduces its chunk layout exactly with the audio bytes unchanged, and a file built from a DAW capture of the same array in a different hall opened in the application and exported a 3rd-order render whose 0th-to-3rd-order rolloff was 8.46 dB, against 8.4 and 8.5 dB for the two corpus renders of that array; the test files are not distributed.

## Dataset card

`dataset_card/` holds the datasheet ([`DATASHEET.md`](dataset_card/DATASHEET.md)), the JSON schema of the per-session `metadata.yaml` ([`metadata_schema.json`](dataset_card/metadata_schema.json)), the session-level train/validation/test partition ([`splits.csv`](dataset_card/splits.csv), rationale in [`SPLITS.md`](dataset_card/SPLITS.md)) and [`SHA256SUMS.txt`](dataset_card/SHA256SUMS.txt) of every audio file in the deposit. Two scripts build it from a deposit checkout: `scan_deposit.py` walks the audio files and writes `corpus_scan.csv` (one row per WAV: path, session, filename, bytes, sha256, frames, channels, duration_s; not committed), and `build_dataset_card.py` turns the scan into `splits.csv` and `SHA256SUMS.txt` and validates every `metadata.yaml` against the schema.

```sh
export HOA_CORPUS_DIR="/path/to/deposit"       # or --corpus-dir
python3 pyscripts/scan_deposit.py corpus_scan.csv          # hashes ~200 GB of audio
python3 pyscripts/build_dataset_card.py --scan corpus_scan.csv
```

## Reproducibility

Everything below was checked on 2026-09-06 in the `requirements-lock.txt` environment against deposit v1.2. [`revision_results/SHA256SUMS`](revision_results/SHA256SUMS) lists the checksums of the caches, every committed CSV/tex output, `reencode/` and `revision_results/figures/`; verify a checkout with `cd revision_results && sha256sum -c SHA256SUMS` (`shasum -a 256 -c SHA256SUMS` on macOS).

| Committed output | Regenerated by | Needs | Result |
|---|---|---|---|
| `revision_results/*.csv`, `revision_stats_variables.tex`, `revision_results/figures/*.png` | `revision_stats.py --base-dir /any/path --block-sweep 10,20,30,60,120`, `revision_figures.py` | committed caches only | byte-identical (the tex up to its `% Generated:` line) |
| `revision_results/cache/*.npz` | `revision_stats.py --base-dir <deposit>` with `cache/` absent | deposit audio | byte-identical (2026-08-29) |
| `reencode/banks/*.npy` | `reencode_zm1.py banks` | zm1_encoder | byte-identical |
| `reencode/cache/*.npz`, `results_*.json`, `validation.json`, `reencode_summary.csv` | `reencode_zm1.py factory`, `sweep`, `validate`, `summary` | deposit audio, committed banks | caches byte-identical; every numeric field identical (only `runtime_s` and `t_*_s` timings differ) |
| `reencode_bootstrap.csv`, `convention_*`, `reencode_variables.tex` | the three cache-driven scripts | committed caches | byte-identical (the tex up to its timestamp) |
| `figures/` Figs 3, 5, 6, 7, 8, 9, 10 | `render_ieee_figures.py` | `plots/*.csv`; deposit audio for Fig. 7 | byte-identical |
| `figures/` Fig. 4 | `render_ieee_figures.py 04` | contextily, geopandas, tile server | rendered on the authors' machine with matplotlib 3.10.8; not re-checked, tiles are fetched live |
| `plots/` Fig. 6 and 8-10 CSVs | `generate_all_figures.py` | deposit audio | byte-identical |
| `data/render_stats_all.csv`, `data/all_variables.tex` | `parse_render_stats.py`, `generate_latex_variables.py` | deposit render reports | byte-identical (the tex up to its timestamp); agrees with the deposit's `corpus_statistics.csv` on every value the manuscript uses |
| `dataset_card/SHA256SUMS.txt`, `splits.csv` | `scan_deposit.py`, `build_dataset_card.py` | deposit audio (254 s) | byte-identical; all 23 `metadata.yaml` files validate |

## License

Everything in this repository (code, frame-energy caches, tables, figures, dataset card): [Creative Commons Attribution 4.0 International License][cc-by]. The recordings themselves are licensed separately (CC BY-NC-SA 4.0, see [Recordings](#recordings)).

[![CC BY 4.0][cc-by-image]][cc-by]

[cc-by]: https://creativecommons.org/licenses/by/4.0/
[cc-by-image]: https://i.creativecommons.org/l/by/4.0/88x31.png

## Contact

Bartłomiej Mróz · bartlomiej.mroz@pg.edu.pl · Department of Multimedia Systems, Gdańsk University of Technology · [bmroz.eu](https://bmroz.eu)
