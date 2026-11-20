"""Tests for versioned CADCraft verification diagram evidence."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "build_diagrams.py"
SOURCES = ROOT / "verification" / "diagrams" / "sources"
CI = ROOT / "ci" / "verification-diagrams" / "ci.yml"

EXPECTED = {
    "corner-bracket-depth.cadcraft.json",
    "corner-bracket-front-corners.cadcraft.json",
    "corner-bracket-goal.cadcraft.json",
    "corner-bracket-local-axes.cadcraft.json",
    "solidcraft-joint-anatomy.cadcraft.json",
    "solidcraft-joint-references.cadcraft.json",
}


def load_module():
    """Load the diagram renderer without making scripts a package."""

    spec = importlib.util.spec_from_file_location("build_diagrams", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DiagramEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.diagrams = load_module()

    def test_historical_six_source_set_is_versioned(self):
        paths = sorted(SOURCES.glob("*.cadcraft.json"))
        self.assertEqual({path.name for path in paths}, EXPECTED)

        for path in paths:
            with self.subTest(path=path.name):
                source = self.diagrams.load_source(path)
                self.assertEqual(source["cadcraft_version"], "0.20.1")
                self.assertTrue(source["title"])
                self.assertTrue(source["commands"])

    def test_cadcraft_release_is_exactly_pinned(self):
        self.assertEqual(self.diagrams.CADCRAFT_VERSION, "0.20.1")
        self.assertEqual(self.diagrams.CADCRAFT_ARCH, "x86_64")
        self.assertEqual(
            self.diagrams.CADCRAFT_ARCHIVE_SHA256,
            "57b6f1b41b4f3c542a82f103202ed1a779440e5ff8d25c08ef66abda1a8cb1b9",
        )
        self.assertIn(
            "/releases/download/v0.20.1/",
            self.diagrams.CADCRAFT_URL,
        )

    def test_command_arguments_preserve_source_commands_as_json(self):
        source = {
            "commands": [
                {
                    "command": "line",
                    "params": {"points": [[0, 0], [10, 10]]},
                }
            ]
        }
        self.assertEqual(
            self.diagrams.command_arguments(source),
            [
                "--cmd",
                'line {"points":[[0,0],[10,10]]}',
            ],
        )

    def test_diagram_item_is_independent_and_durable(self):
        text = CI.read_text(encoding="utf-8")
        self.assertIn("id: verification-diagrams", text)
        self.assertIn("process: true", text)
        self.assertIn("kind: verification", text)
        self.assertNotIn("needs:", text)
        self.assertIn("scripts/build_diagrams.py", text)
        self.assertIn("verification/diagrams/sources/**", text)
        self.assertIn("- diagrams", text)

    def test_renderer_does_not_execute_forge_or_solidcraft(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("cadcraft-cli", text)
        self.assertNotIn("solidcraft-cli", text)
        self.assertNotIn("scpf", text.lower())
        self.assertNotIn("FORGE_RUNTIME_IMAGE", text)
        self.assertNotIn("REFERENCE_RUNTIME_IMAGE", text)


if __name__ == "__main__":
    unittest.main()
