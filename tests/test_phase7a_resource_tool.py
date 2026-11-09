import hashlib
import tempfile
import unittest
from pathlib import Path

from tools import phase7a_resource_tool as resource_tool


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "references" / "Project-Sirius" / "Original_Firmware.bin"


class Phase7AResourceToolTests(unittest.TestCase):
    def test_low_amplitude_tone_keeps_supported_pcm_shape(self):
        wav = {
            "riff_size": 4068, "total_size": 4076, "audio_format": 1, "channels": 1,
            "sample_rate": 11025, "byte_rate": 22050, "block_align": 2,
            "bits_per_sample": 16, "data_size": 4032,
        }
        replacement = resource_tool.low_amplitude_tone(wav)
        self.assertEqual(len(replacement), wav["total_size"])
        self.assertEqual(resource_tool.parse_wav(replacement), wav)
        self.assertNotEqual(replacement[44:], b"\0" * wav["data_size"])

    @unittest.skipUnless(SOURCE.is_file(), "authorized proprietary firmware is required for BEEP allocation validation")
    def test_verified_beep_candidate_is_range_limited_and_restorable(self):
        source = resource_tool.source_bytes(SOURCE)
        record = resource_tool.beep_record(source)
        self.assertEqual(record["index"], 4)
        self.assertEqual(record["file_offset"], 0x121E00)
        self.assertEqual(record["allocation_size"], 0x1000)
        self.assertEqual(record["resource_size"], 4076)
        replacement = resource_tool.low_amplitude_tone(record["wav"])
        manifest = resource_tool.manifest_for(source, replacement)
        candidate, validation = resource_tool.apply_candidate(source, manifest, replacement)
        changed = [index for index, (before, after) in enumerate(zip(source, candidate)) if before != after]
        self.assertTrue(changed)
        self.assertGreaterEqual(min(changed), manifest["file_offset"])
        self.assertLess(max(changed), manifest["file_offset"] + manifest["length"])
        self.assertTrue(validation["restoration_byte_identical"])
        self.assertNotEqual(hashlib.sha256(candidate).hexdigest(), hashlib.sha256(source).hexdigest())

    @unittest.skipUnless(SOURCE.is_file(), "authorized proprietary firmware is required for manifest rejection validation")
    def test_manifest_rejects_unproven_shift(self):
        source = resource_tool.source_bytes(SOURCE)
        replacement = resource_tool.low_amplitude_tone(resource_tool.beep_record(source)["wav"])
        manifest = resource_tool.manifest_for(source, replacement)
        manifest["file_offset"] += 1
        with self.assertRaises(ValueError):
            resource_tool.apply_candidate(source, manifest, replacement)
