#!/usr/bin/env python3
"""Streaming ZM-1 re-encoding pipeline + regularization sweep.

Usage:
    export HOA_CORPUS_DIR="/path/to/deposit"           # root holding sessions/
    export HOA_ARRAY_CAL_DIR="/path/to/hoa-array-cal"   # checkout providing zm1_encoder
    python reencode_zm1.py banks        # build + save the six FIR banks
    python reencode_zm1.py validate     # streaming vs validate.apply_fir_bank, 60 s Franck
    python reencode_zm1.py factory      # frame caches + levels for the factory (Zylia Ambisonics Converter) renders
    python reencode_zm1.py sweep        # 6 configs x 2 pieces
    python reencode_zm1.py sweep tikhonov,mmse_20 Franck    # subset of configs / pieces
    python reencode_zm1.py summary      # write reencode_summary.csv from the results JSON

--out (default revision_results/reencode/) receives banks/, cache/ and the
JSON/CSV results; --corpus-dir overrides HOA_CORPUS_DIR. `banks` and `summary`
need no audio; `validate`, `factory` and `sweep` read the deposit's 2024-08-15
session (audio_a_format/AFORMAT_ZM1_*.wav and audio/3OA_ZM1_*.wav). Only
`banks` and `validate` import the zm1_encoder package (HOA_ARRAY_CAL_DIR);
`factory`, `sweep` and `summary` work from the committed banks/ alone. Paths in
the JSON/CSV outputs are relative to --out and to the deposit root.

No B-format audio is ever written; the encoded output is streamed through an
overlap-add FFT convolver and reduced to per-1-s-frame per-channel sums of
squares, cached in the exact npz layout of revision_stats.py::build_frame_cache.
"""
from __future__ import annotations

import argparse
import hashlib
import csv
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import scipy.fft as sfft
import soundfile as sf

REPO_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_DIR / "revision_results" / "reencode"
COMMITTED_CACHE = REPO_DIR / "revision_results" / "cache"
# simulated per-capsule noise PSD the MMSE bank regularizes against (committed, so the
# banks can be rebuilt without the hoa-array-cal data/ directory)
NOISE_PSD_PATH = DEFAULT_OUT / "banks" / "capsule_noise_psd_simulated.npy"


def load_encoder():
    """Import zm1_encoder (hoa-array-cal); only `banks` and `validate` need it."""
    if os.environ.get("HOA_ARRAY_CAL_DIR"):
        sys.path.insert(0, os.environ["HOA_ARRAY_CAL_DIR"])
    try:
        from zm1_encoder import config, filters, order_limit
        from zm1_encoder.encoder_modeled import compute_modeled_encoder
    except ImportError as exc:
        sys.exit(f"zm1_encoder is not importable ({exc}): set HOA_ARRAY_CAL_DIR to a checkout "
                 "of the hoa-array-cal repository (README, 'Open re-encoding of the ZM-1 A-format')")
    assert config.FIR_LENGTH == FIR_LEN and config.FS == FS, (config.FIR_LENGTH, config.FS)
    if not NOISE_PSD_PATH.exists():
        sys.exit(f"{NOISE_PSD_PATH} is missing; the MMSE bank regularizes against it")
    config.CAPSULE_NOISE_PSD_PATH = NOISE_PSD_PATH
    return config, filters, order_limit, compute_modeled_encoder
SESSION_REL = Path("sessions") / "2024-08-15_aula-pg_solo-piano-mic-comparison"
AFORMAT_FILES = {
    "Franck": "AFORMAT_ZM1_CFranck-PreludeChoralFugue.wav",
    "Prokofiev": "AFORMAT_ZM1_SProkofiev-Sonata4.wav",
}
FACTORY_FILES = {
    "Franck": "3OA_ZM1_CFranck-PreludeChoralFugue.wav",
    "Prokofiev": "3OA_ZM1_SProkofiev-Sonata4.wav",
}
PIECES = list(AFORMAT_FILES)
CAPSULES = list(range(19))          # channel 19 is digitally silent
FS = 48000
FRAME_LEN = 48000
FIR_LEN = 512                        # zm1_encoder.config.FIR_LENGTH, asserted in load_encoder()
DELAY = FIR_LEN // 2                 # 256-sample modelling delay
NFFT = 65536
BLOCK = NFFT - (FIR_LEN - 1)         # 65025
ORDER_RANGES = {0: (0, 1), 1: (1, 4), 2: (4, 9), 3: (9, 16)}

