"""Focused tests for the Forge pipeline with explicit verification stages."""

from __future__ import annotations

import argparse
from pathlib import Path
import unittest
from unittest.mock import call, patch

from scripts import forge_pipeline


def args(**overrides):
    values = {
        "operation": "pr",
        "source_sha": "a" * 40,
        "base_sha": "b" * 40,
        "source_ref": "feature/test",
        "pull_request": 351,
        "stage": "model_verify",
        "cases": "simple-box",
        "verify_references": True,
        "verify_diagrams": False,
        "verify_pipeline": False,
        "image_built": False,
        "verify_contracts": False,
        "image": "qualification:test",
        "solidcraft_version": "0.42.0",
        "repository": "BrainboxEmb/lib.py.solidcraft.forge",
        "workflow_run_id": "42",
        "generated_build": Path("generated-build"),
        "output_root": Path("output"),
        "smoke_out": Path("smoke"),
        "contract_out": Path("contracts"),
        "publish": True,
        "github_output": None,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class ForgePipelineTests(unittest.TestCase):
    def test_selected_cases_are_explicit_or_complete_for_qualification(self):
        self.assertEqual(
            forge_pipeline.selected_tool_cases(
                "model_verify",
                "simple-box,anchored-holes",
            ),
            ("simple-box", "anchored-holes"),
        )
        self.assertEqual(
            forge_pipeline.selected_tool_cases("none", ""),
            (),
        )
        self.assertEqual(
            forge_pipeline.selected_tool_cases("tool_qualification", ""),
            forge_pipeline.supported_case_slugs(),
        )

    def test_evidence_items_follow_explicit_booleans(self):
        self.assertEqual(
            forge_pipeline.evidence_items(True, True),
            ("reference-suite", "qualification-diagrams"),
        )
        self.assertEqual(forge_pipeline.evidence_items(False, False), ())

    def test_model_verify_runs_selected_models_then_publication_adapter(self):
        ns = args()
        command = forge_pipeline.item_gate_args(ns)
        with patch.object(
            forge_pipeline, "run_model_verify"
        ) as model_verify, patch.object(
            forge_pipeline, "run_tool_qualification"
        ) as tool_qualification, patch.object(
            forge_pipeline, "run_tool_cad_ci_evidence"
        ) as evidence, patch.object(
            forge_pipeline, "python"
        ) as adapter:
            forge_pipeline.qualify(ns)

        model_verify.assert_called_once_with("simple-box", ns.image)
        tool_qualification.assert_not_called()
        evidence.assert_called_once_with("reference-suite", ns.image)
        adapter.assert_called_once_with(*command)
        self.assertIn("--stage", command)
        self.assertIn("model_verify", command)

    def test_tool_qualification_runs_aggregate_item_once(self):
        ns = args(
            stage="tool_qualification",
            cases="",
            verify_references=True,
            verify_diagrams=True,
        )
        with patch.object(
            forge_pipeline, "run_model_verify"
        ) as model_verify, patch.object(
            forge_pipeline, "run_tool_qualification"
        ) as tool_qualification, patch.object(
            forge_pipeline, "run_tool_cad_ci_evidence"
        ) as evidence, patch.object(
            forge_pipeline, "python"
        ) as adapter:
            forge_pipeline.qualify(ns)

        model_verify.assert_not_called()
        tool_qualification.assert_called_once_with(ns.image)
        self.assertEqual(
            evidence.call_args_list,
            [
                call("reference-suite", ns.image),
                call("qualification-diagrams", ns.image),
            ],
        )
        adapter.assert_called_once()

    def test_tool_verify_does_not_run_solidcraft_model(self):
        ns = args(
            stage="tool_verify",
            verify_references=False,
            image="",
        )
        with patch.object(
            forge_pipeline, "run_model_verify"
        ) as model_verify, patch.object(
            forge_pipeline, "run_tool_qualification"
        ) as tool_qualification, patch.object(
            forge_pipeline, "python"
        ) as adapter:
            forge_pipeline.qualify(ns)

        model_verify.assert_not_called()
        tool_qualification.assert_not_called()
        adapter.assert_not_called()
        self.assertFalse(forge_pipeline.has_build_output(ns))

    def test_execute_passes_concrete_stage_selection_to_item_runner(self):
        ns = args(verify_pipeline=True, verify_contracts=True)
        with patch.object(
            forge_pipeline, "run_tool_cad_ci_layers"
        ) as layers, patch.object(
            forge_pipeline, "preflight"
        ), patch.object(
            forge_pipeline, "smoke_image"
        ), patch.object(
            forge_pipeline, "verify_contracts"
        ), patch.object(
            forge_pipeline, "qualify"
        ), patch.object(
            forge_pipeline, "publish_pr_candidate", return_value="build"
        ), patch.object(
            forge_pipeline, "resolve_preview"
        ):
            forge_pipeline.execute(ns)

        layers.assert_called_once_with(
            ns.output_root / "tool-cad-ci-plan.json",
            ns.stage,
            ns.cases,
            ns.verify_references,
            ns.verify_diagrams,
        )

    def test_cleanup_removes_build_and_pages_preview(self):
        with patch.object(
            forge_pipeline.publish_generated, "publish"
        ) as publish:
            forge_pipeline.cleanup(351)

        self.assertEqual(
            publish.call_args_list,
            [
                call(
                    branch="build",
                    operation="remove-dir",
                    destination="pr/351",
                    message="Remove build PR #351",
                ),
                call(
                    branch="gh-pages",
                    operation="remove-dir",
                    destination="previews/pr-351",
                    message="Remove preview PR #351",
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
