#!/usr/bin/env python3
"""Offline-only manifest validator and experimental firmware patch tool.

It has no device, USB, serial, SD-card, or network code.  A modified image can
only be written when a manifest declares `experimental-qualified`, every
insertion range is explicitly reviewed, and --allow-experimental is supplied.
It never overwrites the input image and never truncates it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ARM_ALIGNMENT = 4
ARM_BRANCH_MIN = -(1 << 25)
ARM_BRANCH_MAX = (1 << 25) - 4


class ValidationError(ValueError):
    """Input is incomplete, unsafe, or does not match its declared evidence."""


@dataclass(frozen=True)
class ByteRange:
    offset: int
    size: int
    name: str

    @property
    def end(self) -> int:
        return self.offset + self.size

    def overlaps(self, other: "ByteRange") -> bool:
        return self.offset < other.end and other.offset < self.end


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_hex(value: str, label: str) -> bytes:
    try:
        return bytes.fromhex(value)
    except ValueError as error:
        raise ValidationError(f"{label}: invalid hexadecimal bytes") from error


def checked_range(offset: int, size: int, length: int, name: str) -> ByteRange:
    if not isinstance(offset, int) or not isinstance(size, int) or offset < 0 or size <= 0:
        raise ValidationError(f"{name}: offset must be >= 0 and size must be > 0")
    result = ByteRange(offset, size, name)
    if result.end > length:
        raise ValidationError(f"{name}: range 0x{offset:x}..0x{result.end - 1:x} exceeds image")
    return result


def encode_arm_branch(site: int, target: int, *, link: bool = False) -> bytes:
    """Encode A32 B/BL. Both addresses must be aligned; target is absolute VA."""
    if site % ARM_ALIGNMENT or target % ARM_ALIGNMENT:
        raise ValidationError("A32 branch site and target must be 4-byte aligned")
    delta = target - (site + 8)
    if delta % 4 or not ARM_BRANCH_MIN <= delta <= ARM_BRANCH_MAX:
        raise ValidationError("A32 branch target is outside the ±32 MiB direct-branch range")
    instruction = (0xEB000000 if link else 0xEA000000) | ((delta >> 2) & 0x00FFFFFF)
    return instruction.to_bytes(4, "little")


def decode_arm_branch(word: int, site: int) -> tuple[bool, int]:
    if (word & 0x0E000000) != 0x0A000000:
        raise ValidationError(f"0x{word:08x} is not an A32 B/BL instruction")
    imm24 = word & 0x00FFFFFF
    if imm24 & 0x00800000:
        imm24 -= 0x01000000
    return bool(word & 0x01000000), site + 8 + imm24 * 4


def disassemble_a32_words(data: bytes, file_offset: int) -> list[dict[str, Any]]:
    """Small verifier, intentionally not a claimed full ARM disassembler."""
    if len(data) % 4:
        raise ValidationError("A32 inspection region is not a multiple of four bytes")
    lines: list[dict[str, Any]] = []
    for index in range(0, len(data), 4):
        word = int.from_bytes(data[index:index + 4], "little")
        site = file_offset + index
        text = f".word 0x{word:08x}"
        if (word & 0x0E000000) == 0x0A000000:
            link, target = decode_arm_branch(word, site)
            text = f"{'bl' if link else 'b'} 0x{target:08x}"
        elif word == 0xE12FFF1E:
            text = "bx lr"
        elif word == 0xE1A00000:
            text = "nop (mov r0, r0)"
        lines.append({"file_offset": site, "word_le": f"{word:08x}", "text": text})
    return lines


def inspect_update_filename(filename: str) -> dict[str, str]:
    """Parse only the observed filename shape; this does not validate an updater."""
    if len(filename) != 32 or not filename.startswith("JH_5408") or filename[19] != "_" or filename[28:].lower() != ".bin":
        raise ValidationError("filename is not JH_5408<YYYYMMDDhhmm>_<8HEX>.bin")
    timestamp, checksum = filename[7:19], filename[20:28]
    if not timestamp.isdigit() or any(char not in "0123456789abcdefABCDEF" for char in checksum):
        raise ValidationError("filename timestamp/checksum fields are malformed")
    return {"timestamp": timestamp, "checksum_hex": checksum.upper()}


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        manifest = tomllib.load(stream)
    if manifest.get("schema_version") != 1:
        raise ValidationError("only schema_version = 1 is supported")
    source = manifest.get("source", {})
    if not isinstance(source.get("size"), int) or len(str(source.get("sha256", ""))) != 64:
        raise ValidationError("manifest source.size and 64-hex source.sha256 are required")
    return manifest


def validate_source(manifest: dict[str, Any], image: bytes) -> None:
    source = manifest["source"]
    if len(image) != source["size"]:
        raise ValidationError(f"source size mismatch: got 0x{len(image):x}, expected 0x{source['size']:x}")
    actual = sha256_bytes(image)
    if actual.lower() != source["sha256"].lower():
        raise ValidationError(f"source SHA-256 mismatch: got {actual}")


def validate_manifest_layout(manifest: dict[str, Any], image: bytes) -> list[ByteRange]:
    length = len(image)
    mapping = manifest.get("mapping", {})
    if mapping.get("instruction_alignment", ARM_ALIGNMENT) != ARM_ALIGNMENT:
        raise ValidationError("only 4-byte A32 instruction alignment is supported")
    protected = [checked_range(item["offset"], item["size"], length, item.get("name", "protected"))
                 for item in manifest.get("protected_ranges", [])]
    regions: list[ByteRange] = []
    for item in manifest.get("injection_regions", []):
        region = checked_range(item["offset"], item["size"], length, item.get("name", "injection"))
        if region.offset % ARM_ALIGNMENT or region.size % ARM_ALIGNMENT:
            raise ValidationError(f"{region.name}: injection range must be A32 aligned")
        if any(region.overlaps(blocked) for blocked in protected):
            raise ValidationError(f"{region.name}: overlaps a protected range")
        fill = parse_hex(item.get("expected_fill", "ff"), f"{region.name}.expected_fill")
        if len(fill) != 1 or any(byte != fill[0] for byte in image[region.offset:region.end]):
            raise ValidationError(f"{region.name}: image does not contain the declared uniform fill")
        regions.append(region)
    return regions


def require_experimental_manifest(manifest: dict[str, Any], allow: bool) -> None:
    if not allow or manifest.get("status") != "experimental-qualified":
        raise ValidationError("refusing image output: needs --allow-experimental and status = experimental-qualified")
    if not manifest.get("patches"):
        raise ValidationError("refusing image output: manifest has no patches")
    for region in manifest.get("injection_regions", []):
        if region.get("trust") != "reviewed":
            raise ValidationError(f"refusing image output: {region.get('name', 'region')} is not reviewed")


def patch_bytes(manifest: dict[str, Any], image: bytes) -> tuple[bytes, list[dict[str, Any]]]:
    mapping = manifest.get("mapping", {})
    base = mapping.get("payload_runtime_base")
    file_payload = mapping.get("payload_file_offset")
    if not isinstance(base, int) or not isinstance(file_payload, int):
        raise ValidationError("mapping payload_runtime_base and payload_file_offset are required")
    protected = [checked_range(item["offset"], item["size"], len(image), item.get("name", "protected"))
                 for item in manifest.get("protected_ranges", [])]
    planned: list[tuple[ByteRange, bytes, bytes, dict[str, Any]]] = []
    for index, item in enumerate(manifest.get("patches", [])):
        name = item.get("name", f"patch-{index}")
        site = item.get("file_offset")
        expected = parse_hex(item.get("expected_hex", ""), f"{name}.expected_hex")
        if not isinstance(site, int) or not expected:
            raise ValidationError(f"{name}: file_offset and expected_hex are required")
        entry = checked_range(site, len(expected), len(image), name)
        if entry.offset % ARM_ALIGNMENT or entry.size % ARM_ALIGNMENT:
            raise ValidationError(f"{name}: A32 patch must be 4-byte aligned")
        if any(entry.overlaps(blocked) for blocked in protected):
            raise ValidationError(f"{name}: overlaps protected range")
        if image[entry.offset:entry.end] != expected:
            raise ValidationError(f"{name}: expected original bytes do not match")
        if "replacement_hex" in item:
            replacement = parse_hex(item["replacement_hex"], f"{name}.replacement_hex")
        elif "branch_target_file_offset" in item:
            if mapping.get("runtime_mapping_confidence") != "verified":
                raise ValidationError(f"{name}: file-offset to runtime mapping is not verified for a branch patch")
            target_file = item["branch_target_file_offset"]
            if not isinstance(target_file, int):
                raise ValidationError(f"{name}: branch target must be an integer file offset")
            site_va = base + (entry.offset - file_payload)
            target_va = base + (target_file - file_payload)
            replacement = encode_arm_branch(site_va, target_va, link=bool(item.get("link", False)))
        else:
            raise ValidationError(f"{name}: replacement_hex or branch_target_file_offset is required")
        if len(replacement) != entry.size:
            raise ValidationError(f"{name}: replacement length differs from expected original length")
        planned.append((entry, expected, replacement, item))
    for position, left in enumerate(planned):
        if any(left[0].overlaps(right[0]) for right in planned[position + 1:]):
            raise ValidationError("patch ranges overlap")
    modified = bytearray(image)
    report: list[dict[str, Any]] = []
    for entry, expected, replacement, item in planned:
        modified[entry.offset:entry.end] = replacement
        report.append({"name": entry.name, "file_offset": entry.offset, "expected_hex": expected.hex(),
                       "replacement_hex": replacement.hex(), "a32": disassemble_a32_words(replacement, entry.offset)})
    return bytes(modified), report


def find_llvm(name: str) -> str:
    fixed = Path(r"C:\Program Files\LLVM\bin") / name
    if fixed.is_file():
        return str(fixed)
    found = shutil.which(name)
    if not found:
        raise ValidationError(f"required local LLVM tool not found: {name}")
    return found


def assemble_a32(source: Path, output_dir: Path) -> dict[str, str]:
    if not source.is_file():
        raise ValidationError(f"assembly source not found: {source}")
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = source.stem
    obj = output_dir / f"{stem}.o"
    elf = output_dir / f"{stem}.elf"
    raw = output_dir / f"{stem}.text.bin"
    listing = output_dir / f"{stem}.objdump.txt"
    clang = find_llvm("clang.exe")
    linker = find_llvm("ld.lld.exe")
    objcopy = find_llvm("llvm-objcopy.exe")
    objdump = find_llvm("llvm-objdump.exe")
    commands = [
        [clang, "--target=arm-none-eabi", "-march=armv4t", "-marm", "-c", str(source), "-o", str(obj)],
        # A relocatable object cannot be injected: unresolved R_ARM_CALL values
        # make its raw bytes branch to the wrong place. Link at zero only to
        # resolve internal relative branches; callers must still validate their
        # actual injection address and hook branch separately.
        [linker, "-m", "armelf", "--image-base=0", "--entry=synth_entry", "--Ttext=0", "-o", str(elf), str(obj)],
        [objcopy, "-O", "binary", "--only-section=.text", str(elf), str(raw)],
        [objdump, "-d", str(elf)],
    ]
    try:
        subprocess.run(commands[0], check=True, capture_output=True, text=True)
        subprocess.run(commands[1], check=True, capture_output=True, text=True)
        subprocess.run(commands[2], check=True, capture_output=True, text=True)
        listing.write_text(subprocess.run(commands[3], check=True, capture_output=True, text=True).stdout, encoding="utf-8")
    except subprocess.CalledProcessError as error:
        raise ValidationError(error.stderr.strip() or "local ARM assembly failed") from error
    return {"object": str(obj), "linked_elf": str(elf), "text": str(raw), "objdump": str(listing), "text_sha256": sha256_bytes(raw.read_bytes())}


def command_verify(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    image = args.firmware.read_bytes()
    validate_source(manifest, image)
    regions = validate_manifest_layout(manifest, image)
    print(json.dumps({"valid": True, "source_sha256": sha256_bytes(image), "injection_regions": [r.__dict__ for r in regions],
                      "status": manifest.get("status")}, indent=2))
    return 0


def command_assemble(args: argparse.Namespace) -> int:
    print(json.dumps(assemble_a32(args.source, args.output_dir), indent=2))
    return 0


def command_apply(args: argparse.Namespace) -> int:
    if args.output.resolve() == args.firmware.resolve():
        raise ValidationError("output must differ from immutable source image")
    manifest = load_manifest(args.manifest)
    image = args.firmware.read_bytes()
    validate_source(manifest, image)
    validate_manifest_layout(manifest, image)
    require_experimental_manifest(manifest, args.allow_experimental)
    modified, patch_report = patch_bytes(manifest, image)
    if len(modified) != len(image):
        raise ValidationError("internal error: patch changed image size")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(modified)
    report = {"source_sha256": sha256_bytes(image), "modified_sha256": sha256_bytes(modified), "source_size": len(image), "patches": patch_report}
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


def command_revert(args: argparse.Namespace) -> int:
    modified = args.modified.read_bytes()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    if sha256_bytes(modified) != report["modified_sha256"]:
        raise ValidationError("modified image does not match patch report")
    restored = bytearray(modified)
    for patch in report["patches"]:
        old = parse_hex(patch["expected_hex"], patch["name"])
        new = parse_hex(patch["replacement_hex"], patch["name"])
        offset = patch["file_offset"]
        if restored[offset:offset + len(new)] != new:
            raise ValidationError(f"{patch['name']}: modified bytes do not match report")
        restored[offset:offset + len(old)] = old
    if sha256_bytes(bytes(restored)) != report["source_sha256"]:
        raise ValidationError("reversion did not reproduce the declared source hash")
    args.output.write_bytes(restored)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline Phase 2 firmware patch validator")
    sub = parser.add_subparsers(required=True)
    verify = sub.add_parser("verify", help="validate identity and manifest bounds only")
    verify.add_argument("manifest", type=Path); verify.add_argument("firmware", type=Path); verify.set_defaults(func=command_verify)
    assemble = sub.add_parser("assemble", help="assemble an offline A32 object; no firmware is changed")
    assemble.add_argument("source", type=Path); assemble.add_argument("output_dir", type=Path); assemble.set_defaults(func=command_assemble)
    apply = sub.add_parser("apply", help="write a separate experimental image only after strict gates")
    apply.add_argument("manifest", type=Path); apply.add_argument("firmware", type=Path); apply.add_argument("output", type=Path); apply.add_argument("report", type=Path)
    apply.add_argument("--allow-experimental", action="store_true"); apply.set_defaults(func=command_apply)
    revert = sub.add_parser("revert", help="restore a separately modified image using its report")
    revert.add_argument("modified", type=Path); revert.add_argument("report", type=Path); revert.add_argument("output", type=Path); revert.set_defaults(func=command_revert)
    args = parser.parse_args()
    try:
        return args.func(args)
    except (OSError, ValidationError, tomllib.TOMLDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