CONFIGS = {
    "tikhonov": dict(reg_method="tikhonov", order_limit=False),
    "tikhonov_ordlim": dict(reg_method="tikhonov", order_limit=True),
    "softlimit_20": dict(reg_method="softlimit", max_gain_db=20.0, order_limit=False),
    "softlimit_30": dict(reg_method="softlimit", max_gain_db=30.0, order_limit=False),
    "softlimit_40": dict(reg_method="softlimit", max_gain_db=40.0, order_limit=False),
    "mmse_20": dict(reg_method="mmse", snr_prior_db=20.0, order_limit=False),
}


def aformat_path(session: Path, piece: str) -> Path:
    return session / "audio_a_format" / AFORMAT_FILES[piece]


def factory_path(session: Path, piece: str) -> Path:
    return session / "audio" / FACTORY_FILES[piece]


def cache_name(out: Path, cfg: str, piece: str) -> Path:
    return out / "cache" / f"frames_ZMOne_{cfg}_{piece}.npz"


# --------------------------------------------------------------------------- #
# Banks
# --------------------------------------------------------------------------- #
def build_bank(name: str) -> tuple[np.ndarray, dict]:
    config, filters, order_limit, compute_modeled_encoder = load_encoder()
    cfg = CONFIGS[name]
    freqs = np.fft.rfftfreq(config.NFFT, 1.0 / config.FS)
    enc = compute_modeled_encoder(
        freqs,
        reg_method=cfg["reg_method"],
        max_gain_db=cfg.get("max_gain_db"),
        n_order=3,
        snr_prior_db=cfg.get("snr_prior_db"),
    )
    if cfg["order_limit"]:
        enc = order_limit.apply_order_limit(enc, freqs, verbose=True)
    bank = filters.frequency_to_fir(enc)
    meta = {
        "name": name,
        "encoder_kind": "modeled",
        "reg_method": cfg["reg_method"],
        "n_order": 3,
        "max_gain_db": (cfg.get("max_gain_db") if cfg.get("max_gain_db") is not None
                        else config.MAX_GAIN_DB),
        "max_gain_db_used_by_reg": cfg["reg_method"] == "softlimit",
        "snr_prior_db": (cfg.get("snr_prior_db") if cfg.get("snr_prior_db") is not None
                         else config.MMSE_SNR_PRIOR_DB),
        "snr_prior_db_used_by_reg": cfg["reg_method"] == "mmse",
        "noise_psd_file": NOISE_PSD_PATH.name,
        "noise_psd_sha256": hashlib.sha256(NOISE_PSD_PATH.read_bytes()).hexdigest(),
        "noise_psd_used": cfg["reg_method"] == "mmse",
        "noise_psd_provenance": "simulated capsule self-noise (zm1_encoder.simulate, 5 s, seed 0, "
                                "Welch PSD); no measured noise spectrum",
        "order_limit": cfg["order_limit"],
        "order_bands_hz": config.ORDER_BANDS_HZ if cfg["order_limit"] else None,
        "order_taper_oct": config.ORDER_TAPER_OCT if cfg["order_limit"] else None,
        "maxre_taper": config.MAXRE_TAPER_ENABLE if cfg["order_limit"] else False,
        "lambda_schedule": {
            "LAMBDA_MIN": config.LAMBDA_MIN, "LAMBDA_MAX": config.LAMBDA_MAX,
            "LAMBDA_KNEE_HZ": config.LAMBDA_KNEE_HZ,
            "LAMBDA_ALIAS_HZ": config.LAMBDA_ALIAS_HZ,
        } if cfg["reg_method"] == "tikhonov" else None,
        "enc_objective": config.ENC_OBJECTIVE,
        "R_SPHERE": config.R_SPHERE, "C_SOUND": config.C_SOUND,
        "NFFT": config.NFFT, "FS": config.FS,
        "FIR_LENGTH": config.FIR_LENGTH, "FIR_WINDOW": config.FIR_WINDOW,
        "modelling_delay_samples": DELAY,
        "sh_norm": "sn3d", "channel_order": "acn",
        "bank_shape": list(bank.shape), "bank_dtype": str(bank.dtype),
        "fir_rms_gain_db_max": float(filters.rms_gain_db(bank).max()),
        "capsule_channels": CAPSULES,
    }
    return bank, meta


