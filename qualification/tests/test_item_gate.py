"""Tests for assembling a native Forge gate from completed example items."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import call, patch

from qualification import item_gate


class ItemGateTests(unittest.TestCase):
    def test_execute_collects_items_then_adds_reference_and_diagram_evidence(self):
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
                "run",
            ) as run, patch.object(
                item_gate,
                "assemble_build",
            ) as assemble:
                result = item_gate.execute(
                    gate="full-q1-q6",
                    cases_value="",
                    out=root / "gate",
                    build_out=root / "build-out",
                    build_root=root / "build",
                    source_sha="a" * 40,
                    reference_smoke=False,
                    scope="pr",
                    source_ref="feature/test",
                    pull_request=12,
                    base_commit="b" * 40,
                    workflow_run_id="42",
                )

        self.assertEqual(result, ("simple-box",))
        collect.assert_called_once_with(
            build_root=root / "build",
            out=root / "gate",
            cases=("simple-box",),
            source_sha="a" * 40,
        )
        self.assertEqual(
            run.call_args_list,
            [
                call(
                    [
                        item_gate.sys.executable,
                        "qualification/reference_validation.py",
                        "--cases",
                        "simple-box",
                        "--out",
                        str(root / "gate/references"),
                        "--source-sha",
                        "a" * 40,
                    ]
                ),
                call(
                    [
                        item_gate.sys.executable,
                        "qualification/render_diagrams.py",
                        "--out",
                        str(root / "gate/diagrams"),
                    ]
                ),
            ],
        )
        assemble.assert_called_once()

    def test_affected_native_gate_does_not_add_unrequested_reference_work(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(
                item_gate,
                "selected_cases",
                return_value=("simple-box",),
            ), patch.object(
                item_gate,
                "collect_from_items",
            ), patch.object(
                item_gate,
                "run",
            ) as run, patch.object(
                item_gate,
                "assemble_build",
            ):
                item_gate.execute(
                    gate="affected-q1-q6",
                    cases_value="simple-box",
                    out=root / "gate",
                    build_out=root / "build-out",
                    build_root=root / "build",
                    source_sha="a" * 40,
                    reference_smoke=False,
                    scope="pr",
                    source_ref="feature/test",
                    pull_request=12,
                    base_commit=None,
                    workflow_run_id="42",
                )

        run.assert_not_called()

    def test_non_native_gate_is_rejected(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ValueError, "does not support"):
                item_gate.execute(
                    gate="affected-q1-q2",
                    cases_value="simple-box",
                    out=root / "gate",
                    build_out=root / "build-out",
                    build_root=root / "build",
                    source_sha="a" * 40,
                    reference_smoke=False,
                    scope="pr",
                    source_ref="feature/test",
                    pull_request=12,
                    base_commit=None,
                    workflow_run_id="42",
                )


if __name__ == "__main__":
    unittest.main()
