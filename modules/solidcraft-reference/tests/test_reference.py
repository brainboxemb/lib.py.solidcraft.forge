from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from cad_library_solidcraft_reference import (
    MIN_COMMAND_COUNT,
    normalized_registry,
    render_commands,
    root_runtime_pin,
    validate_registry,
    verify_describe_snapshot,
    verify_pinned_describe,
    verify_pinned_reference,
    verify_snapshot,
    write_describe_snapshot,
    write_snapshot,
)


ROOT = Path(__file__).resolve().parents[3]


def registry():
    required = [
        "engine.commands",
        "solid.box",
        "solid.extrude",
        "sketch.create",
        "sketch.draw.dimensioned",
        "sketch.slot.center_to_center",
    ]
    rows = [{"id": command_id, "label": command_id} for command_id in required]
    for index in range(MIN_COMMAND_COUNT - len(rows)):
        rows.append(
            {
                "id": f"test.command_{index:03d}",
                "label": f"Test command {index:03d}",
                "tab": "TEST",
                "panel": "COMMANDS",
            }
        )
    return rows


class SolidCraftReferenceTests(unittest.TestCase):
    def test_rejects_small_hand_curated_registry(self):
        with self.assertRaisesRegex(ValueError, "implausibly small"):
            validate_registry(
                [
                    {"id": "solid.box", "label": "Box"},
                    {"id": "sketch.slot.center_to_center", "label": "Slot"},
                ]
            )

    def test_rejects_missing_required_command(self):
        rows = registry()
        rows = [row for row in rows if row["id"] != "engine.commands"]
        rows.append({"id": "test.replacement", "label": "Replacement"})
        with self.assertRaisesRegex(ValueError, "required SolidCraft commands"):
            validate_registry(rows)

    def test_rejects_duplicate_command_id(self):
        rows = registry()
        rows[-1] = dict(rows[0])
        with self.assertRaisesRegex(ValueError, "duplicate SolidCraft command ids"):
            validate_registry(rows)

    def test_snapshot_keeps_raw_registry_and_catalog_in_lockstep(self):
        rows = normalized_registry(registry())
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "0.49.0"
            write_snapshot(
                out=out,
                version="0.49.0",
                cli_version="solidcraft-cli 0.49.0",
                upstream_commit="10e6242c3a94e942c8fc11e78965ef1cd21e4856",
                runtime_release="v0.3.6",
                runtime_image="ghcr.io/brainboxemb/cad-solidcraft:v0.3.6",
                commands=rows,
            )
            raw = json.loads(
                (out / "commands.json").read_text(encoding="utf-8")
            )
            markdown = (out / "commands.md").read_text(encoding="utf-8")
            source = (out / "SOURCE.md").read_text(encoding="utf-8")
            self.assertEqual(len(raw), MIN_COMMAND_COUNT)
            self.assertIn(
                f"Total registered commands: **{MIN_COMMAND_COUNT}**.",
                markdown,
            )
            for row in raw:
                self.assertIn(f"`{row['id']}`", markdown)
            self.assertIn("v0.3.6", source)
            self.assertIn("solidcraft-cli 0.49.0", source)

    def test_checked_048_catalog_covers_canonical_registry(self):
        reference = ROOT / "docs" / "reference" / "solidcraft" / "0.48.1"
        raw = json.loads(
            (reference / "commands.json").read_text(encoding="utf-8")
        )
        commands = validate_registry(raw)
        markdown = (reference / "commands.md").read_text(encoding="utf-8")
        self.assertIn(
            f"Total registered commands: **{len(commands)}**.",
            markdown,
        )
        for row in commands:
            self.assertIn(f"`{row['id']}`", markdown)
        source = (reference / "SOURCE.md").read_text(encoding="utf-8")
        self.assertIn(f"Registered commands: `{len(commands)}`", source)
        self.assertIn("cad-solidcraft:v0.3.5", source)
        self.assertIn("0.48.1", source)

    def test_root_pin_selects_checked_reference(self):
        image, version = root_runtime_pin(ROOT)
        self.assertEqual(
            image,
            "ghcr.io/brainboxemb/cad-solidcraft:v0.3.6",
        )
        self.assertEqual(version, "0.49.0")
        self.assertTrue(
            (
                ROOT
                / "docs"
                / "reference"
                / "solidcraft"
                / version
                / "commands.json"
            ).is_file()
        )

    def test_verify_snapshot_requires_exact_registry(self):
        rows = normalized_registry(registry())
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "commands.json"
            snapshot.write_text(
                json.dumps(rows, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with patch(
                "cad_library_solidcraft_reference.capture_runtime",
                return_value=("solidcraft-cli 0.49.0", rows),
            ):
                self.assertEqual(
                    verify_snapshot(
                        image="example/runtime:v1",
                        version="0.49.0",
                        snapshot=snapshot,
                    ),
                    len(rows),
                )

            changed = [dict(row) for row in rows]
            changed[-1]["label"] = "Changed"
            with patch(
                "cad_library_solidcraft_reference.capture_runtime",
                return_value=("solidcraft-cli 0.49.0", changed),
            ):
                with self.assertRaisesRegex(
                    RuntimeError, "canonical snapshot differs"
                ):
                    verify_snapshot(
                        image="example/runtime:v1",
                        version="0.49.0",
                        snapshot=snapshot,
                    )

    def test_describe_snapshot_requires_exact_runtime_result(self):
        expected = {
            "result": {
                "id": "config.rule",
                "input": {"type": "object"},
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "config.rule.json"
            write_describe_snapshot(snapshot, expected)
            with patch(
                "cad_library_solidcraft_reference.capture_describe_runtime",
                return_value=("solidcraft-cli 0.49.0", expected),
            ):
                self.assertEqual(
                    verify_describe_snapshot(
                        image="example/runtime:v1",
                        version="0.49.0",
                        command="config.rule",
                        snapshot=snapshot,
                    ),
                    expected,
                )

            changed = {"result": {"id": "config.rule", "input": None}}
            with patch(
                "cad_library_solidcraft_reference.capture_describe_runtime",
                return_value=("solidcraft-cli 0.49.0", changed),
            ):
                with self.assertRaisesRegex(
                    RuntimeError, "describe snapshot differs"
                ):
                    verify_describe_snapshot(
                        image="example/runtime:v1",
                        version="0.49.0",
                        command="config.rule",
                        snapshot=snapshot,
                    )

    def test_missing_describe_snapshot_reports_runtime_result(self):
        actual = {
            "result": {
                "id": "config.rule",
                "input": {"title": "Configuration Rule"},
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "missing.json"
            with patch(
                "cad_library_solidcraft_reference.capture_describe_runtime",
                return_value=("solidcraft-cli 0.49.0", actual),
            ):
                with self.assertRaises(FileNotFoundError) as caught:
                    verify_describe_snapshot(
                        image="example/runtime:v1",
                        version="0.49.0",
                        command="config.rule",
                        snapshot=snapshot,
                    )
            self.assertIn("Captured runtime result", str(caught.exception))
            self.assertIn("Configuration Rule", str(caught.exception))

    @unittest.skipUnless(
        shutil.which("docker"),
        "Docker is required for immutable runtime reference verification",
    )
    def test_checked_config_rule_describe_matches_root_immutable_runtime(self):
        result = verify_pinned_describe(ROOT, "config.rule")
        self.assertIsNotNone(result)

    @unittest.skipUnless(
        shutil.which("docker"),
        "Docker is required for immutable runtime reference verification",
    )
    def test_checked_reference_matches_root_immutable_runtime(self):
        count = verify_pinned_reference(ROOT)
        raw = json.loads(
            (
                ROOT
                / "docs"
                / "reference"
                / "solidcraft"
                / root_runtime_pin(ROOT)[1]
                / "commands.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(count, len(raw))

    def test_discarded_043_reference_tree_is_absent(self):
        self.assertFalse(
            (ROOT / "docs" / "reference" / "solidcraft" / "0.43.0").exists()
        )


if __name__ == "__main__":
    unittest.main()
