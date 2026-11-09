#!/usr/bin/env python3
"""Analysis-only fixed-allocation resource replacement prototype.

No Charmera offsets, container format, checksum, or padding rule is encoded.
An evidence-backed manifest must declare every changed byte range and validate
the source identity before a separate candidate copy is written.
"""
from __future__ import annotations

import hashlib
import json
import argparse
from dataclasses import dataclass
from pathlib import Path


class ResourcePrototypeError(ValueError):
    pass


@dataclass(frozen=True)
class RangeUpdate:
    offset: int
    expected: bytes
    replacement: bytes

    @property
    def end(self) -> int:
        return self.offset + len(self.expected)


def _update(row: dict, label: str) -> RangeUpdate:
    try:
        offset = row["file_offset"]
        expected = bytes.fromhex(row["expected_hex"])
        replacement = bytes.fromhex(row["replacement_hex"])
    except (KeyError, TypeError, ValueError) as error:
        raise ResourcePrototypeError(f"invalid {label}") from error
    if not isinstance(offset, int) or offset < 0 or not expected or len(expected) != len(replacement):
        raise ResourcePrototypeError(f"invalid {label}")
    return RangeUpdate(offset, expected, replacement)


def replace(source_path: Path, output_path: Path, manifest: dict) -> dict:
    if manifest.get("status") != "analysis-only":
        raise ResourcePrototypeError("manifest must remain analysis-only")
    source_spec = manifest.get("source", {})
    resource = _update(manifest.get("resource", {}), "resource")
    alignment = manifest.get("resource", {}).get("required_alignment")
    if not isinstance(alignment, int) or alignment <= 0 or resource.offset % alignment:
        raise ResourcePrototypeError("resource alignment is not proven")
    metadata = [_update(row, "metadata update") for row in manifest.get("metadata_updates", [])]
    updates = [resource, *metadata]
    if source_path.resolve() == output_path.resolve():
        raise ResourcePrototypeError("output must be a separate copy")
    original = source_path.read_bytes()
    if len(original) != source_spec.get("size") or hashlib.sha256(original).hexdigest().lower() != str(source_spec.get("sha256", "")).lower():
        raise ResourcePrototypeError("source identity does not match manifest")
    for left_index, left in enumerate(updates):
        if left.end > len(original) or original[left.offset:left.end] != left.expected:
            raise ResourcePrototypeError("expected source bytes do not match")
        for right in updates[left_index + 1:]:
            if max(left.offset, right.offset) < min(left.end, right.end):
                raise ResourcePrototypeError("declared ranges overlap")
    modified = bytearray(original)
    for update in updates:
        modified[update.offset:update.end] = update.replacement
    allowed = {byte for update in updates for byte in range(update.offset, update.end)}
    changed = {index for index, (before, after) in enumerate(zip(original, modified)) if before != after}
    if not changed.issubset(allowed):
        raise ResourcePrototypeError("unrelated byte changed")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(modified)
    return {"status": "analysis-only-copy", "flash_ready": False, "changed_byte_count": len(changed), "unrelated_bytes_unchanged": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = replace(args.source, args.output, json.loads(args.manifest.read_text(encoding="utf-8")))
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