def cmd_banks(out: Path) -> None:
    bank_dir = out / "banks"
    bank_dir.mkdir(parents=True, exist_ok=True)
    for name in CONFIGS:
        bank, meta = build_bank(name)
        np.save(bank_dir / f"{name}.npy", bank)
        (bank_dir / f"{name}.json").write_text(json.dumps(meta, indent=2) + "\n")
        print(f"[bank] {name}: shape {bank.shape} {bank.dtype}, "
              f"max FIR RMS gain {meta['fir_rms_gain_db_max']:.2f} dB -> {bank_dir / (name + '.npy')}")


def load_bank(out: Path, name: str) -> np.ndarray:
    return np.load(out / "banks" / f"{name}.npy")


# --------------------------------------------------------------------------- #
# Streaming machinery
# --------------------------------------------------------------------------- #
class FrameAccumulator:
    """Per-channel sum of squares in fixed-length frames, skipping `skip` leading samples."""

    def __init__(self, n_ch: int, frame_len: int = FRAME_LEN, skip: int = 0):
        self.frame_len = frame_len
        self.skip = skip
        self.energies: list[np.ndarray] = []
        self.counts: list[int] = []
        self.cur = np.zeros(n_ch, dtype=np.float64)
        self.cur_n = 0

    def push(self, y: np.ndarray) -> None:          # y: (n_ch, n) float64
        if self.skip:
            d = min(self.skip, y.shape[1])
            y = y[:, d:]
            self.skip -= d
        pos = 0
        n = y.shape[1]
        while pos < n:
            take = min(self.frame_len - self.cur_n, n - pos)
            seg = y[:, pos:pos + take]
            self.cur += np.einsum("kn,kn->k", seg, seg)
            self.cur_n += take
            pos += take
            if self.cur_n == self.frame_len:
                self.energies.append(self.cur)
                self.counts.append(self.cur_n)
                self.cur = np.zeros_like(self.cur)
                self.cur_n = 0

    def finish(self) -> tuple[np.ndarray, np.ndarray]:
        if self.cur_n > 0:
            self.energies.append(self.cur)
            self.counts.append(self.cur_n)
            self.cur = np.zeros_like(self.cur)
            self.cur_n = 0
        return np.vstack(self.energies), np.asarray(self.counts, dtype=np.int64)


class OLAConvolver:
    """Block FFT overlap-add of a (K, Q, L) bank against a Q-channel stream."""

    def __init__(self, bank: np.ndarray, nfft: int = NFFT):
        k, q, L = bank.shape
        self.L = L
        self.nfft = nfft
        self.block = nfft - (L - 1)
        # (F, K, Q) complex128 so each block is one batched matmul over bins.
        fh = sfft.rfft(bank.astype(np.float64), n=nfft, axis=-1)     # (K, Q, F)
        self.Fh = np.ascontiguousarray(np.transpose(fh, (2, 0, 1)))
        self.tail = np.zeros((k, L - 1), dtype=np.float64)
        self.K, self.Q = k, q

    def process(self, blk: np.ndarray) -> np.ndarray:
        """blk: (n, Q) with n <= block. Returns (K, n) output samples."""
        n = blk.shape[0]
        X = sfft.rfft(blk.T.astype(np.float64), n=self.nfft, axis=-1, workers=-1)  # (Q, F)
        Y = np.matmul(self.Fh, X.T[:, :, None])[:, :, 0].T            # (K, F)
        y = sfft.irfft(Y, n=self.nfft, axis=-1, workers=-1)             # (K, nfft)
        y = y[:, :n + self.L - 1]
        y[:, :self.L - 1] += self.tail
        out = y[:, :n]
        self.tail = np.zeros_like(self.tail)
        rest = y[:, n:]
        self.tail[:, :rest.shape[1]] = rest
        return out

    def flush(self) -> np.ndarray:
        out = self.tail.copy()
        self.tail = np.zeros_like(self.tail)
        return out


