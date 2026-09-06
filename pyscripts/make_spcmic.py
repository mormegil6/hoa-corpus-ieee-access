#!/usr/bin/env python3
"""
make_spcmic.py
==============

Rewrite an 84-channel Spcmic capture into the container the Harpex Spcmic
application writes, so that a recording made outside the application (for
example through a DAW) can be loaded back into it and encoded with the
factory converter.

The application's own files are RIFF/WAVE carrying a `ds64` chunk and the
32-bit size fields saturated to 0xFFFFFFFF: a hybrid that the RF64
specification does not permit above 4 GiB, and that libsndfile, CoreAudio,
SoX and Python's `wave` all silently truncate to 355 s. This script
reproduces that layout deliberately, because it is what the application
reads, and it verifies the source audio format matches before writing.

Only the container is rewritten. Sample data is copied verbatim: no
resampling, no requantisation, no channel reordering.

Usage:
    python make_spcmic.py IN.wav OUT.spcmic [--seconds N] [--start N]
"""

import argparse
import struct
import sys
from pathlib import Path

W64_RIFF = bytes.fromhex("726966662e91cf11a5d628db04c10000")
EXPECTED = {"channels": 84, "rate": 48000, "bits": 24}
COPY_BLOCK = 1 << 24


def w64_chunks(f):
    """Yield (name, payload_size, data_offset) for each Wave64 chunk."""
    f.seek(40)
    while True:
        head = f.read(24)
        if len(head) < 24:
            return
        name = head[:16][:4].decode("ascii", "replace")
        size = struct.unpack("<Q", head[16:])[0]
        yield name, size - 24, f.tell()
        if name == "data":
            return
        body = size - 24
        f.seek(body + ((8 - (body % 8)) % 8), 1)


def riff_chunks(f):
    f.seek(12)
    while True:
        head = f.read(8)
        if len(head) < 8:
            return
        cid = head[:4].decode("ascii", "replace")
        size = struct.unpack("<I", head[4:])[0]
        yield cid, size, f.tell()
        if cid == "data":
            return
        f.seek(size + (size & 1), 1)


def read_source(path):
    """Return (fmt_tuple, data_offset, data_size) for a Wave64 or RIFF/RF64 source."""
    with open(path, "rb") as f:
        magic = f.read(16)
        f.seek(0)
        walker = w64_chunks if magic == W64_RIFF else riff_chunks
        fmt = data = None
        ds64_data = None
        for name, size, off in walker(f):
            if name.strip() == "fmt":
                cur = f.tell()
                f.seek(off)
                raw = f.read(size)
                f.seek(cur)
                fmt = struct.unpack("<HHIIHH", raw[:16])
            elif name == "ds64":
                cur = f.tell()
                f.seek(off)
                ds64_data = struct.unpack("<QQQ", f.read(size)[:24])
                f.seek(cur)
            elif name == "data":
                real = size
                if ds64_data and size == 0xFFFFFFFF:
                    real = ds64_data[1]
                data = (off, real)
    if fmt is None or data is None:
        sys.exit(f"{path}: could not find fmt and data chunks")
    return fmt, data[0], data[1]


def main():
    ap = argparse.ArgumentParser(
        description="Rewrite an 84-channel Spcmic capture into the container the Harpex "
                    "Spcmic application reads; sample data is copied verbatim.")
    ap.add_argument("source", help="84-channel 48 kHz 24-bit PCM capture (Wave64, RIFF or RF64)")
    ap.add_argument("dest", help="output .spcmic file")
    ap.add_argument("--seconds", type=float, help="write only this many seconds (for a test file)")
    ap.add_argument("--start", type=float, default=0.0, help="skip this many seconds first")
    args = ap.parse_args()

    fmt, data_off, data_size = read_source(args.source)
    tag, channels, rate, byte_rate, block_align, bits = fmt
    print(f"source: fmt={tag} {channels} ch, {rate} Hz, {bits}-bit, block align {block_align}")
    if tag != 1:
        sys.exit(f"refusing: source is not PCM (format tag {tag})")
    if (channels, rate, bits) != (EXPECTED["channels"], EXPECTED["rate"], EXPECTED["bits"]):
        sys.exit(f"refusing: expected {EXPECTED['channels']} ch / {EXPECTED['rate']} Hz / "
                 f"{EXPECTED['bits']}-bit, found {channels}/{rate}/{bits}")
    if block_align != channels * bits // 8:
        sys.exit(f"refusing: block align {block_align} does not match {channels} ch of {bits}-bit")

    skip = int(args.start * rate) * block_align
    if skip >= data_size:
        sys.exit("refusing: --start is past the end of the recording")
    take = data_size - skip
    if args.seconds:
        take = min(take, int(args.seconds * rate) * block_align)
    take -= take % block_align
    frames = take // block_align
    print(f"writing {frames} frames ({frames / rate:.3f} s) from offset {skip} bytes")

    # The application's layout: ds64(28) + fmt(18) + fact(4) + data, sizes saturated.
    fmt_chunk = struct.pack("<HHIIHHH", 1, channels, rate, rate * block_align, block_align, bits, 0)
    ds64 = struct.pack("<QQQ", 0, 0, 0)  # placeholder, patched below
    body = (b"ds64" + struct.pack("<I", 28) + ds64 + b"\0" * 4
            + b"fmt " + struct.pack("<I", len(fmt_chunk)) + fmt_chunk
            + b"fact" + struct.pack("<I", 4) + struct.pack("<I", 0xFFFFFFFF)
            + b"data" + struct.pack("<I", 0xFFFFFFFF))
    riff_size = 4 + len(body) + take

    with open(args.source, "rb") as src, open(args.dest, "wb") as out:
        out.write(b"RIFF" + struct.pack("<I", 0xFFFFFFFF) + b"WAVE")
        out.write(body)
        header_end = out.tell()
        src.seek(data_off + skip)
        left = take
        while left:
            block = src.read(min(COPY_BLOCK, left))
            if not block:
                sys.exit("source ended early: the container size fields disagree with the file")
            out.write(block)
            left -= len(block)
        # patch ds64 now that the true sizes are known
        out.seek(20)
        out.write(struct.pack("<QQQ", riff_size, take, frames))

    written = Path(args.dest).stat().st_size
    print(f"wrote {args.dest} ({written} bytes, header {header_end} + audio {take})")
    print(f"ds64: riffSize={riff_size} dataSize={take} sampleCount={frames}")


if __name__ == "__main__":
    main()
