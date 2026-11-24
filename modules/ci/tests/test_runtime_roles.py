from types import SimpleNamespace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cad_library_ci.batch import runtime_order, run_batches
from cad_library_ci.config import load_project
from cad_library_ci.items import discover_modules
from cad_library_ci.examples import discover_examples


class RuntimeRoleTests(unittest.TestCase):
    def test_solidcraft_precedes_reference_and_each_role_runs_once(self):
        repo = Path.cwd()
        project = load_project(repo)
        modules = discover_modules(repo, project)
        examples = discover_examples(repo, modules)
        solidcraft = next(e for e in examples if e.id == "simple-box-solidcraft")
        cadquery = next(e for e in examples if e.id == "simple-box-cadquery")
        self.assertEqual(runtime_order((solidcraft, cadquery)), ("solidcraft", "reference"))
        with tempfile.TemporaryDirectory() as tmp:
            calls = []
            def run(command, **kwargs):
                manifest_path = next(v.split(":/manifest.json:ro")[0] for v in command if v.endswith(":/manifest.json:ro"))
                manifest = json.loads(Path(manifest_path).read_text())
                calls.append(manifest)
                return SimpleNamespace(returncode=0)
            with patch("cad_library_ci.batch.subprocess.run", side_effect=run):
                run_batches(repo, project, modules, (solidcraft, cadquery), Path(tmp))
            self.assertEqual([m["runtime"] for m in calls], ["solidcraft", "reference"])
            self.assertEqual([r["id"] for r in calls[0]["build_examples"]], ["simple-box-solidcraft"])
            self.assertEqual([r["id"] for r in calls[0]["verify_examples"]], [])
            self.assertEqual({r["id"] for r in calls[1]["build_examples"]}, {"simple-box-cadquery"})
            self.assertEqual({r["id"] for r in calls[1]["verify_examples"]}, {"simple-box-cadquery", "simple-box-solidcraft"})
