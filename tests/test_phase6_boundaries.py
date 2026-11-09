import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class Phase6BoundaryTests(unittest.TestCase):
    def test_follow_up_exporter_targets_event_and_audio_blockers(self):
        script = (ROOT / "ghidra_scripts" / "ExportPhase6Boundaries.java").read_text(encoding="utf-8")
        for address in ("0x25984", "0x8f67c", "0x63b0", "0x1c9c4", "0x12f0c", "0x133f0"):
            self.assertIn(address, script)
        self.assertIn("hypothesis only", script)

    def test_phase6_reports_preserve_no_patch_and_no_hardware_boundary(self):
        reports = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "docs").glob("phase6_*.md"))
        self.assertIn("No safe binary hook", reports)
        self.assertIn("No executable injection region is approved", reports)
        self.assertIn("No retained evidence proves", reports)