def stream_encode(path: Path, bank: np.ndarray, max_seconds: float | None = None,
                  collect: bool = False):
    """Stream a 20-ch A-format file through the bank.

    Returns (energy, counts, n_in, elapsed_s, full_output_or_None). The frame
    accumulator drops the 256-sample modelling delay so frame 0 starts at input
    sample 0; the trailing L-1-256 = 255 samples of filter ringing land in the
    last (partial) frame.
    """
    conv = OLAConvolver(bank)
    acc = FrameAccumulator(bank.shape[0], skip=DELAY)
    chunks = [] if collect else None
    n_in = 0
    limit = None if max_seconds is None else int(round(max_seconds * FS))
    t0 = time.perf_counter()
    with sf.SoundFile(str(path)) as f:
        assert f.samplerate == FS and f.channels == 20, (f.samplerate, f.channels)
        for blk in f.blocks(blocksize=BLOCK, dtype="float64", always_2d=True):
            if limit is not None and n_in + blk.shape[0] > limit:
                blk = blk[:limit - n_in]
            if blk.shape[0] == 0:
                break
            y = conv.process(blk[:, CAPSULES])
            n_in += blk.shape[0]
            acc.push(y)
            if collect:
                chunks.append(y)
            if limit is not None and n_in >= limit:
                break
    y = conv.flush()
    acc.push(y)
    if collect:
        chunks.append(y)
    energy, counts = acc.finish()
    elapsed = time.perf_counter() - t0
    full = np.concatenate(chunks, axis=1) if collect else None
    return energy, counts, n_in, elapsed, full


def stream_frames(path: Path, channels=None):
    """Plain per-frame sums of squares of a WAV (revision_stats.build_frame_cache logic)."""
    t0 = time.perf_counter()
    energies, counts = [], []
    with sf.SoundFile(str(path)) as f:
        sr = f.samplerate
        for block in f.blocks(blocksize=int(round(sr * 1.0)), dtype="float32", always_2d=True):
            if channels is not None:
                block = block[:, channels]
            energies.append(np.sum(block.astype(np.float64) ** 2, axis=0))
            counts.append(block.shape[0])
    return np.vstack(energies), np.asarray(counts, dtype=np.int64), sr, time.perf_counter() - t0


# --------------------------------------------------------------------------- #
# Levels
# --------------------------------------------------------------------------- #
def levels_both(energy: np.ndarray, counts: np.ndarray) -> dict:
    ssum = energy.sum(axis=0)
    n = int(counts.sum())
    rms = np.sqrt(ssum / n)
    mean_rms = [20.0 * np.log10(float(np.mean(rms[a:b])) + 1e-20) for a, b in ORDER_RANGES.values()]
    summed = [10.0 * np.log10(float(np.sum(rms[a:b] ** 2)) + 1e-40) for a, b in ORDER_RANGES.values()]
    return {
        "order_levels_meanrms_dbfs": mean_rms,
        "order_levels_sum_dbfs": summed,
        "rolloff_0_3_meanrms_db": mean_rms[0] - mean_rms[3],
        "rolloff_0_3_sum_db": summed[0] - summed[3],
        "n_samples": n,
        "n_frames": int(len(counts)),
    }


