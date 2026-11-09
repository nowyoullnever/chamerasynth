#!/usr/bin/env python3
"""Read-only firmware inspection for Phase 1.

The program deliberately has no serial, USB, network, subprocess, erase, or
write-to-input path. It calculates file facts and reports candidate signatures;
signature matches are observations, not a claim of an executable format.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Iterator

CHUNK_SIZE = 1024 * 1024
PRINTABLE_MIN = 5
SIGNATURES = {
    "uImage": b"\x27\x05\x19\x56",
    "gzip": b"\x1f\x8b\x08",
    "zlib": b"\x78\x9c",
    "zlib-fast": b"\x78\x01",
    "zlib-best": b"\x78\xda",
    "lzma-alone": b"\x5d\x00\x00",
    "squashfs-le": b"hsqs",
    "squashfs-be": b"sqsh",
    "cramfs": b"\x45\x3d\xcd\x28",
    "FAT": b"FAT",
}


def chunks(path: Path) -> Iterator[bytes]:
    with path.open("rb") as stream:
        while data := stream.read(CHUNK_SIZE):
            yield data


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    for data in chunks(path):
        digest.update(data)
    return digest.hexdigest()


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = [0] * 256
    for item in data:
        counts[item] += 1
    total = len(data)
    return -sum((n / total) * math.log2(n / total) for n in counts if n)


def ascii_strings(path: Path, maximum: int = 200) -> list[dict[str, object]]:
    # Whole-file load avoids silently losing strings spanning a chunk boundary.
    # It is acceptable for the Phase 1 image (~MiB scale), but bounded output
    # protects reports from becoming misleadingly exhaustive.
    data = path.read_bytes()
    found: list[dict[str, object]] = []
    start: int | None = None
    for offset, byte in enumerate(data + b"\x00"):
        if 0x20 <= byte <= 0x7E:
            if start is None:
                start = offset
            continue
        if start is not None and offset - start >= PRINTABLE_MIN:
            found.append({"offset": start, "text": data[start:offset].decode("ascii")})
            if len(found) >= maximum:
                break
        start = None
    return found


def signature_hits(path: Path, maximum_per_signature: int = 64) -> dict[str, list[int]]:
    data = path.read_bytes()
    results: dict[str, list[int]] = {}
    for name, needle in SIGNATURES.items():
        offsets: list[int] = []
        cursor = 0
        while len(offsets) < maximum_per_signature:
            hit = data.find(needle, cursor)
            if hit < 0:
                break
            offsets.append(hit)
            cursor = hit + 1
        if offsets:
            results[name] = offsets
    return results


def inspect(path: Path, window: int = 0x1000) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(path)
    size = path.stat().st_size
    with path.open("rb") as stream:
        head = stream.read(window)
        stream.seek(max(0, size - window))
        tail = stream.read(window)
    return {
        "input": str(path),
        "read_only": True,
        "size_bytes": size,
        "sha256": sha256(path),
        "head_hex": head[:64].hex(),
        "tail_hex": tail[-64:].hex(),
        "entropy": {"first_window": entropy(head), "last_window": entropy(tail)},
        "signature_hits": signature_hits(path),
        "ascii_strings_first_200": ascii_strings(path),
        "limits": [
            "Signatures can occur in data; they do not prove a container.",
            "File offsets are not runtime addresses.",
            "This tool neither disassembles nor executes firmware.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Phase 1 firmware inspection")
    parser.add_argument("firmware", type=Path)
    parser.add_argument("--json", dest="output", type=Path, help="Optional report path; input is never changed")
    args = parser.parse_args()
    report = inspect(args.firmware)
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

