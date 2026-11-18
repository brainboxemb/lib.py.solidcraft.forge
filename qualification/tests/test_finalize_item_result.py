"""Tests for finalizing one self-contained example item result."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from qualification import finalize_item_result


class FinalizeItemResultTests(unittest.TestCase):
    def test_finalize_normalizes_existing_evidence_and_requires_pass(self):
        with TemporaryDirectory() as temp:
            out = Path(temp)
            target = out / "native/simple-box/qualification-result.json"
            with patch.object(
                finalize_item_result,
                "write_validation_summaries",
            ) as summaries, patch.object(
                finalize_item_result,
                "collect_results",
                return_value={
                    "cases": {"simple-box": {"status": "pass"}}
                },
            ) as collect:
                # results.collect owns this file in the real path; create it in
                # the mock so the finalizer's safety check remains exercised.
                target.parent.mkdir(parents=True)
                target.write_text("{}\n", encoding="utf-8")
                result = finalize_item_result.finalize(
                    out,
                    "simple-box",
                    "a" * 40,
                )

        summaries.assert_called_once_with(out, ("simple-box",))
        collect.assert_called_once()
        self.assertEqual(result["status"], "pass")

    def test_finalize_rejects_non_passing_result(self):
        with TemporaryDirectory() as temp:
            out = Path(temp)
            with patch.object(
                finalize_item_result,
                "write_validation_summaries",
            ), patch.object(
                finalize_item_result,
                "collect_results",
                return_value={
                    "cases": {"simple-box": {"status": "fail"}}
                },
            ):
                with self.assertRaisesRegex(RuntimeError, "not passing"):
                    finalize_item_result.finalize(
                        out,
                        "simple-box",
                        "a" * 40,
                    )


if __name__ == "__main__":
    unittest.main()