def save_cache(cache_path: Path, energy, counts, sr=FS):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache_path, energy=energy, counts=counts, sr=sr)


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def cmd_validate(out: Path, session: Path) -> None:
    load_encoder()
    from zm1_encoder.validate import apply_fir_bank

    bank = load_bank(out, "tikhonov")
    path = aformat_path(session, "Franck")
    n = 60 * FS
    with sf.SoundFile(str(path)) as f:
        a = f.read(n, dtype="float64", always_2d=True)[:, CAPSULES].T        # (19, N)
    t0 = time.perf_counter()
    ref = apply_fir_bank(a, bank)                                              # (16, N+511)
    t_ref = time.perf_counter() - t0
    energy, counts, n_in, t_stream, full = stream_encode(path, bank, max_seconds=60.0, collect=True)
    assert n_in == n, (n_in, n)
    assert full.shape == ref.shape, (full.shape, ref.shape)

    diff = np.abs(full - ref)
    max_abs = float(diff.max())
    peak = float(np.abs(ref).max())

    def order_e(x):
        e = np.sum(x ** 2, axis=1)
        return np.array([e[a:b].sum() for a, b in ORDER_RANGES.values()])

    e_ref, e_str = order_e(ref), order_e(full)
    # Frame-level check: derive frames from the reference output the same way.
    acc = FrameAccumulator(16, skip=DELAY)
    acc.push(ref)
    e_ref_frames, c_ref_frames = acc.finish()
    frame_abs = float(np.abs(e_ref_frames - energy).max())
    frame_rel = float((np.abs(e_ref_frames - energy) / np.maximum(e_ref_frames, 1e-300)).max())

    res = {
        "file": str(path.relative_to(session.parent.parent)), "seconds": 60, "bank": "tikhonov",
        "n_input_samples": n, "n_output_samples": int(ref.shape[1]),
        "max_abs_sample_diff": max_abs,
        "ref_peak_abs": peak,
        "max_abs_sample_diff_rel_to_peak": max_abs / peak,
        "per_order_energy_ref": e_ref.tolist(),
        "per_order_energy_stream": e_str.tolist(),
        "max_abs_per_order_energy_diff": float(np.abs(e_ref - e_str).max()),
        "max_rel_per_order_energy_diff": float((np.abs(e_ref - e_str) / e_ref).max()),
        "frames_max_abs_diff": frame_abs, "frames_max_rel_diff": frame_rel,
        "frames_counts_equal": bool(np.array_equal(c_ref_frames, counts)),
        "n_frames": int(len(counts)), "last_frame_count": int(counts[-1]),
        "t_reference_s": t_ref, "t_streaming_s": t_stream,
        "nfft": NFFT, "blocksize": BLOCK,
    }
    (out / "validation.json").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))
    ok = res["max_rel_per_order_energy_diff"] < 1e-6 and res["max_abs_sample_diff_rel_to_peak"] < 1e-6
    print("VALIDATION", "PASS" if ok else "FAIL")
    if not ok:
        sys.exit(1)


def cmd_factory(out: Path, session: Path) -> None:
    res = {}
    for piece in PIECES:
        path = factory_path(session, piece)
        energy, counts, sr, el = stream_frames(path)
        cp = cache_name(out, "factory", piece)
        save_cache(cp, energy, counts, sr)
        lv = levels_both(energy, counts)
        # paths are recorded relative to --out and to the deposit root, never as machine paths
        lv.update(piece=piece, config="factory", cache_path=str(cp.relative_to(out)), runtime_s=el,
                  source=str(path.relative_to(session.parent.parent)))
        # cross-check against the committed cache
        old = COMMITTED_CACHE / f"frames_ZMOne{piece}.npz"
        if old.exists():
            z = np.load(old)
            lv["committed_cache_max_abs_energy_diff"] = float(np.abs(z["energy"] - energy).max())
            lv["committed_cache_counts_equal"] = bool(np.array_equal(z["counts"], counts))
            lv["committed_cache_rolloff_meanrms_db"] = levels_both(z["energy"], z["counts"])["rolloff_0_3_meanrms_db"]
        res[piece] = lv
        print(f"[factory] {piece}: {el:.1f} s, rolloff meanRMS {lv['rolloff_0_3_meanrms_db']:.3f} dB, "
              f"sum {lv['rolloff_0_3_sum_db']:.3f} dB")
    (out / "results_factory.json").write_text(json.dumps(res, indent=2) + "\n")


