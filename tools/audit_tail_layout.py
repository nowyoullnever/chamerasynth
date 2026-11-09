#!/usr/bin/env python3
"""Read-only Phase 5 audit of the candidate tail and Ghidra direct references.

It does not infer that an FF run is free space or executable memory. It merely
cross-checks the exported direct-reference targets against original bytes and
reports bounded FF runs for subsequent manual data-flow analysis.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

SOURCE_SIZE = 0x200000
SOURCE_SHA256 = "720ed0b65c91b149b0916498732b0ecf40227736ef5e3c126c487a7b5253436c"
FILE_BIAS = 0x200
TAIL_START = 0x1AEE00
TAIL_END = 0x200000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ff_runs(data: bytes, minimum: int) -> list[dict[str, int]]:
    runs: list[dict[str, int]] = []
    start: int | None = None
    for offset, byte in enumerate(data + b"\x00"):
        if byte == 0xFF and start is None:
            start = offset
        elif byte != 0xFF and start is not None:
            size = offset - start
            if size >= minimum:
                runs.append({"file_offset": start, "size": size, "end_exclusive": offset})
            start = None
    return runs


def audit(source: Path, graph: Path, minimum_run: int) -> dict[str, object]:
    image = source.read_bytes()
    if len(image) != SOURCE_SIZE or sha256(image) != SOURCE_SHA256:
        raise ValueError("source identity mismatch")
    exported = json.loads(graph.read_text(encoding="utf-8"))
    rows: list[dict[str, object]] = []
    for reference in exported["tail_direct_reference_sites"]:
        file_offset = int(reference["to_file_offset"], 16)
        if not TAIL_START <= file_offset < TAIL_END:
            raise ValueError(f"exported tail reference is outside declared tail: {file_offset:#x}")
        sample = image[file_offset:min(file_offset + 16, len(image))]
        rows.append({
            "from_va": reference["from_va"],
            "from_file_offset": reference["from_file_offset"],
            "to_va": reference["to_va"],
            "to_file_offset": reference["to_file_offset"],
            "mnemonic": reference["mnemonic"],
            "reference_type": reference["reference_type"],
            "owner_entry_va": reference["owner_entry_va"],
            "target_bytes_hex": sample.hex(),
            "target_bytes_all_ff": all(byte == 0xFF for byte in sample),
        })
    header_word = struct.unpack_from("<I", image, 0x10)[0]
    word_hits = [offset for offset in range(0, len(image) - 3, 4)
                 if struct.unpack_from("<I", image, offset)[0] == header_word]
    return {
        "source": {"size": len(image), "sha256": sha256(image)},
        "mapping": "file offset = logical VA + 0x200; hypothesis only",
        "tail": {"start": TAIL_START, "end_exclusive": TAIL_END, "size": TAIL_END - TAIL_START},
        "header_word_at_file_0x10": {"little_endian_u32": header_word, "aligned_word_occurrences": word_hits},
        "direct_reference_audit": rows,
        "ff_runs_at_least": {"minimum_size": minimum_run, "runs": ff_runs(image, minimum_run)},
        "limitations": [
            "Direct Ghidra references include analyzer-generated DATA/PARAM hypotheses and omit computed references.",
            "FF bytes, lack of a reference in this export, and a raw word occurrence do not prove free space, partition ownership, or executable mapping.",
            "The SPII header is outside the imported payload; this audit cannot establish BootROM header-field semantics.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Phase 5 tail-layout audit")
    parser.add_argument("source", type=Path)
    parser.add_argument("graph", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--minimum-run", type=lambda value: int(value, 0), default=0x20)
    args = parser.parse_args()
    report = audit(args.source, args.graph, args.minimum_run)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"references": len(report["direct_reference_audit"]), "ff_runs": len(report["ff_runs_at_least"]["runs"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
