#!/usr/bin/env python3
"""Create an analysis-only payload copy for the Charmera Ghidra project."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SOURCE_SIZE = 0x200000
SOURCE_SHA256 = "720ed0b65c91b149b0916498732b0ecf40227736ef5e3c126c487a7b5253436c"
PAYLOAD_OFFSET = 0x200


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(source: Path, payload: Path, metadata: Path) -> dict[str, object]:
    if source.stat().st_size != SOURCE_SIZE or digest(source) != SOURCE_SHA256:
        raise ValueError("source is not the Phase 1 reference firmware")
    # Only this newly created analysis copy is written; source is opened read-only.
    data = source.read_bytes()[PAYLOAD_OFFSET:]
    payload.parent.mkdir(parents=True, exist_ok=True)
    metadata.parent.mkdir(parents=True, exist_ok=True)
    payload.write_bytes(data)
    report = {
        "source_path": str(source), "source_size": SOURCE_SIZE, "source_sha256": SOURCE_SHA256,
        "payload_path": str(payload), "payload_size": len(data), "payload_sha256": hashlib.sha256(data).hexdigest(),
        "source_file_offset_of_payload": PAYLOAD_OFFSET,
        "candidate_load_address": "0x00000000",
        "mapping": "file_offset = payload_va + 0x200; hypothesis only, not physical runtime proof",
    }
    metadata.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a read-only-derived Ghidra payload")
    parser.add_argument("source", type=Path)
    parser.add_argument("payload", type=Path)
    parser.add_argument("metadata", type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.payload, args.metadata), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

