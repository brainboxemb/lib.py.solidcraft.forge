"""Contract tests for independently rerunnable qualification stages."""

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from unittest.mock import patch

from qualification.case_runner import (
    CaseContext,
    MissingStageInput,
    STAGES,
    plan_stages,
    run_case,
)


class CaseRunnerTests(unittest.TestCase):
    def test_stage_order_is_explicit(self):
        self.assertEqual(
            STAGES,
            (
                "q1",
                "q2",
                "compile",
                "replay",
                "evaluate",
                "inspect",
                "render",
                "mutate",
                "evaluate-mutated",
                "post-build",
                "validate-native",
                "validate-visual",
                "gate",
            ),
        )

    def test_exact_stage_does_not_expand_prerequisites(self):
        self.assertEqual(
            plan_stages(stage="mutate"),
            ("mutate",),
        )

    def test_from_runs_only_tail(self):
        self.assertEqual(
            plan_stages(start="mutate"),
            STAGES[STAGES.index("mutate"):],
        )

    def test_until_runs_only_prefix(self):
        self.assertEqual(
            plan_stages(until="replay"),
            STAGES[: STAGES.index("replay") + 1],
        )

    def test_range_is_supported(self):
        self.assertEqual(
            plan_stages(start="replay", until="inspect"),
            ("replay", "evaluate", "inspect"),
        )

    def test_invalid_reverse_range_is_rejected(self):
        with self.assertRaises(ValueError):
            plan_stages(start="gate", until="compile")

    def test_missing_input_fails_without_running_previous_stage(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp)
            with self.assertRaises(MissingStageInput):
                run_case(
                    "simple-box",
                    out,
                    stages=("evaluate",),
                )
            state = json.loads(
                (
                    out
                    / "stages"
                    / "simple-box"
                    / "05-evaluate.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(state["status"], "fail")
            self.assertIn("model.sc", state["error"])

    def test_skipped_optional_stage_is_recorded(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp)
            with patch(
                "qualification.case_runner.mutation_spec",
                return_value=None,
            ):
                result = run_case(
                    "simple-box",
                    out,
                    stages=("mutate",),
                )
            self.assertEqual(result["mutate"]["status"], "skipped")


if __name__ == "__main__":
    unittest.main()
