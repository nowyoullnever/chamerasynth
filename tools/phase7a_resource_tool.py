#!/usr/bin/env python3
"""Offline-only inspector and equal-size BEEP.WAV replacement prototype.

This tool accepts only the verified Phase 1 source.  It knows the recovered
resource-index layout sufficient for BEEP.WAV and refuses variable-length
replacement, metadata writes, device I/O, SD-card output, or update packaging.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

SOURCE_SIZE = 0x200000
SOURCE_SHA256 = "720ed0b65c91b149b0916498732b0ecf40227736ef5e3c126c487a7b5253436c"
INDEX_OFFSET = 0x120000
INDEX_ENTRIES_OFFSET = 0x18
ENTRY_SIZE = 0x18
SECTOR_SIZE = 0x200
BEEP_NAME = "BEEPWAV"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if len(data) != SOURCE_SIZE or digest(data) != SOURCE_SHA256:
        raise ValueError("source is not the verified Phase 1 reference firmware")
    return data


def parse_wav(data: bytes) -> dict[str, int]:
    if len(data) < 44 or data[:4] != b"RIFF" or data[8:12] != b"WAVE" or data[12:16] != b"fmt " or data[36:40] != b"data":
        raise ValueError("resource is not the supported canonical RIFF/WAVE layout")
    riff_size = struct.unpack_from("<I", data, 4)[0]
    fmt_size = struct.unpack_from("<I", data, 16)[0]
    audio_format, channels, sample_rate, byte_rate, block_align, bits = struct.unpack_from("<HHIIHH", data, 20)
    data_size = struct.unpack_from("<I", data, 40)[0]
    total_size = 8 + riff_size
    if fmt_size != 16 or total_size != 44 + data_size or total_size > len(data):
        raise ValueError("unsupported RIFF/WAVE size layout")
    return {"riff_size": riff_size, "total_size": total_size, "audio_format": audio_format, "channels": channels,
            "sample_rate": sample_rate, "byte_rate": byte_rate, "block_align": block_align, "bits_per_sample": bits,
            "data_size": data_size}


def decode_name(raw: bytes) -> str:
    return raw.split(b"\0", 1)[0].decode("ascii", "strict")


def resources(source: bytes) -> list[dict[str, object]]:
    count = struct.unpack_from("<H", source, INDEX_OFFSET + 2)[0]
    if source[INDEX_OFFSET:INDEX_OFFSET + 2] != b"GP" or count < 2:
        raise ValueError("unrecognized resource index header")
    result: list[dict[str, object]] = []
    for index in range(count - 1):
        offset = INDEX_OFFSET + INDEX_ENTRIES_OFFSET + index * ENTRY_SIZE
        following = offset + ENTRY_SIZE
        name = decode_name(source[offset:offset + 0x13])
        start_sector = struct.unpack_from("<I", source, offset + 0x14)[0]
        next_sector = struct.unpack_from("<I", source, following + 0x14)[0]
        if next_sector <= start_sector:
            raise ValueError(f"resource index is non-monotonic at entry {index}")
        start = INDEX_OFFSET + start_sector * SECTOR_SIZE
        end = INDEX_OFFSET + next_sector * SECTOR_SIZE
        if end > len(source):
            raise ValueError(f"resource range exceeds source at entry {index}")
        result.append({"index": index, "name": name, "index_entry_file_offset": f"0x{offset:06x}",
                       "start_sector": start_sector, "next_start_sector": next_sector, "file_offset": start,
                       "allocation_end": end, "allocation_size": end - start})
    return result


def beep_record(source: bytes) -> dict[str, object]:
    record = next((item for item in resources(source) if item["name"] == BEEP_NAME), None)
    if record is None:
        raise ValueError("BEEPWAV is absent from the recovered index")
    start = int(record["file_offset"])
    allocation_end = int(record["allocation_end"])
    wav = parse_wav(source[start:allocation_end])
    resource_end = start + wav["total_size"]
    padding = source[resource_end:allocation_end]
    if any(byte != 0xff for byte in padding):
        raise ValueError("BEEP allocation padding is not the observed all-FF layout")
    return {**record, "resource_file_end": resource_end, "resource_size": wav["total_size"], "resource_sha256": digest(source[start:resource_end]),
            "allocation_sha256": digest(source[start:allocation_end]), "alignment": SECTOR_SIZE, "trailing_padding_size": len(padding),
            "trailing_padding_byte": "0xff", "wav": wav}


def report(source_path: Path) -> dict[str, object]:
    source = source_bytes(source_path)
    beep = beep_record(source)
    return {"status": "analysis-only", "source_size": len(source), "source_sha256": digest(source), "resource_index": {
        "source_file_offset": f"0x{INDEX_OFFSET:06x}", "entry_size": ENTRY_SIZE, "sector_size": SECTOR_SIZE,
        "entry_count_from_header": struct.unpack_from("<H", source, INDEX_OFFSET + 2)[0],
        "access_evidence": "Ghidra static pseudocode 0x177c/0x133c: table entries are copied as 0x20-byte runtime records; field +0x14 is used as a sector start and successive starts define the allocation."},
        "beep": {key: (f"0x{value:06x}" if key in {"file_offset", "allocation_end", "resource_file_end"} else value) for key, value in beep.items()},
        "limitations": ["Static analysis only; no device, USB, SD card, or flash operation occurred.", "No checksum/signature field has been proven for this resource container.", "No SD override path or filename is inferred by this tool."]}


def low_amplitude_tone(wav: dict[str, int], frequency_hz: float = 659.25, amplitude: float = 0.05) -> bytes:
    if wav["audio_format"] != 1 or wav["channels"] != 1 or wav["bits_per_sample"] != 16 or wav["block_align"] != 2:
        raise ValueError("only PCM mono 16-bit BEEP.WAV format is supported")
    if not 0 < amplitude <= 0.1:
        raise ValueError("amplitude must be within (0, 0.1]")
    samples = wav["data_size"] // wav["block_align"]
    values = [round(32767 * amplitude * math.sin(2.0 * math.pi * frequency_hz * frame / wav["sample_rate"])) for frame in range(samples)]
    payload = struct.pack("<" + "h" * samples, *values)
    return b"RIFF" + struct.pack("<I", 36 + len(payload)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, wav["sample_rate"], wav["sample_rate"] * 2, 2, 16) + b"data" + struct.pack("<I", len(payload)) + payload


def manifest_for(source: bytes, replacement: bytes) -> dict[str, object]:
    record = beep_record(source)
    original = source[int(record["file_offset"]):int(record["resource_file_end"])]
    if len(replacement) != len(original):
        raise ValueError("replacement must match the proven BEEP.WAV container length exactly")
    if parse_wav(replacement) != record["wav"]:
        raise ValueError("replacement WAV format must match the proven BEEP.WAV format exactly")
    return {"status": "analysis-only", "flash_ready": False, "resource": "BEEPWAV", "source_sha256": digest(source),
            "file_offset": int(record["file_offset"]), "file_offset_hex": f"0x{int(record['file_offset']):06x}", "length": len(original),
            "allocation_size": int(record["allocation_size"]), "alignment": SECTOR_SIZE, "expected_sha256": digest(original),
            "replacement_sha256": digest(replacement), "metadata_updates": [], "required_unchanged_ranges": [
                {"start": 0, "end": int(record["file_offset"])}, {"start": int(record["resource_file_end"]), "end": len(source)}],
            "limitations": ["Offline experimental candidate only; not an update package.", "The resource allocation is proven, but device boot/update acceptance and recovery are not proven."]}


def apply_candidate(source: bytes, manifest: dict[str, object], replacement: bytes) -> tuple[bytes, dict[str, object]]:
    if manifest.get("status") != "analysis-only" or manifest.get("flash_ready") is not False:
        raise ValueError("manifest must remain analysis-only and non-flash-ready")
    if manifest.get("source_sha256") != digest(source):
        raise ValueError("manifest source identity mismatch")
    offset, length = int(manifest["file_offset"]), int(manifest["length"])
    expected = source[offset:offset + length]
    if digest(expected) != manifest.get("expected_sha256") or digest(replacement) != manifest.get("replacement_sha256"):
        raise ValueError("manifest byte identity mismatch")
    if len(replacement) != length or offset % int(manifest["alignment"]) != 0:
        raise ValueError("replacement length or alignment is not proven")
    candidate = bytearray(source); candidate[offset:offset + length] = replacement
    changed = [position for position, (before, after) in enumerate(zip(source, candidate)) if before != after]
    if not changed or min(changed) < offset or max(changed) >= offset + length:
        raise ValueError("candidate changes fall outside the declared BEEP container")
    restored = bytearray(candidate); restored[offset:offset + length] = expected
    if bytes(restored) != source:
        raise ValueError("byte-level restoration failed")
    return bytes(candidate), {"status": "analysis-only-copy", "flash_ready": False, "source_sha256": digest(source),
                               "candidate_sha256": digest(bytes(candidate)), "changed_byte_count": len(changed),
                               "changed_range": {"start": f"0x{offset:06x}", "end_exclusive": f"0x{offset + length:06x}"},
                               "restoration_byte_identical": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect"); inspect.add_argument("source", type=Path); inspect.add_argument("output", type=Path)
    tone = sub.add_parser("tone"); tone.add_argument("source", type=Path); tone.add_argument("output_wav", type=Path)
    build = sub.add_parser("manifest"); build.add_argument("source", type=Path); build.add_argument("replacement_wav", type=Path); build.add_argument("output", type=Path)
    apply = sub.add_parser("apply"); apply.add_argument("source", type=Path); apply.add_argument("manifest", type=Path); apply.add_argument("replacement_wav", type=Path); apply.add_argument("candidate", type=Path); apply.add_argument("report", type=Path)
    args = parser.parse_args(); source = source_bytes(args.source)
    if args.command == "inspect": result = report(args.source); args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    elif args.command == "tone":
        result = low_amplitude_tone(beep_record(source)["wav"]); args.output_wav.parent.mkdir(parents=True, exist_ok=True); args.output_wav.write_bytes(result)
    elif args.command == "manifest":
        result = manifest_for(source, args.replacement_wav.read_bytes()); args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    else:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8")); candidate, result = apply_candidate(source, manifest, args.replacement_wav.read_bytes()); args.candidate.parent.mkdir(parents=True, exist_ok=True); args.report.parent.mkdir(parents=True, exist_ok=True); args.candidate.write_bytes(candidate); args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"command": args.command, "status": "analysis-only"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
