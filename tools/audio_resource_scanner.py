#!/usr/bin/env python3
"""Read-only Phase 7A scanner for named audio resources and RIFF/WAVE containers.

The scanner does not decode undocumented formats, write firmware bytes, or infer a
device filesystem override.  Its JSON result records only source-relative facts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SOURCE_SIZE = 0x200000
SOURCE_SHA256 = "720ed0b65c91b149b0916498732b0ecf40227736ef5e3c126c487a7b5253436c"
PAYLOAD_OFFSET = 0x200
NAMES = (b"CLICK.WAV", b"POWERON_AUDIO.WAV", b"POWEROFF_AUDIO.WAV", b"BEEP.WAV", b"IMG.WAV")


def occurrences(blob: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    start = 0
    while True:
        found = blob.find(needle, start)
        if found < 0:
            return offsets
        offsets.append(found)
        start = found + 1


def source_offset_record(offset: int) -> dict[str, object]:
    return {
        "source_file_offset": f"0x{offset:06x}",
        "candidate_payload_va": f"0x{offset - PAYLOAD_OFFSET:06x}" if offset >= PAYLOAD_OFFSET else None,
        "mapping": "file_offset = payload_va + 0x200; hypothesis only",
    }


def riff_records(blob: bytes) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for offset in occurrences(blob, b"RIFF"):
        if offset + 12 > len(blob) or blob[offset + 8:offset + 12] != b"WAVE":
            continue
        declared_size = int.from_bytes(blob[offset + 4:offset + 8], "little")
        end = offset + 8 + declared_size
        record: dict[str, object] = {
            **source_offset_record(offset),
            "declared_riff_size": declared_size,
            "declared_end_file_offset": f"0x{end:06x}",
            "within_source": end <= len(blob),
            "format": "RIFF/WAVE",
        }
        if end <= len(blob):
            chunks: list[dict[str, object]] = []
            cursor = offset + 12
            while cursor + 8 <= end:
                tag = blob[cursor:cursor + 4]
                size = int.from_bytes(blob[cursor + 4:cursor + 8], "little")
                payload_end = cursor + 8 + size
                if payload_end > end:
                    chunks.append({"tag_ascii": tag.decode("ascii", "replace"), "size": size, "truncated": True})
                    break
                chunks.append({"tag_ascii": tag.decode("ascii", "replace"), "size": size, "truncated": False})
                cursor = payload_end + (size & 1)
            record["chunks"] = chunks
        records.append(record)
    return records


def pointer_candidates(blob: bytes, target_offset: int) -> dict[str, list[dict[str, object]]]:
    # These are byte-pattern candidates only.  The raw loader/base and runtime
    # relocation state are not established by this scan.
    target_va = target_offset - PAYLOAD_OFFSET
    values = {
        "u32_payload_va_le": target_va.to_bytes(4, "little"),
        "u32_source_offset_le": target_offset.to_bytes(4, "little"),
        "u16_payload_va_le": (target_va & 0xffff).to_bytes(2, "little"),
        "u16_source_offset_le": (target_offset & 0xffff).to_bytes(2, "little"),
    }
    return {
        name: [source_offset_record(position) for position in occurrences(blob, value)]
        for name, value in values.items()
    }


def scan(source: Path) -> dict[str, object]:
    blob = source.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if len(blob) != SOURCE_SIZE or digest != SOURCE_SHA256:
        raise ValueError("source is not the verified Phase 1 reference firmware")
    resources = []
    for name in NAMES:
        positions = occurrences(blob, name)
        resources.append({
            "name": name.decode("ascii"),
            "name_occurrences": [source_offset_record(position) for position in positions],
            "raw_pointer_pattern_candidates": [pointer_candidates(blob, position) for position in positions],
        })
    return {
        "status": "analysis-only",
        "source_size": len(blob),
        "source_sha256": digest,
        "resources": resources,
        "riff_wave_containers": riff_records(blob),
        "limitations": [
            "A filename or raw pointer-pattern match does not prove a resource table, allocation, decoder, or runtime lookup path.",
            "No undocumented container is decoded and no replacement image is written.",
            "No SD-card or device behavior is observed by this offline scan.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = scan(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "resources": len(result["resources"]), "riff_wave_containers": len(result["riff_wave_containers"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
