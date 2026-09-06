# Datasheet: A Seven-Year Corpus of Higher-Order Ambisonics Recordings

Deposit v1.2, concept DOI [10.34808/w8bx-2094](https://doi.org/10.34808/w8bx-2094) (Bridge of Data / Most Danych, Gdańsk University of Technology). Structure follows Gebru et al., "Datasheets for Datasets" (CACM 64(12), 2021). Companion paper: B. Mróz, S. Zaporowski, "A Seven-Year Higher-Order Ambisonics Recording Corpus: Dataset, Methodology, and a Co-Located Spherical Microphone Array Comparison", IEEE Access (under review). Analysis pipeline: [10.5281/zenodo.21789163](https://doi.org/10.5281/zenodo.21789163).

Contents: [1 Motivation](#1-motivation) · [2 Composition](#2-composition) · [3 Collection process](#3-collection-process) · [4 Preprocessing, cleaning, labelling](#4-preprocessing-cleaning-labelling) · [5 Uses](#5-uses) · [6 Distribution](#6-distribution) · [7 Maintenance](#7-maintenance). Appendices at the end: [A File hierarchy](#appendix-a-file-hierarchy) · [B Metadata schema](#appendix-b-metadata-schema) · [C Metadata inconsistencies](#appendix-c-known-metadata-inconsistencies-in-v12).

---

## 1 Motivation

**Purpose.** The corpus collects the B-format (spherical-harmonic) renders of 23 microphone-array recording sessions made between April 2019 and January 2026, mostly of live classical music in the Tricity area (Gdańsk, Sopot, Gdynia), Poland. It was assembled to give the spatial-audio community a body of natural, long-form, higher-order Ambisonics (HOA) material recorded under production conditions, and to support the paper's co-located comparison of three arrays. It sits between synthetic or impulse-response datasets and short-clip sound-event corpora: whole performances in real halls, some of them before an audience.

**Creators.** Bartłomiej Mróz (Department of Multimedia Systems, Gdańsk Tech), who did the recording, editing, rendering and metadata, and is the sole creator on the deposit record. Szymon Zaporowski is listed on that record as a project member, and is a co-author of the companion paper.

**Funding.** IDUB Argentum grant no. 20/1/2023/IDUB/I3b/Ag, Gdańsk Tech (manuscript Acknowledgment). The follow-up perceptual study is funded by NCN Miniatura grant no. 2026/10/X/ST7/00128.

## 2 Composition

### 2.1 What the instances are

An instance is a rendered B-format WAV file of one musical performance (or one continuous concert part) captured by one spherical array and encoded to one Ambisonics order. Instances are grouped into sessions (one venue, one date or consecutive dates, one programme). Sessions with more than one array ship parallel renders of the same performance; 2024-08-15 additionally ships the raw A-format masters.

All B-format files: ACN channel ordering, SN3D normalisation (AmbiX), 24-bit PCM, `.wav` extension throughout. The container varies with size and origin: 62 files under 4 GiB are ordinary RIFF WAV, and of the 12 above 4 GiB, six are RF64 and six are Sony Wave64. The Wave64 files are the 3OA and 5OA Spcmic renders of 2024-08-15 and 2026-01-18, among them the two largest files in the deposit. Code that accepts only RIFF and RF64 will fail on those six despite the `.wav` extension; FFmpeg, libsndfile and Audacity read all three containers.

### 2.2 Counts

| | value |
|---|---|
| Sessions | 23 (2019-04-12 to 2026-01-18) |
| Rendered B-format files | 74: 10 first-order (4 ch), 59 third-order (16 ch), 5 fifth-order (36 ch) |
| Rendered duration | 16 h 02 min (961.9 min) of files; 726.2 min of unique programme (parallel captures counted once) |
| Rendered size | 164.6 GB (153.3 GiB) |
| A-format masters | 6 files, 33.2 GB (30.9 GiB), 2024-08-15 only: ZM-1 20 ch, Spcmic 84 ch, SR-VRMIC 4 ch, all 48 kHz / 24-bit |
| Sample rate of renders | 67 files at 48 kHz, 7 files at 96 kHz (all seven are Spcmic renders: both pieces of 2024-08-15 in 3OA and 5OA, both orders of 2025-09-28, and the 3OA render of 2026-01-18) |
| Loudness of renders | LUFS-I from −35.31 to −15.34, mean −22.04, median −21.29 (`corpus_statistics.csv`) |
| Photographs | 176 images across all 23 `photos/` folders |

Sessions by venue (13 + 2 = 15 of 23 on the Gdańsk Tech campus):

| venue | sessions |
|---|---|
| Aula Politechniki Gdańskiej (Main Aula, Gdańsk Tech), Gdańsk | 13 |
| Hol przed Aulą (lobby in front of the Aula, Gdańsk Tech), Gdańsk | 2 |
| Kościół Świętej Trójcy (Holy Trinity Church), Gdańsk | 1 |
| Baltic Sea pier, Sopot (open air) | 1 |
| Polska Filharmonia Bałtycka (Baltic Philharmonic), Gdańsk | 1 |
| Fiqu Miqu Studio (recording studio), Gdynia | 1 |
| Kamieniołom Piechcin (quarry, open-air VR film set), Piechcin | 1 |
| Akademia Muzyczna im. S. Moniuszki, concert hall (aMuz), Gdańsk | 1 |
| Agrotourism barn with styrofoam cave film set, Jędrzejewo | 1 |
| Archikatedra Oliwska (Oliwa Cathedral), Gdańsk | 1 |

Sessions by `content.type`: solo_piano 8, choir 4, ensemble 2, vr_film_production 2, orchestra 1, choir_with_orchestra 1, choir_with_soloists 1, choir_with_ensemble 1, piano_duet 1, chamber 1, ambient 1. Six sessions were recorded with an audience present (150-550 people). Of the other 17, thirteen are concert halls without an audience; the rest are a recording studio, an open-air pier, a quarry and an indoor film set.

Sessions by array (a session counts for every array that has a render in it): Zylia ZM-1 21, Harpex Spcmic 4, RØDE NT-SF1 4, Saramonic SR-VRMIC 1. The primary array is the ZM-1 in 21 sessions and the Spcmic in 2 (2025-09-28, 2026-01-18). The figures here are counted from the files and agree with the equipment table in the deposit's `README.md`.

### 2.3 Is it a sample?

No. It is the complete set of the first author's spherical-array sessions from 2019-2026 for which distribution rights could be secured. Three items were withheld (listed in the deposit's `README.md`): the 2023-06-17 Gdańsk Tech courtyard choir/cabaret concert (repertoire under ZAiKS licensing), a 2023-08-06 piano-and-tenor session (performers' request), and one file of the 2022-06-27 session (`3OA_ZM1_PMykietyn-Prelude.wav`, composer's licensing restriction). The corpus is therefore a convenience collection, not a designed sample of venues or repertoire.

### 2.4 Labels and metadata

There are no time-aligned labels of any kind: no sound-event annotations, no source positions or trajectories, no transcripts, no onset/offset marks. Each session carries a `metadata.yaml` (schema in [Appendix B](#appendix-b-metadata-schema)) with venue, room acoustics (Aula PG only, from a 2023 impulse-response survey), equipment and placement, content, performers, repertoire, per-file loudness, and free-text notes; each rendered file has a REAPER `*.render_stats.html` loudness report; `corpus_statistics.csv` at the root tabulates duration, normalisation gain, peak, true-peak, LUFS-M/S/I and LRA for all 74 renders.

### 2.5 Missing information

- `metadata.yaml` keys are absent, never null, when a value was not recorded or is not applicable. [Appendix B](#appendix-b-metadata-schema) lists presence counts per key.
- The 2025-09-28 session's metadata is minimal (no acoustics, processing, quality, file durations or loudness).
- `normalization_db` in `corpus_statistics.csv` is empty for 48 of 74 files, because REAPER's render report only carries the applied gain in some versions: 21 reports name the column `Normalized/Adjusted` and 5 older ones `Post-render Gain`, while the remaining 48 reports have no gain column at all. An empty cell therefore records nothing about how a file was normalised, only that the report of the day did not print a gain. The grouping actually used is classified group by group in [4.2](#42-peak-normalisation-and-its-consequences), where 16 of these 48 files belong to groups that did not share a gain.
- The analog preamp gain of the Zoom F4 used for the SR-VRMIC in 2024-08-15 was not recorded.
- No absolute calibration (SPL) exists for any file.

### 2.6 Relationships between instances

Parallel renders of one performance are the same acoustic event through different arrays and encoders; they are identifiable by matching `<CONTENT>` tokens inside one session, allowing for a trailing index that one array's filename may carry and the other's may not (2024-12-10 pairs `ChopinRecital` with `ChopinRecital1`) (for example the eight renders of 2024-08-15, the ZM-1/NT-SF1 pairs of 2021-06-27, 2023-06-03, 2024-12-10 and 2025-02-05, the ZM-1/Spcmic pair of 2024-04-30, the Spcmic 3OA/5OA pairs of 2025-09-28 and 2026-01-18). Several files are segments of one continuous take (2022-04-21: six segments of one 3OA take; 2022-03-10 and 2023-10-12: two parts of one concert). See [`SPLITS.md`](SPLITS.md) for the consequences.

### 2.7 Recommended splits

`splits.csv` gives a session-level train/validation/test partition (16/4/3 sessions; 67.8/14.2/18.0 % by file duration) with the 2024-08-15 comparison session, one recording studio and one open-air session held out in test. [`SPLITS.md`](SPLITS.md) explains the rationale, the rule that all files of a session and every segment of one continuous recording stay in one partition, and the limited forms of venue- and microphone-independent evaluation the corpus allows.

### 2.8 Errors, noise, redundancies

- **Known sources of noise.** Audience noise, applause and incidental stage speech at the six audience sessions; HVAC and traffic in the hall sessions; wind and sea noise at Sopot; 360-degree camera fan noise in some 2022 sessions (the metadata notes describe the mitigation); an unrelated second ZM-1 unit was running next to the primary array in 2024-03-07, 2024-03-09 and 2024-08-15.
- **Edit boundaries.** The 2024-08-15 renders were cut on the project timeline rather than to a common acoustic window, so the Franck ends abruptly and the Prokofiev begins abruptly, and the renders of one piece are not sample-aligned with each other: on the Franck the Spcmic render begins 7.77 s earlier in real time, so a given musical moment sits 7.77 s later in its file, and on the Prokofiev the offset runs the other way by 7.92 s (measured by waveform cross-correlation; correlation at zero lag is 0.006 and -0.005, and 0.44 and 0.65 at those lags). Any analysis pairing the arrays in time must align them first, as the released pipeline does. The A-format masters do not have this problem: all six share one window per piece.
- **Clipping.** No rendered B-format file contains a full-scale sample: the highest sample peak across all 74 renders is −0.46 dBFS. The A-format SR-VRMIC masters of 2024-08-15 contain input clipping on the Zoom F4: Franck 4 full-scale samples on channel index 1; Prokofiev 164 on channel index 1 and 2 on channel index 2 (0-based indices; the session's `audio_a_format/AFORMAT_README.md` calls the same channels "channel 2" and "channel 3"), as flat-top runs, i.e. a few milliseconds in total. The rendered 1OA SR-VRMIC files show no full-scale samples because the encoder and the −0.5 dB group gain bring the level down; the clipped input is nevertheless present in them as distortion.
- **Silent channel.** ZM-1 A-format channel index 19 (the 20th channel) is digitally silent in both A-format files: the array has 19 capsules and the 20th channel is empty by design.
- **Level and loudness relations.** See [4.2](#42-peak-normalisation-and-its-consequences): absolute level relations between microphones and between sessions are not preserved.
- **Metadata inconsistencies.** [Appendix C](#appendix-c-known-metadata-inconsistencies-in-v12) lists the discrepancies known to remain in v1.2; those corrected in this version are listed in [6.3](#63-versions).

### 2.9 Self-contained?

Yes. All audio and metadata are in the deposit. The A-format README cites the Harpex Spcmic manual and the paper cites the room-acoustics MSc thesis (Król & Jankowski 2023, Gdańsk Tech), neither of which is needed to use the data.

### 2.10 Confidential, offensive or personal content

- The audio contains no confidential material. Incidental non-consented conversation between session participants occurred near the piece boundaries of the 2024-08-15 session. The six A-format masters are cropped to one shared window per piece that begins past it (`audio_a_format/AFORMAT_README.md`), and the B-format renders were cut to the musical pieces. The renders were cut on the project timeline before that shared window was derived, so three of the eight begin earlier than it: the 3OA and 5OA Spcmic renders of the Franck by 7.7 s, and the 3OA ZM-1 render of the Prokofiev by 4.5 s. The author has listened to those three leading sections; they carry a brief spoken recording cue and no part of the conversation. The complete uncropped masters are held privately by the authors.
- Speech: the corpus holds no dedicated speech. What spoken material there is comes from incidental, unannotated stage announcements at the live events and from production dialogue in the two VR-film sessions (2024-07-27, 2025-09-28).
- People: performers are named in `metadata.yaml` (pianists, violinist, conductors, the Gdańsk Tech Academic Choir, band members of 2023-12-07, ensemble Emigrah, organist); VR-session actors are anonymised by role. Performer permissions were obtained before publication (manuscript Acknowledgment: Piotr Pawlak, Mikołaj Sikała, Patryk Morgaś, Jan Staruch, Bartosz Wiśniewski, the Akademicki Chór Politechniki Gdańskiej and conductor Mariusz Mróz, Andrzej Szadejko, the Miejsce Słowa foundation, Emigrah) and cover the published form: the recordings, the naming of the performers in the deposit and the paper, and the accompanying photographs; reuse, including derivative works, is governed by the deposit license (CC BY-NC-SA 4.0).
- Audiences at the six concerts were not individually consented; they are audible only as crowd noise and applause.
- The `photos/` folders show venues and the performers and production crews who consented to the sessions' publication; the photos have been public since the first release.
- No demographic attributes are recorded.

## 3 Collection process

### 3.1 Acquisition

Sound was captured directly by the spherical arrays (no simulation, no derived data).

| array | capsules | native order | interface | sessions |
|---|---|---|---|---|
| Zylia ZM-1 (serial SM19DRXWS03100AR, one unit) | 19 MEMS on a rigid sphere | 3rd (16 ch) | USB 2.0, 20 ch (19 + 1 empty), 48 kHz / 24-bit | 21 |
| Harpex Spcmic (serial 01A3AB) | 84 MEMS | 5th (36 ch) | USB, 84 ch, 48-96 kHz / 24-32-bit | 4 |
| RØDE NT-SF1 | 4 condenser (tetrahedral) | 1st (4 ch) | analog, via audio interface | 4 |
| Saramonic SR-VRMIC | 4 electret (tetrahedral) | 1st (4 ch) | analog, via Zoom F4 recorder | 1 |

- **Gain structure.** The ZM-1 and Spcmic are USB MEMS arrays with no analog gain stage; both were captured at their default 0 dB digital gain in every session. The SR-VRMIC was recorded through a Zoom F4 analog preamp whose gain setting was not recorded.
- **Recording chain.** REAPER (versions 5.x-7.x) on a laptop; multi-microphone sessions combined USB arrays with conventional microphones through an Apogee Ensemble/Element 88 using separate laptops or macOS aggregate devices. Spcmic-primary sessions (2025-09-28, 2026-01-18) were captured in the manufacturer's Spcmic recording software. Real-time binaural monitoring on Beyerdynamic DT 770 Pro with head tracking.
- **Placement.** `metadata.yaml` gives height, distance and a placement description per session: 0.5-3.0 m from the source and 0.9-2.0 m high across the sessions that record it.
- **Clocks in the 2024-08-15 comparison session.** The three arrays ran on three independent free-running clocks: the ZM-1 in REAPER through a macOS aggregate device shared with a second, unrelated ZM-1; the Spcmic in the manufacturer app; the SR-VRMIC on the Zoom F4. The A-format files were aligned by FFT cross-correlation: start lag ≤ 0.6 ms; 6.6-9.9 ms of accumulated drift over the 988-1145 s aligned windows, i.e. about 7-9 ppm. The B-format renders of that session are not sample-synchronous either; the manuscript's comparison uses per-array statistics only and never combines arrays coherently. The 17 cm inter-array spacing on the shared bar adds up to about 0.5 ms of capture-position offset.
- **Room acoustics.** The Aula PG was measured in 2023 (ZM-1 + B&K 4292 omni source, log sweep, Aurora deconvolution): T30 1.97 s, EDT 1.92 s, C80 −1.8 dB, D50 27 %, and octave-band T30 from 2.28 s (125 Hz) to 1.06 s (8 kHz). These venue values are replicated in the 13 Aula `metadata.yaml` files. The aMuz hall carries C80/C50 only; other venues carry dimensions and audience data at most.

### 3.2 Who collected, when, and under what arrangements

All sessions were recorded by the first author, mostly as part of concert production, competition-application recordings, student theses and VR-film work for the performers and ensembles named in the metadata; the 2024-08-15 session was designed for the array comparison. Dates: 2019-04-12 to 2026-01-18 with no sessions between April 2019 and March 2021 (COVID-19 restrictions).

### 3.3 Ethics review

No ethics-board review was sought: the recordings are artistic performances made with the performers' permission ([2.10](#210-confidential-offensive-or-personal-content)), and the authors judged no review to be required.

## 4 Preprocessing, cleaning, labelling

### 4.1 A-to-B encoding (one converter version per array, corpus-wide)

| array | encoder | output |
|---|---|---|
| Zylia ZM-1 | ZYLIA Ambisonics Converter v1.7.0 (VST, Dec 2023); every ZM-1 session, including those recorded before 2023, was (re-)encoded with this version | 16 ch 3OA |
| Harpex Spcmic | Spacemic VST 1.0.2 alpha | 36 ch 5OA |
| Harpex Spcmic | Spcmic standalone app 0.9.1 beta | 16 ch 3OA |
| RØDE NT-SF1 | Audio Brewers ab Transcoder with anechoic impulse responses (model IRs; the first author contributed IRs of his unit) | 4 ch 1OA |
| Saramonic SR-VRMIC | Audio Brewers ab Transcoder with IRs of the first author's unit measured in an anechoic chamber | 4 ch 1OA |

Where a `metadata.yaml` `processing_chain` string says "Zylia Studio PRO/ZAM" (2023-06-03, 2023-12-07, 2024-04-30) the encoder is the same ZYLIA converter v1.7.0 as elsewhere (manuscript Section II). The encoders' filters and regularisation are proprietary and undisclosed; the A-to-B stage is part of the measured capture system. Hardware and encoder contributions cannot be separated in the B-format files; only the 2024-08-15 A-format masters allow re-encoding.

The 2024-04-30 Spcmic was captured as an 84-channel A-format stream in REAPER, which the standalone app cannot decode post hoc, so that session has a 5OA render only (manuscript Section IV footnote).

### 4.2 Peak normalisation and its consequences

- Rendered files are peak-normalised towards −0.5 dBTP, in most groups with one shared gain per (session × microphone) group across pieces, chosen so that the loudest piece of the group reaches −0.5 dBTP. Within such a group the relative loudness of the pieces is preserved, but absolute level relations between microphones and between sessions are not: a ZM-1 file and an NT-SF1 file of the same session, or two ZM-1 files from different sessions, cannot be compared in absolute level.
- Practice varied across the seven years, and the deposited peak values show which case applies to any group. Of the 16 groups holding more than one file, 9 show the shared-gain pattern. In eight of them exactly one file reaches −0.5; the ninth is the 2024-08-15 Spcmic group, where two files do, because the 3OA and 5OA renders of a piece share a peak and one gain of +12.0 dB was applied to all four. Four groups were normalised per file, so within-group loudness relations are **not** preserved there: 2022-04-21 ZM-1 (6 files), 2024-03-09 ZM-1 (2), 2025-09-28 Spcmic (2, recorded gains −0.5 and +1.7 dB) and 2026-01-18 Spcmic (2, recorded gains −0.5 and +9.4 dB). Two groups preserve their internal relations but were never scaled to the target: 2021-03-27 ZM-1 (loudest −0.8 dBTP) and 2024-03-07 ZM-1b (loudest −7.2 dBTP). In 2023-08-04 ZM-1 the two loudest pieces sit at exactly −0.50 while the other four spread from −5.4 to −15.8, which is consistent with a shared gain plus a ceiling at the target but cannot be settled from the deposited files. The 2024-08-15 comparison session follows the shared-gain case for all three arrays.
- Group gains applied in the 2024-08-15 comparison session: ZM-1 −0.5 dB, Spcmic +12.0 dB (the same +12.0 dB for the 3OA and the 5OA render), SR-VRMIC −0.5 dB. Other retained group gains (`corpus_statistics.csv`, column `normalization_db`): 2021-06-27 NT-SF1 +2.4 dB and ZM-1 +0.7 dB; 2023-06-03 NT-SF1 −0.2 dB and ZM-1 +1.9 dB; 2024-04-30 Spcmic 5OA +21.2 dB; 2024-12-10 NT-SF1 +1.7 dB; 2026-01-18 Spcmic 3OA −0.5 dB and 5OA +9.4 dB. The column is empty for the remaining files: an empty cell is a missing record of the gain, not a different normalisation method.
- LUFS-I, peak and LRA values in `corpus_statistics.csv`, the `*.render_stats.html` reports and `metadata.yaml` were measured on the normalised renders (ITU-R BS.1770-5). The `lufs_m_max` and `lufs_s_max` columns of the CSV do not reliably reproduce the momentary and short-term maxima in the render reports; use the reports where those matter.
- The `true_peak_db` column of `corpus_statistics.csv` equals `peak_db` in all 74 rows: it carries the sample peak, not an independently measured inter-sample true peak. Only the render reports that print a true-peak column hold a genuine true-peak figure. Treat the column as a sample peak.
- The A-format masters are not normalised (native capture level: ZM-1 peaks −20.7/−19.4 dBFS, Spcmic −16.3/−14.4 dBFS, SR-VRMIC 0.0 dBFS with the clipping described in [2.8](#28-errors-noise-redundancies)).

### 4.3 Editing

Pieces were cut from continuous session takes in REAPER at piece boundaries. Nothing else was edited: every render is a single continuous performance, with no comping, retakes, equalisation, dynamics processing, noise reduction or de-clipping applied to any corpus file. The 2024-08-15 A-format files were cropped to a shared per-piece window to line the three devices up and to keep out the incidental conversation that cutting to the pieces had already kept out of the B-format renders ([2.10](#210-confidential-offensive-or-personal-content)); the `bext` TimeReference of the ZM-1 and SR-VRMIC files was advanced by the number of trimmed samples, other provenance chunks are verbatim.

### 4.4 Container fix in v1.2

In deposit v1.1 the two Spcmic A-format files (`AFORMAT_Spcmic_*.wav`, 13.9 GB and 11.9 GB) were written with a `RIFF` tag plus a `ds64` chunk, and a `RIFF` tag with its 32-bit size field makes libsndfile-based readers (Python `soundfile`, Audacity, MATLAB `audioread`) stop without an error after the first 4 GiB, i.e. after about 355 s of the 84-channel 48 kHz 24-bit stream; ffmpeg reads both variants in full. v1.2 replaces both files with standard `RF64` (tag `RF64`, size field 0xFFFFFFFF, `ds64` chunk) and identical audio bytes. The checksums in `SHA256SUMS.txt` are those of the v1.2 files.

### 4.5 Labelling

No labelling was performed. Metadata was written by the first author from session notes, REAPER projects and the loudness reports; the venue acoustics come from the Król & Jankowski thesis.

### 4.6 Raw data availability

The raw A-format captures are archived by the authors for every session and published only for 2024-08-15 (six files).

## 5 Uses

### 5.1 Already used for

- The companion IEEE Access paper (array comparison, corpus statistics; under review) and the earlier [AES Copenhagen 2026 paper](https://aes2.org/publications/elibrary-page/?id=23166) on the same comparison session.
- Training data for a neural Ambisonics-to-binaural renderer ([Zaporowski and Mróz 2026](https://aes2.org/publications/elibrary-page/?id=23351), AES AVARIG 2026): 1,555 paired Ambisonics-binaural files (~9,300 five-second segments), about 62 % of that model's training material, were cut from this corpus.
- Produced versions of nine sessions were released on YouTube, HOAST, streaming services or as a livestream (`publication_platforms` in `metadata.yaml`).

### 5.2 Recommended uses

- Spatial-audio rendering and decoding research needing long natural HOA scenes (binaural rendering, decoder design, order-truncation studies using the five 5OA files, loudspeaker-array evaluation).
- Stimulus material for perceptual studies (the funded NCN follow-up uses the parallel captures of 2024-08-15).
- Encoder research: re-encoding the 2024-08-15 A-format masters with open, adjustable encoders to separate hardware from encoder effects; the released pipeline provides frame-level per-order energies and annotated ZM-1/Spcmic difference files for the same session.
- Room-acoustics work in the Aula PG, where measured parameters and 13 sessions of programme coexist.
- Self-supervised or generative audio modelling where unlabelled multichannel music is the point, subject to the licence ([6.1](#61-licence)) and the biases below.
- Education and production reference for HOA capture.

### 5.3 Uses the corpus is unsuitable for

- **Sound event localisation and detection (SELD)** and any task needing event labels or source trajectories: there are none.
- **Speech, ASR, speaker or dialogue research**: no dedicated speech; the only spoken content is incidental unannotated stage announcements and the VR-production dialogue of two short sessions (3.2 + 4.5 min of files).
- **Absolute-level, SPL or calibrated-gain work**: peak normalisation removed inter-session and inter-microphone level relations; the SR-VRMIC preamp gain is unknown; no calibration signals exist.
- **Sample-synchronous multi-array processing** on 2024-08-15 (beamforming across arrays, coherent fusion): three free-running clocks, 6-10 ms drift per piece.
- **Genre-general music models**: repertoire is Western classical, mostly solo piano and choral; jazz, amplified and non-Western material is marginal (one pop-covers ensemble, one folk band, one choir-with-big-band concert).
- **Microphone-unit statistics**: one physical unit per array model.
- **Commercial use of any kind**, including training models that are themselves commercial products ([6.1](#61-licence)).

### 5.4 Known biases that affect downstream results

- **Venue concentration.** 15 of 23 sessions (62 of 74 files) are on the Gdańsk Tech campus, 13 of them (59 files) in one hall (Aula PG, T30 about 2 s). Hall diversity is dominated by a single room, and venue and repertoire are partially confounded (the studio holds the folk band, the cathedral holds carols).
- **Genre and instrument.** Solo piano (8 sessions, 35 files; 39 with the piano duet) and choir (8 sessions counting the choir-with-* types and the 2019 passion concert, 26 files) dominate; the same Steinway D (serial D560633) is the piano in every Aula piano session; three pianists account for all solo-piano sessions.
- **Single ZM-1 unit** (SM19DRXWS03100AR) in 21 of 23 sessions, with one encoder version: any ZM-1-specific colouration is a corpus-wide constant.
- **Order imbalance.** 59 of 74 files are 3OA; 5OA exists in five files from four sessions; 1OA exists only as a secondary array's parallel render.
- **Temporal.** There are no sessions between 2019-04 and 2021-03, and the session count peaks in 2022-2024.
- **Geographic**: all venues are in Poland, all but two within 30 km of Gdańsk.

## 6 Distribution

### 6.1 Licence

- **Audio, photographs and metadata: CC BY-NC-SA 4.0** (`LICENSE.txt`). This excludes commercial use and requires share-alike: any adapted material (re-encodings, mixes, derived datasets, and, where a model or its outputs count as adapted material, those too) must be redistributed under the same licence. In practice this restricts industry machine-learning training and any use inside a commercial product or service. Attribution to the authors and a link to the DOI are required.
- **Analysis pipeline (code, caches, figures): CC BY 4.0** (GitHub/Zenodo repository), attribution only.
- The performed works are separately subject to their composers' rights; one file and one session were withheld for that reason, and a second session at the performers' request ([2.3](#23-is-it-a-sample)). Reusers who publish derived audio remain responsible for the underlying musical rights.

### 6.2 Where and how

- Deposit: Bridge of Data, Gdańsk University of Technology, concept DOI 10.34808/w8bx-2094 (resolves to the latest version). Download as a directory tree or the repository's ZIP.
- Pipeline: DOI [10.5281/zenodo.21789163](https://doi.org/10.5281/zenodo.21789163); development history at [git.pg.edu.pl/p829296/hoa-corpus-ieee-access](https://git.pg.edu.pl/p829296/hoa-corpus-ieee-access), mirror at [github.com/mormegil6/hoa-corpus-ieee-access](https://github.com/mormegil6/hoa-corpus-ieee-access).
- Companion AES analysis: [github.com/mormegil6/hoa-mic-comparison-aes2026](https://github.com/mormegil6/hoa-mic-comparison-aes2026).
- Integrity: `SHA256SUMS.txt` (this folder) lists the SHA-256 of all 80 audio files with paths relative to the deposit root; verify by running `shasum -a 256 -c dataset_card/SHA256SUMS.txt` from the deposit root.

### 6.3 Versions

| version | content | what changed |
|---|---|---|
| v1.0 | 23 sessions, 74 B-format renders, `metadata.yaml`, `*.render_stats.html`, `photos/`, `corpus_statistics.csv`, README, LICENSE | initial release, 10 April 2026 (version DOI 10.34808/5xe2-ah94) |
| v1.1 | as v1.0 plus `sessions/2024-08-15_.../audio_a_format/` (6 A-format masters and their README) | A-format masters added for the comparison session; the two Spcmic files carried a `RIFF` tag with a `ds64` chunk ([4.4](#44-container-fix-in-v12)). Released 4 August 2026 (version DOI 10.34808/z4h6-sj32) |
| v1.2 | as v1.1 with the two `AFORMAT_Spcmic_*.wav` rewritten as `RF64`, plus `dataset_card/` (this datasheet, `metadata_schema.json`, `splits.csv`, `SPLITS.md`, `SHA256SUMS.txt`) | container fix (same audio bytes) and documentation added, plus the metadata corrections listed below |

Each version has its own DOI; 10.34808/w8bx-2094 is the concept DOI and always resolves to the latest version, and is the one to cite for the corpus as a whole.

Metadata corrected in v1.2, none of it affecting audio: the five 2021-06-27 `3OA_ZM1_*` entries carried pre-normalisation `lufs_i` and `true_peak_db` (0.7 dB low, the ZM-1 group gain) and the 1OA entries lacked `true_peak_db`, all now taken from `corpus_statistics.csv`; `5OA_Spcmic_ChristmasCarolsConcert.wav` was recorded as 96 kHz when the file is 48 kHz; the 2025-09-28 `duration_minutes` read 5 against a 2.26-minute programme, now 2.3; the 2024-03-09 `quality.lufs_i_range` lower bound read −15.81 against a file value of −15.9; the `genre` vocabulary held two spellings of two labels, normalised to `classical_choral` and `classical_contemporary`; `rendered_files_size_gb` was recomputed as decimal GB (10^9 bytes) with the basis now stated, since the old values were inconsistent and in two sessions (2022-06-27, 2023-02-21) stale rather than merely mis-united; the session identifier was unified so that `metadata.yaml` `session_id` equals the session directory name, `corpus_statistics.csv` gained a `session_dir` column carrying the same key, and `splits.csv` dropped its now-redundant `metadata_session_id` column; and the equipment-table session counts and bit-depth line in the deposit's `README.md` were corrected ([2.2](#22-counts)).

Citation (from the deposit's `README.md`):

```bibtex
@dataset{mroz2026hoa,
  author    = {Mróz, Bartłomiej},
  title     = {A Seven-Year Corpus of Higher-Order Ambisonics Recordings},
  year      = {2026},
  publisher = {Gdańsk University of Technology},
  doi       = {10.34808/w8bx-2094}
}
```

### 6.4 Export controls and other restrictions

None known beyond the licence and the withheld items.

## 7 Maintenance

- **Contact.** Bartłomiej Mróz, bartlomiej.mroz@pg.edu.pl, Department of Multimedia Systems, Gdańsk Tech (as given in the deposit's `README.md`), sole long-term contact.
- **Hosting.** Bridge of Data, the Gdańsk Tech institutional research-data repository. The MOST Wiedzy Open Research Data Catalog that hosts it has been CoreTrustSeal-certified since 2023 and keeps published versions indefinitely.
- **Versioning.** New versions, including future sessions, appear under the same concept DOI with a version DOI each. Audio bytes never change silently: the v1.2 container fix is a new version for that reason. Errata go in the version table ([6.3](#63-versions)).
- **Deprecation.** Nothing deprecated. Performers consent before publication; a withdrawal would mean removal in a new version, noted here, with earlier versions retained by the repository.
- **Contributions.** Work derived from the corpus by others, such as re-encodings, annotation layers or alternative splits, is not merged into this deposit. Anyone producing such work can publish it themselves under the terms of the corpus licence ([6.1](#61-licence)) and contact the author to have a link added here.
- **Update cadence.** None promised.

---

## Appendix A: File hierarchy

```
<deposit root>/
├── README.md                     overview, citation, naming, exclusions
├── LICENSE.txt                   CC BY-NC-SA 4.0 text
├── corpus_statistics.csv         74 rows: session, filename, duration,
│                                 normalization_db, peak, true-peak, clips,
│                                 LUFS-M/S/I, LRA, stats file
├── dataset_card/                 (v1.2) this datasheet, metadata_schema.json,
│                                 splits.csv, SPLITS.md, SHA256SUMS.txt
└── sessions/
    └── YYYY-MM-DD_<venue-slug>_<content-slug>/      (23 directories)
        ├── metadata.yaml                             schema: [Appendix B](#appendix-b-metadata-schema)
        ├── audio/
        │   ├── <ORDER>_<MIC>_<CONTENT>.wav           1-10 renders per session
        │   └── <ORDER>_<MIC>_<CONTENT>.render_stats.html   one per render
        ├── audio_a_format/                           2024-08-15 only
        │   ├── AFORMAT_<MIC>_<CONTENT>.wav           6 files
        │   └── AFORMAT_README.md                    crop points, alignment,
        │                                             signal quality
        └── photos/                                   1-27 images (jpg/JPG/jpeg/png)
```

File-name tokens: `ORDER` ∈ {`1OA`, `3OA`, `5OA`}; `MIC` ∈ {`ZM1`, `ZM1b`, `Spcmic`, `NTSF1`, `SRVRMIC`} (`ZM1b` occurs only in 2024-03-07, see [Appendix C](#appendix-c-known-metadata-inconsistencies-in-v12)); `CONTENT` is Composer-Title (`CFranck-PreludeChoralFugue`), a concert part (`ChoirConcertPt1`) or a descriptive name (`SopotPier`). The session directory name is the identifier throughout: the `session_id` in `metadata.yaml` and `splits.csv`, the path prefix in `SHA256SUMS.txt`, and the `session_dir` column of `corpus_statistics.csv`. That CSV also keeps a `session` column with the author's original working-folder name (`2024.08.15 -- ZM1 Spcmic Saramonic`), the identifier used before v1.2.

Per-session file counts (renders / photos): 2019-04-12 1/2 · 2021-03-27 4/7 · 2021-06-27 10/5 · 2022-03-10 2/1 · 2022-03-25 1/4 · 2022-04-13 7/2 · 2022-04-21 6/15 · 2022-06-27 5/6 · 2023-02-21 1/8 · 2023-06-03 2/4 · 2023-08-04 6/5 · 2023-10-12 2/4 · 2023-12-07 1/3 · 2024-03-07 4/8 · 2024-03-09 2/8 · 2024-04-30 2/12 · 2024-07-27 1/17 · 2024-08-15 8/11 (+6 A-format) · 2024-12-10 2/27 · 2025-01-10 1/7 · 2025-02-05 2/8 · 2025-09-28 2/6 · 2026-01-18 2/6.

## Appendix B: Metadata schema

Machine-readable form: `metadata_schema.json` (JSON Schema 2020-12), derived by parsing all 23 files; every file validates against it. Presence is given as n/23 sessions. **Missing-value policy:** an absent key means "not recorded or not applicable"; no key is ever present with a null value; readers must treat absence as unknown, not as zero or false. Values are never empty strings. Types are YAML-native (`str`, `int`, `float`, `bool`, `list`, `dict`); where a key appears with two types both are listed.

Required (23/23): `session_id`, `duration_minutes`, `venue`, `equipment`, `recording_settings`, `content`, `files`, `rendered_files_count`, and one of `recording_date` / `recording_dates`.

### Top level

| key | type | unit / values | n/23 | notes; absent in |
|---|---|---|---|---|
| `session_id` | str | `YYYY-MM-DD_<venue-slug>_<content-slug>` | 23 | equals the session directory name |
| `recording_date` | str | ISO date | 21 | absent in 2021-03-27, 2022-04-13 (they carry `recording_dates`) |
| `recording_dates` | list[str] | ISO dates | 3 | multi-day sessions: 2021-06-27, 2022-04-13 |
| `duration_minutes` | float | min, unique programme | 23 | parallel captures counted once |
| `venue` | dict | | 23 | |
| `acoustics` | dict | | 22 | absent in 2025-09-28 |
| `acoustics_reference` | str | citation | 13 | all 13 Aula sessions |
| `equipment` | dict | | 23 | |
| `recording_settings` | dict | | 23 | |
| `content` | dict | | 23 | |
| `instruments` | list[str] | free text | 19 | absent in 2021-06-27, 2022-03-25, 2024-07-27, 2025-09-28 |
| `performers` | list[dict] | | 18 | absent in 2019-04-12, 2021-06-27, 2022-03-10, 2022-03-25, 2022-04-21 |
| `repertoire` | list[dict] | | 21 | absent in 2022-03-25, 2025-09-28 |
| `processing` | dict | | 22 | absent in 2025-09-28 |
| `files` | list[dict] | | 23 | one entry per render (A-format files not listed) |
| `rendered_files_count` | int | count | 23 | equals `len(files)` |
| `rendered_files_size_gb` | float | decimal GB (10^9 bytes) | 16 | absent in 2019-04-12, 2021-06-27, 2022-03-10, 2022-03-25, 2022-04-13, 2022-04-21, 2025-09-28 |
| `quality` | dict | | 21 | absent in 2024-04-30, 2025-09-28 |
| `is_published` | bool | always true when present | 9 | absent means no known public release |
| `publication_platforms` | list[dict] | | 9 | same 9 sessions as `is_published` |
| `photos_count` | int | count | 15 | every session has a `photos/` folder regardless |
| `notes` | str | free text | 21 | absent in 2022-06-27, 2025-09-28 |

### `venue`

| key | type | unit / values | n/23 |
|---|---|---|---|
| `name` | str | | 23 |
| `type` | str | `concert_hall` (17), `church` (2), `outdoor`, `recording_studio`, `outdoor_quarry`, `indoor_film_set` | 23 |
| `city` | str | Gdańsk (19), Sopot, Gdynia, Piechcin, Jędrzejewo | 23 |
| `country` | str | `Poland` | 23 |
| `url` | str | URL | 20 (absent 2019-04-12, 2022-03-25, 2025-09-28) |
| `coordinates` | list[float, float] | [lat, lon], WGS84 degrees | 23 |

### `acoustics` (22 sessions)

| key | type | unit | n/23 | notes |
|---|---|---|---|---|
| `audience_present` | bool | | 22 | true in 6 sessions |
| `audience_size` | int | persons | 6 | only when audience present |
| `room_length_m`, `room_width_m` | float/int | m | 16 | |
| `room_height_m` | float | m | 15 | |
| `seating_capacity` | int | seats | 14 | Aula 370, aMuz 441 |
| `rt60_T30_seconds`, `rt60_T20_seconds`, `rt60_EDT_seconds` | float | s | 13 | Aula only |
| `clarity_C80_dB`, `clarity_C50_dB` | float | dB | 14 | Aula + aMuz |
| `definition_D50_percent` | int | % | 13 | Aula only |
| `center_time_Ts_ms` | int | ms | 13 | Aula only |
| `lateral_energy_fraction_LEF` | float | 0-1 | 13 | Aula only |
| `direct_reverb_ratio_DRR_dB` | float | dB | 13 | Aula only |
| `diffuseness_early`, `diffuseness_late` | float | 0-1 | 13 | Aula only |
| `rt60_octave_bands` | dict{`125Hz`,`250Hz`,`500Hz`,`1kHz`,`2kHz`,`4kHz`,`8kHz`: float} | s | 13 | Aula only |

Sessions without any measured parameter: 2019-04-12, 2022-03-10, 2022-03-25, 2023-02-21, 2023-10-12, 2024-03-09, 2024-07-27, 2025-09-28, 2026-01-18 (2025-01-10 has C80/C50 only).

### `equipment`

| key | type | unit / values | n/23 | absent in |
|---|---|---|---|---|
| `primary_mic_model` | str | `Zylia ZM-1` (21), `Harpex Spcmic` (2) | 23 | |
| `primary_mic_serial` | str | | 22 | 2025-09-28 |
| `primary_mic_mount` | str | free text | 11 | 12 sessions |
| `primary_mic_height_m` | float | m | 22 | 2025-09-28 |
| `primary_mic_distance_source_m` | float | m | 20 | 2019-04-12, 2022-03-25, 2025-09-28 |
| `primary_mic_orientation` | str | free text | 21 | 2019-04-12, 2025-09-28 |
| `secondary_mics` | list[dict] | | 15 | 2019-04-12, 2021-03-27, 2022-06-27, 2023-02-21, 2023-08-04, 2023-10-12, 2024-07-27, 2025-09-28 |
| `secondary_mics[].model` | str | | 15 | required within entry |
| `secondary_mics[].purpose` | str | | 15 | |
| `secondary_mics[].notes` | str | | 5 | |
| `secondary_mics[].channels` | int or list[int] | count or interface input numbers | 7 | |
| `secondary_mics[].height_m` | float | m | 4 | |
| `secondary_mics[].processing` | str or list[str] | encoder used | 5 | |

`secondary_mics` includes devices whose signals are not in the corpus (spot microphones, stereo pairs, 360° cameras, the unrelated second Zylia unit); most entries that correspond to a corpus render name an A-to-B encoder under `processing`, but not all: the 2021-06-27 NT-SF1 entry has no `processing` key and ships five renders, so match by filename token rather than by this field.

### `recording_settings`

| key | type | unit / values | n/23 | absent in |
|---|---|---|---|---|
| `sample_rate_hz` | int | Hz: 48000 (21), 96000 (2) | 23 | |
| `bit_depth` | int | bits: 24 (22), 32 (1) | 23 | |
| `raw_channels` | int | 20 (21), 84 (1) | 22 | 2025-09-28 |
| `recording_software` | str | REAPER (21), Spcmic recording software (1) | 22 | 2025-09-28 |
| `daw` | str | REAPER | 22 | 2025-09-28 |

These describe the primary array's capture; render sample rates can differ ([Appendix C](#appendix-c-known-metadata-inconsistencies-in-v12)).

### `content`

| key | type | values | n/23 | absent in |
|---|---|---|---|---|
| `type` | str | `solo_piano` (8), `choir` (4), `ensemble` (2), `vr_film_production` (2), `orchestra`, `choir_with_orchestra`, `ambient`, `choir_with_soloists`, `choir_with_ensemble`, `piano_duet`, `chamber` | 23 | |
| `genre` | str | 12 distinct free-text labels | 22 | 2025-09-28 |
| `performers_count` | int | persons (VR sessions include extras) | 22 | 2022-03-25 |
| `purpose` | str | free text | 17 | 2019-04-12, 2021-06-27, 2022-03-10, 2022-03-25, 2022-04-21, 2025-09-28 |
| `conductor` | str | | 3 | elsewhere under `performers[]` |
| `ensemble` | str | | 3 | elsewhere under `performers[]` |

### `performers[]`, `repertoire[]`, `publication_platforms[]`

| key | type | unit / values | notes |
|---|---|---|---|
| `performers[].name` | str | | required; ensembles and anonymised roles ("2 actors") also appear here |
| `performers[].role` | str | | 35/35 entries |
| `performers[].affiliation` | str | | 2023-12-07 only |
| `repertoire[].title` | str | | required; concert sessions list all pieces although they ship one file |
| `repertoire[].composer` | str | may include "arr. ..." | 93/104 entries |
| `repertoire[].duration_minutes` | float/int | min | 44/104 entries |
| `repertoire[].performer` | str | soloist for that piece | 2019-04-12 only |
| `repertoire[].notes` | str | | 2019-04-12 only |
| `publication_platforms[].platform` | str | | required |
| `publication_platforms[].url` | str | URL | 12/16 entries |
| `publication_platforms[].date` | str | `YYYY`, `YYYY-MM` or `YYYY-MM-DD` | 11/16 entries |
| `publication_platforms[].notes` | str | | 14/16 entries |

### `processing` (22 sessions)

| key | type | values | n/23 | notes |
|---|---|---|---|---|
| `ambisonics` | bool | true | 22 | |
| `ambisonics_order` | int | 3 (18), 5 (1) | 19 | single-order sessions |
| `ambisonics_orders` | list[int] | [3,1] or [3,5] | 3 | 2021-06-27, 2023-06-03, 2024-04-30 |
| `ambisonics_channels` | int or list[int] | 4, 16, 36 | 22 | list form in the three multi-order sessions |
| `processing_chain` | str or dict{device: str} | encoder description | 15 | dict form in 2023-06-03 (`ZM-1`, `NT-SF1`, `competition`) and 2024-04-30 (`ZM-1`, `Spcmic`) |

### `files[]` (74 entries)

| key | type | unit / values | entries | notes |
|---|---|---|---|---|
| `filename` | str | `<ORDER>_<MIC>_<CONTENT>.wav` | 74 | required |
| `duration_minutes` | float | min, one decimal | 72 | absent for 2025-09-28 |
| `channels` | int | 4, 16, 36 | 20 | otherwise implied by ORDER |
| `ambisonics_order` | int | 1, 3, 5 | 8 | otherwise implied by ORDER |
| `microphone` | str | | 6 | otherwise implied by MIC |
| `lufs_i` | float | LUFS, on the normalised render | 72 | absent for 2025-09-28 |
| `true_peak_db` | float | dBTP | 64 | absent for the 10 files of 2024-08-15 and 2025-09-28 |
| `lra` | float | LU | 64 | absent for 2024-08-15, 2025-09-28 |
| `sample_rate_hz` | int | Hz | 2 | 2026-01-18 only |
| `notes` | str | | 13 | |

### `quality` (21 sessions)

| key | type | unit / values | n/23 | notes |
|---|---|---|---|---|
| `peak_normalization_dbtp` | float | dBTP, always −0.5 | 19 | absent in 2021-06-27, 2023-06-03 (whose `notes` state it), 2024-04-30, 2025-09-28 |
| `lufs_i_range` | list[float, float] | LUFS | 19 | element order inconsistent ([max,min] in most, [min,max] in some) |
| `lufs_i_average` | float | LUFS | 19 | |
| `dynamic_preservation` | bool | true | 20 | |
| `clipping_detected` | bool | false | 21 | refers to renders only |
| `quality_rating` | str | `excellent` | 21 | author's rating, not a measured quantity |
| `notes` | str | | 21 | |

## Appendix C: Known metadata inconsistencies in v1.2

Found while deriving the schema and cross-checking against the files and `corpus_statistics.csv`. None affects the audio. Items corrected in v1.2 are listed in [6.3](#63-versions); the four below are still present and are documented rather than changed.

1. **2024-08-15 Spcmic renders** (3OA and 5OA, both pieces) are 96 kHz although the session's `recording_settings.sample_rate_hz` is 48000 and the Spcmic A-format masters are 48 kHz; the Spcmic tools rendered at 96 kHz. The ZM-1 and SR-VRMIC renders of the session are 48 kHz, so resample before any cross-array comparison that assumes equal rates. The session's `metadata.yaml` carries a note stating the render rates.
2. **2025-09-28** has no `acoustics`, `processing` or `quality` section and no per-file durations or loudness, because the session was a short VR production shoot rather than a music recording.
3. **2024-03-07**: the files are named `3OA_ZM1b_*` while `equipment` names the usual ZM-1 (SM19DRXWS03100AR) as primary and a "Zylia (experimental unit)" as secondary. `ZM1b` denotes the primary ZM-1; the experimental second unit's recordings were not published. The filenames are kept as published so that paths and checksums from earlier versions stay valid.
4. **`corpus_statistics.csv`**: the `lufs_m_max` and `lufs_s_max` columns are wrong for 69 of the 74 files (the report parser shifted columns: `lufs_m_max` holds the short-term maximum and `lufs_s_max` the LRA). `lufs_i`, `peak_db`, `true_peak_db`, `normalization_db`, `lra` and the durations are right, and no published statistic uses the two affected columns. The corrected table is `data/render_stats_all.csv` in the analysis repository; the two 2025-09-28 Spcmic `lufs_i` values there carry two decimals (−22.45, −25.22) where this file rounds to one.
