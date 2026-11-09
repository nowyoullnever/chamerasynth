import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class Phase5EvidenceTests(unittest.TestCase):
    def test_event_export_contains_proven_update_relay_sites(self):
        graph = json.loads((ROOT / "work" / "phase5-event" / "phase5_event_graph.json").read_text(encoding="utf-8"))
        scalar_hits = graph["scalar_hits"]
        self.assertTrue(any(hit["instruction_va"] == "0x00006438" and hit["value"] == "0x108" for hit in scalar_hits))
        self.assertTrue(any(hit["instruction_va"] == "0x00025674" and hit["value"] == "0x100" for hit in scalar_hits))

    def test_audio_export_has_resource_and_request_chain_artifacts(self):
        graph = json.loads((ROOT / "work" / "phase5-audio" / "audio_handle_graph.json").read_text(encoding="utf-8"))
        entries = {item["requested_va"]: item for item in graph["functions"]}
        self.assertIn("0x0001e234", entries)
        self.assertIn("0x0001e844", entries)
        self.assertIn("0x0001e970->0x00025984", entries["0x0001e844"]["direct_call_edges"])

    def test_manifest_stays_analysis_only_after_tail_audit(self):
        manifest = (ROOT / "patches" / "manifest.example.toml").read_text(encoding="utf-8")
        self.assertIn('status = "analysis-only"', manifest)
        self.assertIn("Phase 5 audited 26 direct Ghidra references", manifest)
