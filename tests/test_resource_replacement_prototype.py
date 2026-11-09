import hashlib
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.resource_replacement_prototype import ResourcePrototypeError, replace


class ResourceReplacementPrototypeTests(unittest.TestCase):
    def _manifest(self, image):
        return {"status": "analysis-only", "source": {"size": len(image), "sha256": hashlib.sha256(image).hexdigest()}, "resource": {"file_offset": 8, "expected_hex": image[8:12].hex(), "replacement_hex": "a1a2a3a4", "required_alignment": 4}, "metadata_updates": [{"file_offset": 20, "expected_hex": image[20:22].hex(), "replacement_hex": "9901"}]}

    def test_copy_changes_only_declared_ranges(self):
        image = bytes(range(32))
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "source.bin"; output = root / "candidate.bin"; source.write_bytes(image)
            report = replace(source, output, self._manifest(image)); candidate = output.read_bytes()
        self.assertTrue(report["unrelated_bytes_unchanged"]); self.assertFalse(report["flash_ready"])
        self.assertEqual(candidate[8:12], bytes.fromhex("a1a2a3a4")); self.assertEqual(candidate[20:22], bytes.fromhex("9901"))
        self.assertEqual(candidate[:8] + candidate[12:20] + candidate[22:], image[:8] + image[12:20] + image[22:])

    def test_rejects_wrong_identity_or_unproven_alignment(self):
        image = bytes(range(32))
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "source.bin"; source.write_bytes(image); manifest = self._manifest(image)
            manifest["source"]["sha256"] = "00" * 32
            with self.assertRaises(ResourcePrototypeError): replace(source, root / "candidate.bin", manifest)
            manifest = self._manifest(image); manifest["resource"]["required_alignment"] = 16
            with self.assertRaises(ResourcePrototypeError): replace(source, root / "candidate.bin", manifest)
