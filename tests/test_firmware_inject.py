import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import tomllib

from tools.firmware_inject import (
    ValidationError,
    assemble_a32,
    decode_arm_branch,
    encode_arm_branch,
    inspect_update_filename,
    patch_bytes,
    require_experimental_manifest,
    validate_manifest_layout,
    validate_source,
)


def manifest_for(image, *, status="experimental-qualified", regions=None, protected=None, patches=None):
    return {
        "schema_version": 1,
        "status": status,
        "source": {"size": len(image), "sha256": hashlib.sha256(image).hexdigest()},
        "mapping": {"payload_file_offset": 0, "payload_runtime_base": 0, "instruction_alignment": 4,
                    "runtime_mapping_confidence": "verified"},
        "injection_regions": regions or [],
        "protected_ranges": protected or [],
        "patches": patches or [],
    }


class FirmwareInjectTests(unittest.TestCase):
    def test_a32_branch_round_trip_and_range_checks(self):
        encoded = encode_arm_branch(0x100, 0x200)
        link, target = decode_arm_branch(int.from_bytes(encoded, "little"), 0x100)
        self.assertFalse(link)
        self.assertEqual(target, 0x200)
        with self.assertRaises(ValidationError):
            encode_arm_branch(0x100, 0x102)
        with self.assertRaises(ValidationError):
            encode_arm_branch(0, 0x2000008)

    def test_source_identity_and_non_ff_insertion_checks(self):
        image = b"\xff" * 64
        good = manifest_for(image, regions=[{"name": "tail", "offset": 32, "size": 32, "expected_fill": "ff", "trust": "reviewed"}])
        validate_source(good, image)
        validate_manifest_layout(good, image)
        with self.assertRaises(ValidationError):
            validate_source(good, image[:-1])
        image = image[:40] + b"\x00" + image[41:]
        bad = manifest_for(image, regions=[{"name": "tail", "offset": 32, "size": 32, "expected_fill": "ff", "trust": "reviewed"}])
        with self.assertRaises(ValidationError):
            validate_manifest_layout(bad, image)

    def test_protected_overlap_and_expected_bytes_rejected(self):
        image = b"\x00" * 64
        protected = [{"name": "boot", "offset": 0, "size": 16}]
        overlapping = manifest_for(image, protected=protected, patches=[{"name": "bad", "file_offset": 0, "expected_hex": "00000000", "replacement_hex": "00000000"}])
        with self.assertRaises(ValidationError):
            patch_bytes(overlapping, image)
        mismatch = manifest_for(image, patches=[{"name": "bad", "file_offset": 16, "expected_hex": "ffffffff", "replacement_hex": "00000000"}])
        with self.assertRaises(ValidationError):
            patch_bytes(mismatch, image)

    def test_patch_and_byte_level_restoration(self):
        image = bytearray(b"\xff" * 64)
        image[16:20] = b"\x00\x00\xa0\xe1"  # A32 nop
        original = bytes(image)
        manifest = manifest_for(original, protected=[{"name": "protected-prefix", "offset": 0, "size": 16}],
                                patches=[{"name": "test-branch", "file_offset": 16, "expected_hex": "0000a0e1", "branch_target_file_offset": 32}])
        modified, report = patch_bytes(manifest, original)
        self.assertEqual(len(modified), len(original))
        self.assertNotEqual(modified, original)
        self.assertEqual(modified[:16], original[:16])
        restored = bytearray(modified)
        for item in report:
            old = bytes.fromhex(item["expected_hex"])
            restored[item["file_offset"]:item["file_offset"] + len(old)] = old
        self.assertEqual(bytes(restored), original)

    def test_unresolved_manifest_cannot_write_an_image(self):
        image = b"\xff" * 64
        manifest = manifest_for(image, status="analysis-only", patches=[{"name": "x", "file_offset": 0, "expected_hex": "ffffffff", "replacement_hex": "00000000"}])
        with self.assertRaises(ValidationError):
            require_experimental_manifest(manifest, True)
        manifest["status"] = "experimental-qualified"
        manifest["injection_regions"] = [{"name": "unreviewed", "offset": 32, "size": 32, "trust": "unverified"}]
        with self.assertRaises(ValidationError):
            require_experimental_manifest(manifest, True)

    def test_update_filename_shape_is_not_a_safety_verdict(self):
        self.assertEqual(inspect_update_filename("JH_5408202505201029_0F065D55.bin")["checksum_hex"], "0F065D55")
        with self.assertRaises(ValidationError):
            inspect_update_filename("JH_5408bad.bin")

    @unittest.skipUnless(Path("references/Project-Sirius/Original_Firmware.bin").is_file(), "authorized proprietary firmware is required for protected-range byte checks")
    def test_committed_manifest_protects_observed_updater_main(self):
        image = Path("references/Project-Sirius/Original_Firmware.bin").read_bytes()
        manifest = tomllib.loads(Path("patches/manifest.example.toml").read_text(encoding="utf-8"))
        manifest["status"] = "experimental-qualified"
        manifest["patches"] = [{"name": "updater-main", "file_offset": 0x21370,
                                "expected_hex": image[0x21370:0x21374].hex(), "replacement_hex": "0000a0e1"}]
        with self.assertRaises(ValidationError):
            patch_bytes(manifest, image)

    @unittest.skipUnless(Path("references/Project-Sirius/Original_Firmware.bin").is_file(), "authorized proprietary firmware is required for protected-range byte checks")
    def test_committed_manifest_protects_boot_to_event_loop_and_camera_dispatch(self):
        image = Path("references/Project-Sirius/Original_Firmware.bin").read_bytes()
        base = tomllib.loads(Path("patches/manifest.example.toml").read_text(encoding="utf-8"))
        for name, site in (("boot-dispatch", 0x2DD34), ("camera-dispatch", 0x2592C)):
            manifest = dict(base)
            manifest["status"] = "experimental-qualified"
            manifest["patches"] = [{"name": name, "file_offset": site,
                                    "expected_hex": image[site:site + 4].hex(), "replacement_hex": "0000a0e1"}]
            with self.assertRaises(ValidationError):
                patch_bytes(manifest, image)

    def test_local_llvm_assembles_and_disassembles_offline_stub(self):
        source = Path("firmware/synth_stub.S")
        with tempfile.TemporaryDirectory() as temp:
            result = assemble_a32(source, Path(temp))
            self.assertTrue(Path(result["text"]).read_bytes())
            self.assertIn("synth_entry", Path(result["objdump"]).read_text(encoding="utf-8"))

    def test_event_handler_abi_prototype_is_a_separate_offline_elf(self):
        source = Path("firmware/synth_event_handler_prototype.S")
        with tempfile.TemporaryDirectory() as temp:
            result = assemble_a32(source, Path(temp))
            listing = Path(result["objdump"]).read_text(encoding="utf-8")
            self.assertIn("synth_camera_event_handler", listing)
            self.assertIn("bx\tlr", listing)
            self.assertNotIn("\tbl\t", listing)

