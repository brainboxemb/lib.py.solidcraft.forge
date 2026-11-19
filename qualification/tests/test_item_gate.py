"""Tests for assembling publication input from completed CI items."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from qualification import item_gate


def write_item(root: Path, path: str, output: str) -> None:
    item = root / path
    item.mkdir(parents=True, exist_ok=True)
    (item / "item.json").write_text(
        json.dumps({"status": "pass"}),
        encoding="utf-8",
    )
    target = item / output
    target.mkdir(parents=True, exist_ok=True)
    (target / "evidence.txt").write_text("ok\n", encoding="utf-8")


class ItemGateTests(unittest.TestCase):
    def test_model_verify_collects_cases_and_requested_evidence(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            build_root = root / "build"
            write_item(
                build_root,
                "qualification/reference_suite",
                "references",
            )
            write_item(
                build_root,
                "qualification/diagrams",
                "rendered",
            )
            with patch.object(
                item_gate,
                "selected_cases",
                return_value=("simple-box",),
            ), patch.object(
                item_gate,
                "collect_from_items",
            ) as collect, patch.object(
                item_gate,
                "assemble_build",
            ) as assemble:
                result = item_gate.execute(
                    stage="model_verify",
                    cases_value="simple-box",
                    out=root / "result",
                    build_out=root / "build-out",
                    build_root=build_root,
                    source_sha="a" * 40,
                    verify_references=True,
                    verify_diagrams=True,
                    scope="pr",
                    source_ref="feature/test",
                    pull_request=12,
                    base_commit="b" * 40,
                    workflow_run_id="42",
                )

            self.assertEqual(result, ("simple-box",))
            collect.assert_called_once_with(
                build_root=build_root,
                out=root / "result",
                cases=("simple-box",),
                source_sha="a" * 40,
            )
            self.assertEqual(
                (root / "result/references/evidence.txt").read_text(
                    encoding="utf-8"
                ),
                "ok\n",
            )
            self.assertEqual(
                (root / "result/diagrams/evidence.txt").read_text(
                    encoding="utf-8"
                ),
                "ok\n",
            )
            assemble.assert_called_once()

    def test_tool_verify_does_not_collect_model_results(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(
                item_gate,
                "selected_cases",
                return_value=("simple-box",),
            ), patch.object(
                item_gate,
                "collect_from_items",
            ) as collect, patch.object(
                item_gate,
                "assemble_build",
            ):
                item_gate.execute(
                    stage="tool_verify",
                    cases_value="simple-box",
                    out=root / "result",
                    build_out=root / "build-out",
                    build_root=root / "build",
                    source_sha="a" * 40,
                    verify_references=False,
                    verify_diagrams=False,
                    scope="pr",
                    source_ref="feature/test",
                    pull_request=12,
                    base_commit=None,
                    workflow_run_id="42",
                )

        collect.assert_not_called()

    def test_reference_verification_materializes_only_reference_item(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(
                item_gate,
                "selected_cases",
                return_value=(),
            ), patch.object(
                item_gate,
                "collect_from_items",
            ), patch.object(
                item_gate,
                "copy_completed_item_output",
            ) as copy_evidence, patch.object(
                item_gate,
                "assemble_build",
            ):
                item_gate.execute(
                    stage="none",
                    cases_value="",
                    out=root / "result",
                    build_out=root / "build-out",
                    build_root=root / "build",
                    source_sha="a" * 40,
                    verify_references=True,
                    verify_diagrams=False,
                    scope="pr",
                    source_ref="feature/test",
                    pull_request=12,
                    base_commit=None,
                    workflow_run_id="42",
                )

        copy_evidence.assert_called_once_with(
            build_root=root / "build",
            item_path=Path("qualification/reference_suite"),
            output_name="references",
            destination=root / "result/references",
        )


if __name__ == "__main__":
    unittest.main()
