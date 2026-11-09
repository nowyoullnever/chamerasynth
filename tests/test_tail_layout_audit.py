import json
import tempfile
import unittest
from pathlib import Path

from tools.audit_tail_layout import audit


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "references" / "Project-Sirius" / "Original_Firmware.bin"
GRAPH = ROOT / "work" / "phase4-driver-tail" / "driver_tail_graph.json"


class TailLayoutAuditTests(unittest.TestCase):
    def test_tail_audit_preserves_identity_and_marks_all_exported_targets(self):
        before = SOURCE.read_bytes()
        result = audit(SOURCE, GRAPH, 0x20)
        self.assertEqual(SOURCE.read_bytes(), before)
        self.assertEqual(result["source"]["size"], 0x200000)
        self.assertEqual(result["header_word_at_file_0x10"]["little_endian_u32"], 0x001B0000)
        self.assertEqual(len(result["direct_reference_audit"]), 26)
        self.assertTrue(all(item["target_bytes_all_ff"] for item in result["direct_reference_audit"]))
        self.assertTrue(any(run["file_offset"] == 0x1AEE00 for run in result["ff_runs_at_least"]["runs"]))

    def test_audit_result_is_json_serializable(self):
        result = audit(SOURCE, GRAPH, 0x100)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.json"
            path.write_text(json.dumps(result), encoding="utf-8")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["tail"]["start"], 0x1AEE00)
