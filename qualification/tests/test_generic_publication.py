"""Tests for generic Forge build and Pages publication."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import call, patch

from scripts import generic_publication


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class GenericPublicationTests(unittest.TestCase):
    def test_completed_items_only_returns_final_passing_items(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_json(
                root / "examples/simple-box/item.json",
                {"status": "pass"},
            )
            plan = (
                {"id": "simple-box", "path": "examples/simple-box"},
                {"id": "anchored-holes", "path": "examples/anchored-holes"},
            )

            self.assertEqual(
                generic_publication.completed_items(plan, root),
                ("simple-box",),
            )

    def test_generic_main_available_requires_schema_one_main_manifest(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            write_json(
                root / "main/build.json",
                {"schema": 1, "scope": "main"},
            )
            self.assertTrue(generic_publication.generic_main_available(root))
            write_json(
                root / "main/build.json",
                {"schema_version": 2, "scope": "main"},
            )
            self.assertFalse(generic_publication.generic_main_available(root))

    def test_cutover_pr_defers_publication_until_generic_main_exists(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "output"
            write_json(output / "tool-cad-ci-plan.json", [])
            with patch.object(
                generic_publication,
                "run_tool",
            ) as tool:
                result = generic_publication.execute(
                    source_sha="a" * 40,
                    source_ref="feature/cutover",
                    operation="pr",
                    pull_request=12,
                    gate="preflight",
                    cases="",
                    workflow_run_id="42",
                    generated_build=root / "generated-build",
                    output_root=output,
                    publish=True,
                )

            self.assertIsNone(result)
            tool.assert_not_called()

    def test_first_generic_main_requires_full_gate(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "output"
            write_json(output / "tool-cad-ci-plan.json", [])
            with self.assertRaisesRegex(RuntimeError, "full native gate"):
                generic_publication.execute(
                    source_sha="a" * 40,
                    source_ref="main",
                    operation="main",
                    pull_request=0,
                    gate="preflight",
                    cases="",
                    workflow_run_id="42",
                    generated_build=root / "generated-build",
                    output_root=output,
                    publish=True,
                )

    def test_cleanup_uses_generic_scoped_publish_commands(self):
        with patch.object(generic_publication, "run_tool") as tool:
            generic_publication.cleanup(12)

        self.assertEqual(
            tool.call_args_list,
            [
                call(
                    "publish",
                    "build-cleanup",
                    "--repo",
                    str(generic_publication.ROOT),
                    "--pull-request",
                    "12",
                    "--message",
                    "Remove Forge build PR #12",
                ),
                call(
                    "publish",
                    "pages-cleanup",
                    "--repo",
                    str(generic_publication.ROOT),
                    "--pull-request",
                    "12",
                    "--message",
                    "Remove Forge preview PR #12",
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
