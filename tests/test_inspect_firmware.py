import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.inspect_firmware import inspect


class FirmwareInspectionTests(unittest.TestCase):
    def test_reports_hash_size_and_offsets_without_writing_input(self):
        sample = b"ABCD" + b"hello-version" + b"\x1f\x8b\x08" + b"EFGH"
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "sample.bin"
            image.write_bytes(sample)
            before = image.read_bytes()
            result = inspect(image, window=8)
            self.assertEqual(result["size_bytes"], len(sample))
            self.assertEqual(result["sha256"], hashlib.sha256(sample).hexdigest())
            self.assertEqual(result["signature_hits"]["gzip"], [17])
            self.assertEqual(image.read_bytes(), before)

