"""Qualification contract for the public @assembly decorator."""

from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]


class AssemblyDecoratorCommandTests(unittest.TestCase):
    def test_imported_assembly_lowers_to_reusable_native_occurrences(self):
        commands = run_script(
            ROOT / "examples/assembly-decorator/scpf/model.py"
        )["commands"]

        created = [
            row["params"]["name"]
            for row in commands
            if row["command"] == "component.create"
        ]
        self.assertEqual(created, ["Post"])

        copies = [
            row["params"]
            for row in commands
            if row["command"] == "occurrence.copy"
        ]
        self.assertEqual(
            copies,
            [{"component": "Post", "translate": [30.0, 0.0, 0.0]}],
        )

        self.assertFalse(any(
            row["command"] == "occurrence.move"
            for row in commands
        ))


if __name__ == "__main__":
    unittest.main()
