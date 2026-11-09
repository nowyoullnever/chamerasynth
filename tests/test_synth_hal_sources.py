import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SynthHalSourceTests(unittest.TestCase):
    def test_hal_and_synth_sources_compile_as_host_c11_objects(self):
        compiler = shutil.which("clang") or shutil.which("gcc")
        if compiler is None:
            self.skipTest("no host C compiler available")
        sources = [
            ROOT / "firmware" / "hal" / "audio_hal.c",
            ROOT / "firmware" / "synth" / "synth_main.c",
            ROOT / "firmware" / "synth" / "synth_event_integration.c",
        ]
        with tempfile.TemporaryDirectory() as directory:
            for source in sources:
                result = subprocess.run(
                    [compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-c", str(source), "-o", str(Path(directory) / (source.stem + ".o"))],
                    cwd=ROOT,
                    check=False,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_c_boundary_never_bakes_in_stock_addresses_or_mmio(self):
        corpus = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "firmware" / "hal").glob("*.c")
        ) + "\n" + "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "firmware" / "synth").glob("*.c")
        )
        self.assertNotIn("0x1e844", corpus)
        self.assertNotIn("0x12f0c", corpus)
        self.assertNotIn("MMIO", corpus)
        self.assertNotIn("int16_t", corpus)
