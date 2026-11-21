"""Tests for the Forge qualification-summary evidence adapter."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "qualification_summary.py"
SPEC = importlib.util.spec_from_file_location("qualification_summary", SCRIPT)
summary = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(summary)


@dataclass(frozen=True)
class FakeCheck:
    name: str
    status: str
    required: bool = True
    reason: str | None = None
    evidence: object = None


class FakeSemanticApi:
    @staticmethod
    def compose_semantic_result(checks):
        rows = tuple(checks)
        required = [row for row in rows if row.required]
        status = "pass"
        for candidate, result in (
            ("error", "error"),
            ("fail", "fail"),
            ("missing", "incomplete"),
            ("review", "review"),
            ("blocked", "blocked"),
        ):
            if any(row.status == candidate for row in required):
                status = result
                break
        return {
            "status": status,
            "checks": [
                {
                    "name": row.name,
                    "status": row.status,
                    "required": row.required,
                    "reason": row.reason,
                    "evidence": row.evidence,
                }
                for row in rows
            ],
        }

    @staticmethod
    def compose_item_results(items):
        rows = tuple(items)
        status = "pass"
        states = [result["status"] for _, result in rows]
        for candidate in ("error", "fail", "incomplete", "review", "blocked"):
            if candidate in states:
                status = candidate
                break
        return {"status": status, "items": []}

    @staticmethod
    def semantic_checks_from_report(report):
        return tuple(
            FakeCheck(
                row["id"],
                row["status"],
                reason=row.get("reason"),
                evidence={
                    "evidence": row.get("evidence"),
                    "artifacts": row.get("artifacts", []),
                    "error": row.get("error"),
                },
            )
            for row in report["checks"]
        )


def fake_api():
    return (
        FakeCheck,
        FakeSemanticApi.compose_item_results,
        FakeSemanticApi.compose_semantic_result,
        FakeSemanticApi.semantic_checks_from_report,
    )


class QualificationSummaryTests(unittest.TestCase):
    def write_json(self, root, relative, value):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def make_case(self, root, slug="simple-box", saved=True):
        case = root / "examples" / slug
        self.write_json(
            root,
            f"examples/{slug}/.cad-ci/steps/contract_test.json",
            {"status": "pass"},
        )
        self.write_json(
            root,
            f"examples/{slug}/.cad-ci/steps/model_verify.json",
            {"status": "pass"},
        )
        self.write_json(
            root,
            f"examples/{slug}/solidcraft.json",
            {"commands": [{"command": "solid.box"}]},
        )
        for name in ("model.sc", "model.step", "results.json"):
            path = case / "model_verify" / "native" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x", encoding="utf-8")

        checks = [
            {
                "id": "baseline",
                "status": "pass",
                "reason": None,
                "error": None,
                "evidence": {},
                "artifacts": [{"path": "baseline/measurements.json"}],
            }
        ]
        if saved:
            checks.append(
                {
                    "id": "saved_design_length_50",
                    "status": "pass",
                    "reason": None,
                    "error": None,
                    "evidence": {},
                    "artifacts": [
                        {"path": "saved_designs/length_50/model.sc"},
                        {"path": "saved_designs/length_50/measurements.json"},
                    ],
                }
            )
        self.write_json(
            root,
            f"examples/{slug}/model_verify/verification.json",
            {
                "schema": "cad-verification",
                "schema_version": 1,
                "status": "pass",
                "checks": checks,
            },
        )
        views = []
        for view in ("front", "right", "iso"):
            views.append(
                {
                    "view": view,
                    "status": "pass",
                    "evidence": {
                        "actual_image": f"visual/{view}/actual.png",
                        "diff_image": f"visual/{view}/diff.png",
                        "goal_image": f"visual/{view}/goal.png",
                        "overlay_image": f"visual/{view}/overlay.png",
                        "baseline_status": "pass",
                        "expected_shape_status": "pass",
                    },
                }
            )
        self.write_json(
            root,
            f"examples/{slug}/model_verify/visual.json",
            {
                "status": "pass",
                "semantic": {"status": "pass", "checks": []},
                "views": views,
            },
        )
        for implementation in summary.REFERENCE_IMPLEMENTATIONS:
            self.write_json(
                root,
                (
                    f"examples/{slug}/{implementation}/references/"
                    f"{slug}/{implementation}/verification.json"
                ),
                {"implementation": implementation, "status": "pass"},
            )
        return case

    def test_restores_existing_public_five_check_shape(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            summary, "_semantic_api", fake_api
        ):
            root = Path(tmp)
            self.make_case(root)
            result, gate = summary.compose_case(root, "simple-box")

        self.assertEqual(result["schema_version"], 5)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(
            tuple(result["checks"]),
            ("integration", "native_model", "geometry", "saved_design", "visual"),
        )
        self.assertNotIn("reference", result["checks"])
        self.assertEqual(gate["status"], "pass")

    def test_no_saved_design_is_not_required(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            summary, "_semantic_api", fake_api
        ):
            root = Path(tmp)
            self.make_case(root, saved=False)
            result, _ = summary.compose_case(root, "simple-box")
        self.assertEqual(result["checks"]["saved_design"]["status"], "not-required")
        self.assertFalse(result["checks"]["saved_design"]["required"])

    def test_reference_failure_blocks_internal_gate_not_public_shape(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            summary, "_semantic_api", fake_api
        ):
            root = Path(tmp)
            self.make_case(root)
            target = (
                root
                / "examples"
                / "simple-box"
                / "cadquery"
                / "references"
                / "simple-box"
                / "cadquery"
                / "verification.json"
            )
            target.write_text(
                json.dumps({"implementation": "cadquery", "status": "fail"}),
                encoding="utf-8",
            )
            result, gate = summary.compose_case(root, "simple-box")
        self.assertEqual(result["status"], "pass")
        self.assertNotIn("reference", result["checks"])
        self.assertEqual(gate["status"], "fail")

    def test_missing_visual_is_incomplete_and_required(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            summary, "_semantic_api", fake_api
        ):
            root = Path(tmp)
            case = self.make_case(root)
            (case / "model_verify" / "visual.json").unlink()
            result, gate = summary.compose_case(root, "simple-box")
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["checks"]["visual"]["status"], "missing")
        self.assertTrue(result["checks"]["visual"]["required"])
        self.assertEqual(gate["status"], "incomplete")

    def test_batch_reference_duplicates_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            summary, "_semantic_api", fake_api
        ):
            root = Path(tmp)
            self.make_case(root)
            for implementation in summary.REFERENCE_IMPLEMENTATIONS:
                self.write_json(
                    root,
                    (
                        "ci/reference-verification-batch/references/"
                        f"simple-box/{implementation}/verification.json"
                    ),
                    {
                        "implementation": implementation,
                        "status": "fail",
                    },
                )
            result, gate = summary.compose_case(root, "simple-box")

        self.assertEqual(result["status"], "pass")
        self.assertEqual(gate["status"], "pass")

    def test_split_visual_roles_compose_independently(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            summary, "_semantic_api", fake_api
        ):
            root = Path(tmp)
            case = self.make_case(root)
            path = case / "model_verify" / "visual.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["views"] = [
                {
                    "view": "front",
                    "status": "pass",
                    "regression_required": True,
                    "expected_shape_required": False,
                    "evidence": {
                        "actual_image": "visual/front/actual.png",
                        "diff_image": "visual/front/diff.png",
                        "goal_image": None,
                        "overlay_image": None,
                        "baseline_status": "pass",
                        "expected_shape_status": "missing",
                    },
                },
                {
                    "view": "top",
                    "status": "pass",
                    "regression_required": False,
                    "expected_shape_required": True,
                    "evidence": {
                        "actual_image": "visual/top/actual.png",
                        "diff_image": None,
                        "goal_image": "visual/top/goal.png",
                        "overlay_image": "visual/top/overlay.png",
                        "baseline_status": "missing",
                        "expected_shape_status": "pass",
                    },
                },
            ]
            path.write_text(json.dumps(report), encoding="utf-8")
            result, gate = summary.compose_case(root, "simple-box")

        visual = result["checks"]["visual"]
        self.assertEqual(visual["status"], "pass")
        self.assertEqual(visual["regression_status"], "pass")
        self.assertEqual(visual["expected_shape_status"], "pass")
        self.assertEqual(gate["status"], "pass")

    def test_inconsistent_visual_pass_becomes_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            summary, "_semantic_api", fake_api
        ):
            root = Path(tmp)
            case = self.make_case(root)
            path = case / "model_verify" / "visual.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["views"][0]["evidence"]["baseline_status"] = "missing"
            path.write_text(json.dumps(report), encoding="utf-8")
            result, gate = summary.compose_case(root, "simple-box")
        self.assertEqual(result["checks"]["visual"]["status"], "missing")
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(gate["status"], "incomplete")

    def test_native_artifacts_keep_native_separate_from_geometry_failure(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            summary, "_semantic_api", fake_api
        ):
            root = Path(tmp)
            case = self.make_case(root)
            report = json.loads(
                (case / "model_verify" / "verification.json").read_text(
                    encoding="utf-8"
                )
            )
            report["checks"][0]["status"] = "fail"
            (case / "model_verify" / "verification.json").write_text(
                json.dumps(report),
                encoding="utf-8",
            )
            result, _ = summary.compose_case(root, "simple-box")
        self.assertEqual(result["checks"]["native_model"]["status"], "pass")
        self.assertEqual(result["checks"]["geometry"]["status"], "fail")
        self.assertEqual(result["status"], "fail")

    def test_module_does_not_execute_cad_or_publish(self):
        source = SCRIPT.read_text(encoding="utf-8").lower()
        for forbidden in (
            "subprocess",
            "solidcraft-cli",
            "docker",
            "git push",
            "gh-pages",
            "run_script",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
