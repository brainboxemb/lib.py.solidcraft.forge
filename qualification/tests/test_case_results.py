"""Tests for semantic per-example qualification results."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from qualification import results


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def passing_case(root: Path, slug: str = "simple-box") -> None:
    """Write the smallest complete staged model-verification evidence set for one case."""

    write_json(
        root / f"{slug}.json",
        {"commands": [{"command": "solid.box"}]},
    )
    for number, stage in (
        (1, "compile"),
        (2, "replay"),
        (3, "evaluate"),
        (11, "result"),
    ):
        write_json(
            root / "stages" / slug / f"{number:02d}-{stage}.json",
            {"status": "pass"},
        )

    model = root / "model_verify" / slug
    write_json(
        model / "validation.json",
        {"geometry": "pass", "saved_design": "pass"},
    )
    write_json(
        model / "visual-validation.json",
        {
            "status": "pass",
            "regression": {"status": "pass"},
            "expected_shape": {
                "status": "pass",
                "required_views": ["front", "right", "iso"],
            },
        },
    )
    for name in (
        "results.json",
        "measurements.json",
        "model.sc",
        "model.step",
    ):
        (model / name).parent.mkdir(parents=True, exist_ok=True)
        (model / name).write_text("{}\n", encoding="utf-8")
    (model / "model.png").write_bytes(b"png")


class SemanticResultTests(unittest.TestCase):
    def test_complete_item_writes_schema_v5_without_numbered_levels(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            passing_case(root)

            aggregate = results.collect(
                root,
                "abc123",
                "0.test",
                "0.42.0",
                "2026-11-19T00:00:00Z",
                cases=("simple-box",),
            )

            case = aggregate["cases"]["simple-box"]
            self.assertEqual(case["schema_version"], 5)
            self.assertEqual(case["status"], "pass")
            self.assertNotIn("levels", case)
            self.assertEqual(
                tuple(case["checks"]),
                (
                    "tool_verify",
                    "model_verify",
                    "geometry",
                    "saved_design",
                    "visual",
                ),
            )
            self.assertEqual(case["checks"]["tool_verify"]["status"], "pass")
            self.assertEqual(case["checks"]["model_verify"]["status"], "pass")
            self.assertEqual(case["checks"]["geometry"]["status"], "pass")
            self.assertEqual(case["checks"]["saved_design"]["status"], "pass")
            self.assertEqual(case["checks"]["visual"]["status"], "pass")

            persisted = json.loads(
                (
                    root
                    / "model_verify/simple-box/qualification-result.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(persisted["checks"], case["checks"])
            encoded = json.dumps(persisted).lower()
            for legacy in ("q1", "q2", "q3", "q4", "q5", "q6"):
                self.assertNotIn(legacy, encoded)

    def test_missing_compile_result_is_incomplete(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            passing_case(root)
            (root / "stages/simple-box/01-compile.json").unlink()

            case = results.collect(
                root,
                "abc123",
                "0.test",
                "0.42.0",
                "2026-11-19T00:00:00Z",
                cases=("simple-box",),
            )["cases"]["simple-box"]

            self.assertEqual(case["checks"]["tool_verify"]["status"], "missing")
            self.assertEqual(case["status"], "incomplete")

    def test_failed_geometry_check_fails_case(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            passing_case(root)
            write_json(
                root / "model_verify/simple-box/validation.json",
                {"geometry": "fail", "saved_design": "pass"},
            )

            case = results.collect(
                root,
                "abc123",
                "0.test",
                "0.42.0",
                "2026-11-19T00:00:00Z",
                cases=("simple-box",),
            )["cases"]["simple-box"]

            self.assertEqual(case["checks"]["geometry"]["status"], "fail")
            self.assertEqual(case["status"], "fail")


if __name__ == "__main__":
    unittest.main()
