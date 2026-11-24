from pathlib import Path
from types import SimpleNamespace
import json
import tempfile
import unittest
from unittest.mock import patch

from cad_library_ci.runtime import execute


class EngineBatchTests(unittest.TestCase):
    def test_one_child_for_two_rows_and_parent_verification(self):
        rows = [{"id": item, "builder": "test", "engine_python": "/opt/isolated/bin/python",
                 "build_entry": "builder:build", "verify_entry": "verifier:run",
                 "adapter": "mesh", "source": "source", "definition": "definition"}
                for item in ("a", "b")]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def run(command, **kwargs):
                self.assertEqual(command[0], "/opt/isolated/bin/python")
                manifest = json.loads(Path(command[command.index("--manifest") + 1]).read_text())
                self.assertEqual(len(manifest["examples"]), 2)
                for row in rows:
                    (root / "examples" / row["id"] / "model.stl").write_bytes(b"stl")
                Path(command[command.index("--build-report") + 1]).write_text(
                    json.dumps({"schema": 1, "results": {row["id"]: {"status": "pass"} for row in rows}}))
                return SimpleNamespace(returncode=0)
            with patch("cad_library_ci.runtime.subprocess.run", side_effect=run) as child, patch("cad_library_ci.runtime.resolve", return_value=lambda *a, **kw: {"status": "pass"}) as resolve:
                self.assertEqual(execute({"schema": 1, "runtime": "reference", "image": "test:1", "examples": rows}, root), 0)
                child.assert_called_once()
                self.assertEqual(resolve.call_count, 2)

    def test_missing_child_report_fails_batch(self):
        row = {"id": "a", "builder": "test", "engine_python": "/opt/test/python",
               "build_entry": "builder:build", "verify_entry": "verifier:run"}
        with tempfile.TemporaryDirectory() as tmp:
            with patch("cad_library_ci.runtime.subprocess.run", return_value=SimpleNamespace(returncode=0)):
                self.assertEqual(execute({"schema": 1, "runtime": "reference", "image": "test:1", "examples": [row]}, Path(tmp)), 1)
