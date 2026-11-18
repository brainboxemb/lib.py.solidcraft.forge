"""Tests for collecting qualification results from generic example items."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from qualification import collect_item_results


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class CollectItemResultsTests(unittest.TestCase):
    def test_materialize_requires_complete_item_and_copies_owned_evidence(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            build = root / "build"
            item = build / "examples" / "simple-box"
            case = item / "case"
            write_json(item / "item.json", {"item": "simple-box", "status": "pass"})
            write_json(case / "simple-box.json", {"commands": []})
            write_json(case / "stages/simple-box/01-q1.json", {"status": "pass"})
            (case / "native/simple-box").mkdir(parents=True)
            write_json(case / "native/simple-box/validation.json", {"q4": "pass"})
            for level in ("q1", "q2"):
                evidence = (
                    case
                    / "qualification"
                    / "case-evidence"
                    / level
                    / "simple-box.txt"
                )
                evidence.parent.mkdir(parents=True, exist_ok=True)
                evidence.write_text("PASS\n", encoding="utf-8")

            out = root / "aggregate"
            collect_item_results.materialize_case(build, out, "simple-box")

            self.assertTrue((out / "simple-box.json").is_file())
            self.assertTrue(
                (out / "stages/simple-box/01-q1.json").is_file()
            )
            self.assertTrue(
                (out / "native/simple-box/validation.json").is_file()
            )
            self.assertTrue(
                (
                    out
                    / "qualification/case-evidence/q2/simple-box.txt"
                ).is_file()
            )

    def test_materialize_rejects_integration_only_item(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            item = root / "build/examples/simple-box"
            write_json(
                item / "item.json",
                {"item": "simple-box", "status": "running"},
            )
            with self.assertRaisesRegex(RuntimeError, "not complete"):
                collect_item_results.materialize_case(
                    root / "build",
                    root / "out",
                    "simple-box",
                )

    def test_validation_summaries_are_derived_from_native_json(self):
        with TemporaryDirectory() as temp:
            out = Path(temp)
            native = out / "native/simple-box"
            write_json(
                native / "validation.json",
                {"q4": "pass", "q5": "not-required"},
            )
            write_json(
                native / "visual-validation.json",
                {"status": "pass"},
            )

            collect_item_results.write_validation_summaries(
                out,
                ("simple-box",),
            )

            self.assertEqual(
                (out / "qualification/native-validation.tsv").read_text(
                    encoding="utf-8"
                ),
                "case\tq4\tq5\nsimple-box\tPASS\tNOT-REQUIRED\n",
            )
            self.assertEqual(
                (out / "qualification/visual-validation.tsv").read_text(
                    encoding="utf-8"
                ),
                "case\tstatus\nsimple-box\tPASS\n",
            )
            self.assertEqual(
                json.loads(
                    (out / "qualification/native-validation.json").read_text(
                        encoding="utf-8"
                    )
                )["simple-box"]["q4"],
                "pass",
            )
            self.assertEqual(
                json.loads(
                    (out / "qualification/visual-validation.json").read_text(
                        encoding="utf-8"
                    )
                )["simple-box"]["status"],
                "pass",
            )

    def test_collect_uses_existing_item_output_without_running_cad(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(
                collect_item_results,
                "materialize_case",
            ) as materialize, patch.object(
                collect_item_results,
                "write_validation_summaries",
            ) as summaries, patch.object(
                collect_item_results,
                "collect_results",
                return_value={
                    "cases": {"simple-box": {"status": "pass"}}
                },
            ) as collector:
                result = collect_item_results.collect_from_items(
                    build_root=root / "build",
                    out=root / "aggregate",
                    cases=("simple-box",),
                    source_sha="a" * 40,
                )

            materialize.assert_called_once_with(
                root / "build",
                root / "aggregate",
                "simple-box",
            )
            summaries.assert_called_once_with(
                root / "aggregate",
                ("simple-box",),
            )
            collector.assert_called_once()
            self.assertEqual(result["cases"]["simple-box"]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
