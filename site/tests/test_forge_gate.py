"""Tests for the unified Forge gate command."""

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
CI = ROOT / "scripts" / "ci"
sys.path.insert(0, str(CI))

from forge_gate import command_for  # noqa: E402


class ForgeGateTests(unittest.TestCase):
    def test_preflight_plan_has_no_gate_command(self):
        self.assertIsNone(
            command_for(
                {"has_build": False},
                source_sha="a",
                source_ref="feature",
                workflow_run_id="1",
                out=Path("out"),
                build_out=Path("build"),
            )
        )

    def test_pr_gate_owns_scope_cases_and_base_commit(self):
        command = command_for(
            {
                "has_build": True,
                "gate": "affected-q1-q6",
                "cases": ["simple-box"],
                "reference_smoke": False,
                "publication": "preview",
                "pull_request": 12,
            },
            source_sha="head",
            source_ref="feature/test",
            workflow_run_id="77",
            base_commit="base",
            out=Path("out/gate"),
            build_out=Path("out/build"),
        )
        self.assertIn("affected-q1-q6", command)
        self.assertIn("simple-box", command)
        self.assertIn("pr", command)
        self.assertIn("12", command)
        self.assertIn("base", command)

    def test_main_full_gate_is_main_scope_without_pr_metadata(self):
        command = command_for(
            {
                "has_build": True,
                "gate": "full-q1-q6",
                "cases": [],
                "reference_smoke": False,
                "publication": "stable",
                "pull_request": None,
            },
            source_sha="head",
            source_ref="main",
            workflow_run_id="78",
            out=Path("out/gate"),
            build_out=Path("out/build"),
        )
        self.assertIn("full-q1-q6", command)
        self.assertIn("main", command)
        self.assertNotIn("--pull-request", command)
        self.assertNotIn("--base-commit", command)


if __name__ == "__main__":
    unittest.main()
