# Revision results - bootstrap uncertainty analysis

Outputs of [`../pyscripts/revision_stats.py`](../pyscripts/revision_stats.py), the uncertainty estimates of the IEEE Access corpus paper's microphone-comparison results.

## Resampling design

Each recording of the co-located session (2024-08-15) is streamed in 1-second frames and the per-frame, per-channel sum of squares is cached. Because all three arrays recorded the same performance simultaneously, frames are paired across arrays by wall-clock time: a bootstrap replicate resamples the *same* frame indices for both arrays of a pair, so the programme-level variance shared by both cancels and the resulting interval reflects the between-array difference alone.

Resampling uses a moving-block bootstrap (30-second blocks, 2000 replicates, fixed seed 2026), which respects the strong temporal correlation of musical material. An i.i.d. frame bootstrap would badly understate the interval. Every rolloff estimate carries its percentile 95% CI and its bootstrap standard error (SD of the replicates); the block length is a command-line option (`--block-seconds`) and the sensitivity of the intervals to it is tabulated below. Per-order levels are recomputed per replicate using the linear mean of per-channel RMS within each Ambisonics order, the same definition used in the companion AES Copenhagen paper's [`analyze_paper.py`](https://github.com/mormegil6/hoa-mic-comparison-aes2026/blob/main/analyze_paper.py) (`order_energies_dbfs`), so point estimates match to the last decimal.

**Scope**: these intervals quantify the within-recording temporal variability of each estimate (how much it moves when 30-s stretches of this one performance are resampled) and nothing else. They carry no information about other venues, sessions, performances, source types or distances, or physical units (the levels are dBFS of peak-normalized renders, not calibrated SPL).

## Files