def cmd_sweep(out: Path, session: Path, configs=None, pieces=None) -> None:
    configs = list(CONFIGS) if configs is None else configs
    pieces = PIECES if pieces is None else pieces
    res_path = out / "results_sweep.json"
    res = json.loads(res_path.read_text()) if res_path.exists() else {}
    for cfg in configs:
        bank = load_bank(out, cfg)
        for piece in pieces:
            key = f"{cfg}/{piece}"
            src = aformat_path(session, piece)
            energy, counts, n_in, el, _ = stream_encode(src, bank)
            cp = cache_name(out, cfg, piece)
            save_cache(cp, energy, counts)
            lv = levels_both(energy, counts)
            lv.update(piece=piece, config=cfg, cache_path=str(cp.relative_to(out)), runtime_s=el,
                      n_input_samples=int(n_in), source=str(src.relative_to(session.parent.parent)))
            res[key] = lv
            res_path.write_text(json.dumps(res, indent=2) + "\n")
            print(f"[sweep] {key}: {el:.1f} s, n_in {n_in}, frames {lv['n_frames']}, "
                  f"meanRMS {['%.2f' % v for v in lv['order_levels_meanrms_dbfs']]} "
                  f"rolloff {lv['rolloff_0_3_meanrms_db']:.3f} / sum {lv['rolloff_0_3_sum_db']:.3f} dB",
                  flush=True)


def cmd_summary(out: Path) -> None:
    rows = []
    fac = json.loads((out / "results_factory.json").read_text())
    swp = json.loads((out / "results_sweep.json").read_text())
    entries = list(fac.values()) + list(swp.values())
    order = {"factory": 0, **{c: i + 1 for i, c in enumerate(CONFIGS)}}
    entries.sort(key=lambda r: (r["piece"], order[r["config"]]))
    for r in entries:
        m, s = r["order_levels_meanrms_dbfs"], r["order_levels_sum_dbfs"]
        rows.append({
            "piece": r["piece"], "config": r["config"],
            "n_samples": r["n_samples"], "n_frames": r["n_frames"],
            "runtime_s": f"{r['runtime_s']:.1f}",
            **{f"order{o}_meanrms_dbfs": f"{m[o]:.3f}" for o in range(4)},
            "rolloff_0_3_meanrms_db": f"{r['rolloff_0_3_meanrms_db']:.3f}",
            **{f"order{o}_sum_dbfs": f"{s[o]:.3f}" for o in range(4)},
            "rolloff_0_3_sum_db": f"{r['rolloff_0_3_sum_db']:.3f}",
            "cache_path": r["cache_path"],
        })
    path = out / "reencode_summary.csv"
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path} ({len(rows)} rows)")
    for r in rows:
        print(r["piece"], r["config"], "meanRMS rolloff", r["rolloff_0_3_meanrms_db"],
              "sum rolloff", r["rolloff_0_3_sum_db"], "runtime", r["runtime_s"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["banks", "validate", "factory", "sweep", "summary"])
    ap.add_argument("selection", nargs="*",
                    help="sweep only: comma-separated configs, then comma-separated pieces")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT,
                    help="results directory holding banks/, cache/ and the JSON/CSV outputs "
                         "(default %(default)s)")
    ap.add_argument("--corpus-dir", type=Path, default=os.environ.get("HOA_CORPUS_DIR"),
                    help="deposit root containing sessions/ (default: $HOA_CORPUS_DIR)")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    session = None
    if args.command in ("validate", "factory", "sweep"):
        if args.corpus_dir is None:
            sys.exit(f"{args.command} needs the deposit audio: set HOA_CORPUS_DIR or pass "
                     "--corpus-dir (download from doi.org/10.34808/w8bx-2094)")
        session = args.corpus_dir / SESSION_REL
        if not session.is_dir():
            sys.exit(f"session folder not found: {session}")

    if args.command == "banks":
        cmd_banks(args.out)
    elif args.command == "validate":
        cmd_validate(args.out, session)
    elif args.command == "factory":
        cmd_factory(args.out, session)
    elif args.command == "sweep":
        cmd_sweep(args.out, session,
                  configs=args.selection[0].split(",") if len(args.selection) > 0 else None,
                  pieces=args.selection[1].split(",") if len(args.selection) > 1 else None)
    elif args.command == "summary":
        cmd_summary(args.out)


if __name__ == "__main__":
    main()
