import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.prepare_ghidra_payload import PAYLOAD_OFFSET, SOURCE_SHA256, SOURCE_SIZE, prepare


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "references" / "Project-Sirius" / "Original_Firmware.bin"
GRAPH = ROOT / "work" / "ghidra" / "exports" / "function_graph.json"
PHASE4_APP_GRAPH = ROOT / "work" / "ghidra" / "exports" / "phase4-app" / "phase4_application_graph.json"
PHASE4_UPDATER_GRAPH = ROOT / "work" / "ghidra" / "phase4_updater" / "updater_deep.json"
PHASE4_DRIVER_GRAPH = ROOT / "work" / "phase4-driver-tail" / "driver_tail_graph.json"


class GhidraPipelineTests(unittest.TestCase):
    def test_preparation_locks_identity_and_never_mutates_source(self):
        before = SOURCE.read_bytes()
        self.assertEqual(len(before), SOURCE_SIZE)
        self.assertEqual(hashlib.sha256(before).hexdigest(), SOURCE_SHA256)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "payload.bin"
            metadata = root / "mapping.json"
            report = prepare(SOURCE, payload, metadata)
            self.assertEqual(SOURCE.read_bytes(), before)
            self.assertEqual(payload.read_bytes(), before[PAYLOAD_OFFSET:])
            self.assertEqual(report["payload_size"], SOURCE_SIZE - PAYLOAD_OFFSET)
            self.assertEqual(json.loads(metadata.read_text(encoding="utf-8"))["candidate_load_address"], "0x00000000")

    def test_scripts_pin_raw_a32_import_and_export_mapping(self):
        runner = (ROOT / "tools" / "run_ghidra_analysis.ps1").read_text(encoding="utf-8")
        exporter = (ROOT / "ghidra_scripts" / "ExportCharmeraAnalysis.java").read_text(encoding="utf-8")
        self.assertIn("-loader BinaryLoader", runner)
        self.assertIn("-loader-baseAddr 0x0", runner)
        self.assertIn("ARM:LE:32:v4t", runner)
        self.assertIn("PAYLOAD_FILE_OFFSET = 0x200", exporter)
        self.assertIn("direct_call_edges", exporter)

    def test_actual_export_has_expected_mapping_edges_and_boundary_warning(self):
        self.assertTrue(GRAPH.is_file(), "run tools/run_ghidra_analysis.ps1 before this test")
        graph = json.loads(GRAPH.read_text(encoding="utf-8"))
        self.assertIn("va + 0x200", graph["mapping"])
        functions = {entry["seed_file_offset"]: entry for entry in graph["functions"]}
        self.assertIn("0x0002db70->0x00036074", functions["0x02dd48"]["direct_call_edges"])
        self.assertEqual(functions["0x0065b0"]["callers"], ["0x00025668"])
        self.assertEqual(functions["0x036274"]["body_min_va"], "0x00030ed0")
        self.assertIn("0x000215b8->0x00001b20", functions["0x0217b4"]["direct_call_edges"])

    def test_phase4_exports_prove_shared_loop_dispatch_and_spi_opcodes(self):
        for path in (PHASE4_APP_GRAPH, PHASE4_UPDATER_GRAPH, PHASE4_DRIVER_GRAPH):
            self.assertTrue(path.is_file(), f"missing focused Phase 4 export: {path}")
        app = json.loads(PHASE4_APP_GRAPH.read_text(encoding="utf-8"))
        by_va = {item["target_va"]: item for item in app["targets"]}
        loop = by_va["0x00025668"]
        self.assertIn("0x0002572c->0x000063b0", loop["direct_call_edges"])
        updater = by_va["0x000257b8"]
        self.assertIn("0x000257b8->0x00021170", updater["direct_call_edges"])
        deep = json.loads(PHASE4_UPDATER_GRAPH.read_text(encoding="utf-8"))
        erase = next(item for item in deep["functions"] if item["seed_va"] == "0x0003060c")
        self.assertIn("0x0003066c mov r0,#0xd8", erase["instructions"])

    def test_machine_readable_update_table_preserves_static_limits(self):
        table = json.loads((ROOT / "docs" / "phase4_update_operations.json").read_text(encoding="utf-8"))
        ops = {item["name"]: item for item in table["operations"]}
        self.assertEqual(ops["erase_64k"]["opcode"], "0xd8")
        self.assertEqual(ops["program_256"]["transfer_bytes"], 256)
        self.assertIn("Physical flash capacity", table["limitations"][0])

