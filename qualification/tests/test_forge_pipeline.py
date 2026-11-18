"""Focused tests for the reproducible Forge pipeline entrypoint."""

from __future__ import annotations

import argparse
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts import forge_pipeline


def args(**overrides):
    values = {
        "operation": "pr",
        "source_sha": "a" * 40,
        "base_sha": "b" * 40,
        "source_ref": "feature/test",
        "pull_request": 351,
        "gate": "affected-q1-q6",
        "cases": "simple-box",
        "required_level": "affected-q1-q6",
        "reference_smoke": True,
        "pipeline_smoke": False,
        "image_built": False,
        "contracts": False,
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
    def test_parse_bool_accepts_ci_values(self):
        for value in ("true", "1", "yes", "on"):
            with self.subTest(value=value):
                self.assertTrue(forge_pipeline.parse_bool(value))
        for value in ("false", "0", "no", "off", ""):
            with self.subTest(value=value):
                self.assertFalse(forge_pipeline.parse_bool(value))
        with self.assertRaises(argparse.ArgumentTypeError):
            forge_pipeline.parse_bool("maybe")

    def test_selected_tool_cases_follow_forge_gate_selection(self):
        self.assertEqual(
            forge_pipeline.selected_tool_cases(
                "affected-q1-q6",
                "simple-box,anchored-holes",
            ),
            ("simple-box", "anchored-holes"),
        )
        self.assertEqual(
            forge_pipeline.selected_tool_cases("preflight", ""),
            (),
        )
        self.assertEqual(
            forge_pipeline.selected_tool_cases("full-q1-q6", ""),
            forge_pipeline.supported_case_slugs(),
        )

    def test_pr_qualification_arguments_are_complete(self):
        command = forge_pipeline.qualification_args(args())
        self.assertEqual(command[0], "scripts/verification_gate.py")
        self.assertIn("affected-q1-q6", command)
        self.assertIn("simple-box", command)
        self.assertIn("--reference-smoke", command)
        self.assertIn("--base-commit", command)
        self.assertIn("--pull-request", command)
        self.assertIn("351", command)

    def test_native_gate_collects_items_instead_of_rerunning_legacy_gate(self):
        ns = args()
        command = forge_pipeline.item_gate_args(ns)
        with patch.object(
            forge_pipeline,
            "run_tool_cad_ci_case",
        ) as case_item, patch.object(
            forge_pipeline,
            "run_tool_cad_ci_evidence",
        ) as evidence_item, patch.object(
            forge_pipeline,
            "python",
        ) as item_gate:
            forge_pipeline.qualify(ns)

        case_item.assert_called_once_with("simple-box", ns.image)
        evidence_item.assert_called_once_with("reference-suite", ns.image)
        item_gate.assert_called_once_with(*command)
        self.assertEqual(command[0], "qualification/item_gate.py")
        self.assertNotIn("scripts/verification_gate.py", command)

    def test_qualify_skips_native_case_item_for_cheap_gate(self):
        ns = args(
            gate="affected-q1-q2",
            required_level="affected-q1-q2",
            image="",
            reference_smoke=False,
        )
        command = forge_pipeline.qualification_args(ns)
        with patch.object(
            forge_pipeline,
            "run_tool_cad_ci_case",
        ) as case_item, patch.object(
            forge_pipeline,
            "python",
        ) as legacy_gate:
            forge_pipeline.qualify(ns)

        case_item.assert_not_called()
        legacy_gate.assert_called_once_with(*command)

    def test_reference_item_can_run_for_cheap_gate(self):
        ns = args(
            gate="affected-q1-q2",
            required_level="affected-q1-q2",
            cases="simple-box",
            reference_smoke=True,
        )
        with patch.object(
            forge_pipeline,
            "run_tool_cad_ci_case",
        ) as case_item, patch.object(
            forge_pipeline,
            "run_tool_cad_ci_evidence",
        ) as evidence_item, patch.object(
            forge_pipeline,
            "docker_python",
        ):
            forge_pipeline.qualify(ns)

        case_item.assert_not_called()
        evidence_item.assert_called_once_with("reference-suite", ns.image)

    def test_execute_pr_runs_verification_then_generic_publication(self):
        ns = args(pipeline_smoke=True, contracts=True)
        with patch.object(
            forge_pipeline,
            "run_tool_cad_ci_layers",
        ) as tool_layers, patch.object(
            forge_pipeline,
            "preflight",
        ) as preflight, patch.object(
            forge_pipeline,
            "smoke_image",
        ) as smoke, patch.object(
            forge_pipeline,
            "verify_contracts",
        ) as contracts, patch.object(
            forge_pipeline,
            "qualify",
        ) as qualify, patch.object(
            forge_pipeline.generic_publication,
            "execute",
            return_value=None,
        ) as publish:
            result = forge_pipeline.execute(ns)

        self.assertIsNone(result)
        tool_layers.assert_called_once_with(
            ns.output_root / "tool-cad-ci-plan.json",
            ns.gate,
            ns.cases,
            ns.reference_smoke,
        )
        preflight.assert_called_once_with(
            ns.source_sha,
            ns.output_root / "preflight-site",
        )
        smoke.assert_called_once_with(ns.image, ns.smoke_out)
        contracts.assert_called_once_with(
            ns.image,
            ns.solidcraft_version,
            ns.contract_out,
        )
        qualify.assert_called_once_with(ns)
        publish.assert_called_once_with(
            source_sha=ns.source_sha,
            source_ref=ns.source_ref,
            operation=ns.operation,
            pull_request=ns.pull_request,
            gate=ns.gate,
            cases=ns.cases,
            workflow_run_id=ns.workflow_run_id,
            generated_build=ns.generated_build,
            output_root=ns.output_root,
            publish=ns.publish,
        )

    def test_new_image_is_smoke_tested_even_without_pipeline_change(self):
        ns = args(pipeline_smoke=False, image_built=True)
        with patch.object(forge_pipeline, "run_tool_cad_ci_layers"),              patch.object(forge_pipeline, "preflight"),              patch.object(forge_pipeline, "smoke_image") as smoke,              patch.object(forge_pipeline, "qualify"),              patch.object(forge_pipeline.generic_publication, "execute"):
            forge_pipeline.execute(ns)
        smoke.assert_called_once_with(ns.image, ns.smoke_out)

    def test_execute_main_returns_generic_build_commit(self):
        ns = args(operation="main", pull_request=0, source_ref="main")
        with patch.object(forge_pipeline, "run_tool_cad_ci_layers") as tool_layers,              patch.object(forge_pipeline, "preflight"),              patch.object(forge_pipeline, "qualify"),              patch.object(
                 forge_pipeline.generic_publication,
                 "execute",
                 return_value="build-commit",
             ) as publish:
            result = forge_pipeline.execute(ns)

        self.assertEqual(result, "build-commit")
        tool_layers.assert_called_once_with(
            ns.output_root / "tool-cad-ci-plan.json",
            ns.gate,
            ns.cases,
            ns.reference_smoke,
        )
        publish.assert_called_once()

    def test_cleanup_uses_generic_build_and_pages_cleanup(self):
        with patch.object(
            forge_pipeline.generic_publication,
            "cleanup",
        ) as cleanup:
            forge_pipeline.cleanup(351)

        cleanup.assert_called_once_with(351)


if __name__ == "__main__":
    unittest.main()