| File | Contents |
|---|---|
| [`spatial_energy_two_piece.csv`](spatial_energy_two_piece.csv) | Per-order dBFS with 95% CIs, every array x both pieces |
| [`rolloff_bootstrap.csv`](rolloff_bootstrap.csv) | 0th-to-3rd rolloff per array and the paired between-array difference, each with 95% CI and bootstrap SE |
| [`block_sensitivity.csv`](block_sensitivity.csv) | The same rolloff CIs (with width and SE) at 10/20/30/60/120-s block lengths (`--block-sweep`) |
| [`directional_ci.csv`](directional_ci.csv) | W level (`W_dBFS`, 20 log10 of the W RMS) and X/Y/Z-over-W ratios with 95% CIs, both pieces; the ratios are linear RMS-amplitude ratios of ACN channels 3/1/2 to channel 0, not energy ratios |
| [`revision_stats_variables.tex`](revision_stats_variables.tex) | `\newcommand` macros consumed by the manuscript |
| `frame_order_energies_<key>.csv` | Frame-level per-order dBFS for each recording |
| `frame_difference_3OA_<piece>.csv` | Annotated frame-level ZM-1 vs Spcmic difference file (per order) |
| [`aformat_alignment.csv`](aformat_alignment.csv) | Inter-device alignment of the deposited A-format captures: raw leading offsets, shared-window crop points, post-trim verification lags and the implied clock-rate difference. Documented values transcribed from the deposit's `audio_a_format/AFORMAT_README.md`, not a pipeline output (see [A-format alignment data](#a-format-alignment-data)) |
| [`figures/`](figures/) | Two-piece Fig. 9 and Figs 10a/10b (Franck rows of `directional_ci.csv`) rendered with CI whiskers |
| `cache/frames_<key>.npz` | Per-frame per-channel energy caches (see [Reproducing without the audio](#reproducing-without-the-audio)) |
| [`reencode/`](reencode/) | Open re-encoding of the ZM-1 A-format: FIR banks, frame caches, sweep results, bootstrap CIs, LaTeX macros ([Open re-encoding of the ZM-1 A-format](../README.md#open-re-encoding-of-the-zm-1-a-format) in the root README; column semantics of its bootstrap table under [Re-encoding bootstrap table](#re-encoding-bootstrap-table)) |
| [`SHA256SUMS`](SHA256SUMS) | Checksums of the caches, of every CSV/tex output here, of `reencode/` and of `figures/` |

## Headline numbers

The paired differences are the quantities the manuscript cites.

| Quantity | Point estimate | 95% CI |
|---|---|---|
| ZM-1 rolloff 0->3, Franck | 27.4 dB | 27.0-28.3 (SE 0.33) |
| ZM-1 rolloff 0->3, Prokofiev | 26.0 dB | 25.4-27.1 (SE 0.44) |
| Spcmic (3OA) rolloff 0->3, both pieces | 8.4 / 8.5 dB | width < 0.1 dB |
| Paired difference, Franck | 19.0 dB | 18.6-19.9 (SE 0.33) |
| Paired difference, Prokofiev | 17.5 dB | 16.9-18.6 (SE 0.45) |

The paired rows of `rolloff_bootstrap.csv` use 1139 (Franck) and 976 (Prokofiev) frame pairs after the integer-frame alignment of the two renders (`pair_lag_frames` +8 / -8, `pair_r_at_lag` 0.968 / 0.979 against `pair_r_at_zero` 0.408 / 0.354); see [Frame alignment](#frame-alignment).

## Frame alignment

The ZM-1 and Spcmic renders of a piece do not start at the same instant, so `revision_stats.py` aligns them by an integer-frame lag before pairing; the lag, the correlation at the lag and at lag 0 are written to `rolloff_bootstrap.csv` and to the `\PairLag<piece>` / `\PairCorr<piece>` macros. The procedure, its residual (below one 1-s frame) and the columns of the paired files are described under [Frame-level difference files](#frame-level-difference-files). The sub-millisecond alignment of the deposited *A-format* captures is a separate matter, documented in [`aformat_alignment.csv`](aformat_alignment.csv).

## Block-length sensitivity

`--block-sweep 10,20,30,60,120` repeats the rolloff bootstraps at each block length, every one from a fresh generator with the same seed, and writes `block_sensitivity.csv` plus `\Rolloff...Width<N>s` macros. 95% CI widths in dB:

| Block length | 10 s | 20 s | 30 s | 60 s | 120 s |
|---|---|---|---|---|---|
| Paired difference, Franck | 1.16 | 1.28 | 1.30 | 1.33 | 1.25 |
| Paired difference, Prokofiev | 1.37 | 1.57 | 1.72 | 1.81 | 1.74 |
| ZM-1 rolloff, Franck | 1.19 | 1.15 | 1.31 | 1.37 | 1.28 |
| ZM-1 rolloff, Prokofiev | 1.41 | 1.59 | 1.69 | 1.77 | 1.68 |

The widths grow with block length up to 60 s (the ZM-1 Franck row dips at 20 s), so 10-s blocks still understate the dependence; at 30 s the paired intervals are within 0.1 dB of the widest (60-s) value for both pieces (0.03 dB Franck, 0.09 dB Prokofiev). With 120-s blocks a replicate draws only 9-10 blocks from a 16-19 min recording, so the percentile bounds themselves become noisy. The 30-s row reproduces `rolloff_bootstrap.csv` exactly.

## Reproducing without the audio

The `cache/*.npz` frame-energy caches are committed (~1.1 MB total), so the bootstrap, the derived CSVs, and the figures can be regenerated without downloading the ~38 GB of session audio. Re-running `revision_stats.py` reuses any cache it finds and only streams WAV files whose cache is missing:

```sh
python3 ../pyscripts/revision_stats.py --base-dir /any/path --block-sweep 10,20,30,60,120   # caches present -> no audio read
python3 ../pyscripts/revision_figures.py   # figures/, byte-identical in the environment below
```

The committed outputs were produced with Python 3.14.7 and the exact package versions in [`../requirements-lock.txt`](../requirements-lock.txt) (numpy 2.5.2, scipy 1.18.1, soundfile 0.14.0, matplotlib 3.11.1), the `pip freeze` of a fresh `python3.14 -m venv` built from [`../requirements.txt`](../requirements.txt). Checked 2026-09-06 in such a venv: with `cache/*.npz` copied into `<out>/cache/`, `revision_stats.py --base-dir /nonexistent --out <out> --block-sweep 10,20,30,60,120` reproduced all 14 pipeline-written CSV files here byte-for-byte and `revision_stats_variables.tex` up to its `% Generated:` timestamp line, and `revision_figures.py` reproduced the three PNGs under `figures/` byte-for-byte. `SHA256SUMS` covers the caches, every CSV/tex output here, `reencode/` and `figures/`:

```sh
sha256sum -c SHA256SUMS      # macOS without coreutils: shasum -a 256 -c SHA256SUMS
```

To rebuild the caches from the audio, delete `cache/` and pass the deposit root as `--base-dir` (download from [doi.org/10.34808/w8bx-2094](https://doi.org/10.34808/w8bx-2094); the audio is read from `sessions/2024-08-15_aula-pg_solo-piano-mic-comparison/audio/`). Rebuilding all eight caches from the deposit on 2026-08-29 gave `cache/*.npz` byte-identical to the committed ones.

## Frame-level difference files

`frame_difference_3OA_<piece>.csv` gives, for every 1-second frame, the per-order dBFS of the ZM-1 and the Spcmic and their difference. The result is an annotation of the matched-capture space (both arrays, identical performance, co-located 17 cm apart on a shared bar) that machine-learning work can use without audio-level preprocessing.

Columns: `t_start_s` (start of the ZM-1 frame, seconds into the ZM-1 render); `zm1_frame` and `spcmic_frame` (the 1-s frame indices that were paired); `zm1_orderN_dBFS` and `spcmic_orderN_dBFS` (per-order level of each array in the frame, per-channel-mean convention of the paper, dBFS of the normalized render); `diff_orderN_dB` = `zm1_orderN_dBFS` - `spcmic_orderN_dBFS`.

Alignment: the two renders of a piece were exported from separate projects and do not start at the same instant. `revision_stats.py` therefore estimates an integer-frame lag by cross-correlating the per-frame W-channel log energy of the two renders over -15..+15 frames and pairs ZM-1 frame `i` with Spcmic frame `i + lag` (Franck: lag +8, r = 0.97 at the lag versus 0.41 at lag 0; Prokofiev: lag -8, r = 0.98 versus 0.35). The lag is written to `rolloff_bootstrap.csv` (`pair_lag_frames`, `pair_r_at_lag`, `pair_r_at_zero`) and to the tex macros `\PairLag<piece>` / `\PairCorr<piece>`. The residual misalignment is below one frame (1 s); no sub-frame alignment is attempted, and the correlation at the integer lag (0.97 / 0.98) is the measure of the residual. Only full-length frames of both renders are paired (the trailing partial frame is dropped).

These are paired inter-array difference measurements between two capture systems, not ground truth: neither array is a calibrated reference for the sound field, so the sign of a difference says which system delivered more energy to that order, not which one is correct. Frames at the edges of the overlap where one render has not yet started are absent by construction.

## A-format alignment data

`aformat_alignment.csv` transcribes, one row per piece and device, the inter-device alignment of the six deposited A-format captures from the deposit's `audio_a_format/AFORMAT_README.md`; it is documentation, not a pipeline output, and no value in it is computed here except the last column. The ZM-1 is the reference device. Columns: `raw_leading_offset_s` is how much earlier the device's own master starts than the ZM-1 master (positive = more leading material; it equals `crop_start_s` minus the ZM-1's `crop_start_s`); `crop_start_s` / `crop_end_s` are the shared-window crop points in each device's own master timeline (`crop_end_s` empty and `tail_untrimmed` = 1 where the Spcmic's own file end defines the window); `frames_kept` and `duration_s` are the deposited files' lengths; `verify_start_lag_ms` / `verify_end_lag_ms` and the `_r` columns are the lags and correlation coefficients of the deposit's post-trim check between the ZM-1 and the device on 10-s excerpts near the start and the end of the window; `clock_rate_diff_ppm` is the derived relative clock-rate difference, `verify_end_lag_ms` divided by the window length (`crop_end_s` minus `crop_start_s` of the ZM-1); it is approximate, since the exact excerpt positions are not documented. All devices ran at 48 kHz on free-running clocks.

## Re-encoding bootstrap table

`reencode/reencode_bootstrap.csv`, written by [`../pyscripts/reencode_bootstrap.py`](../pyscripts/reencode_bootstrap.py), has three kinds of row, distinguished by `kind`:

- `single`: one row per `config` (the six open encoders, `factory`, and the corpus Spcmic 3OA render as `Spcmic3OA_corpus`) and `piece`. `order0_dBFS`..`order3_dBFS` are the per-order levels over all frames (`n_frames`), `rolloff_0_3_dB` their 0th-minus-3rd difference, `ci_lo`/`ci_hi`/`bootstrap_se` the percentile 95% CI and bootstrap SE of that rolloff from `replicates` moving-block replicates of `block_s`-second blocks over the `n_full_frames` full-length frames (seed `seed`); `cache` is the frame cache read, relative to `reencode/`.
- `paired_vs_Spcmic3OA`: one row per open encoder and `factory`, per piece. `offset_frames` is the integer lag that maximises the cross-correlation of the per-frame W-channel log energies against the Spcmic 3OA cache (`xcorr_peak` at that lag, `xcorr_second`/`xcorr_second_lag` the runner-up, `xcorr_table` the whole `lag:r` list over -10..+10); `unambiguous` is true when the peak exceeds 0.9 and beats the runner-up by more than 0.05. Only then are `n_paired_frames`, `delta_pt_dB` (ZM-1 rolloff minus Spcmic rolloff on the aligned frames), `ci_lo`/`ci_hi`/`bootstrap_se` (paired bootstrap, same block design) and `zm1_rolloff_aligned_dB`/`spcmic_rolloff_aligned_dB` filled; `delta_fullrange_dB` is the difference of the two full-range single-array rolloffs and is filled for every row. Rows without an unambiguous lag carry the reason in `reason`.
- `INFORMATIONAL_ambiguous_lag_do_not_cite`: for each ambiguous case, the paired bootstrap at each of the two competing lags, so a reader can see how far apart they are. These rows document the ambiguity and must not be quoted as results.

`ci_source` says where the interval comes from: `rolloff_bootstrap.csv` for the factory and Spcmic reference rows, whose intervals are those of `rolloff_bootstrap.csv` in this directory (one committed interval per quantity), and `this script` for the open encoders. All levels are dBFS of the deposited files under the per-channel-mean convention of the paper; differences are in dB.

