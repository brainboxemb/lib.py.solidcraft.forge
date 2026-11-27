from pathlib import Path
from types import SimpleNamespace
import json
import tempfile
import unittest
from unittest.mock import patch

from cad_library_ci.batch import run_batches
from cad_library_ci.config import load_project
from cad_library_ci.items import discover_modules
from cad_library_ci.probe_run import _selection
from cad_library_ci.probes import discover_api_probes, select_api_probes


class ApiProbeTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path.cwd()
        self.project = load_project(self.repo)
        self.modules = discover_modules(self.repo, self.project)
        self.probes = discover_api_probes(
            self.repo,
            self.project,
            self.modules,
        )

    def test_baseline_probe_is_discoverable_but_selection_is_explicit(self):
        ids = [probe.id for probe in self.probes]
        self.assertIn("configuration-installed-current", ids)
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all((probe.root / "README.md").is_file()
                            for probe in self.probes))
        self.assertEqual(select_api_probes(self.probes, ()), ())
        self.assertEqual(
            [probe.id for probe in select_api_probes(
                self.probes,
                ("configuration-installed-current",),
            )],
            ["configuration-installed-current"],
        )

    def test_manual_probe_selection_accepts_ids_or_all(self):
        self.assertEqual(_selection("configuration-installed-current,other,configuration-installed-current"), ("configuration-installed-current", "other"))
        self.assertIsNone(_selection("all"))

    def test_probe_uses_own_output_root_in_runtime_manifest(self):
        manifests = []

        def run(command, **kwargs):
            path = next(
                item.split(":/manifest.json:ro")[0]
                for item in command
                if item.endswith(":/manifest.json:ro")
            )
            manifests.append(json.loads(Path(path).read_text()))
            return SimpleNamespace(returncode=0)

        with tempfile.TemporaryDirectory() as tmp:
            with patch(
                "cad_library_ci.batch.subprocess.run",
                side_effect=run,
            ) as invoked, patch(
                "cad_library_ci.batch._aggregate_probe",
                return_value=True,
            ):
                selected = select_api_probes(
                    self.probes,
                    ("configuration-installed-current",),
                )
                run_batches(
                    self.repo,
                    self.project,
                    self.modules,
                    (),
                    Path(tmp),
                    probes=selected,
                )

        self.assertEqual(invoked.call_count, 1)
        manifest = manifests[0]
        self.assertEqual(manifest["runtime"], "solidcraft")
        self.assertEqual(len(manifest["build_items"]), 1)
        row = manifest["build_items"][0]
        self.assertEqual(row["owner"], "configuration-installed-current")
        self.assertEqual(row["output_root"], "api-probes")
        self.assertEqual(row["implementation"], "probe")
        self.assertEqual(row["builder"], "builder-scpf")
        self.assertEqual(manifest["verify_items"], [])
        self.assertEqual(manifest["preview_items"], [])


if __name__ == "__main__":
    unittest.main()
