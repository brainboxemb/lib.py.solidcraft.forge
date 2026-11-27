from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"


class ReleaseWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_release_workflow_has_no_external_brainbox_dependency(self):
        self.assertNotIn("brainboxemb/tool.py.lib.ci", self.workflow)
        self.assertNotIn("uses: brainboxemb/", self.workflow)
        self.assertNotIn("reusable-release.yml", self.workflow)

    def test_release_workflow_uses_repository_local_release_module(self):
        for value in (
            "Validate release actor",
            "Check out repository-local release implementation",
            "Parse exact release request",
            "Check exact stable build evidence",
            "Run repository release validator",
            "Publish or verify exact GitHub release",
            "Record release on triggering issue",
            "modules/release/src",
            "cad_library_release.command parse",
            "cad_library_release.command publish",
            "cadlib/release.py",
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.workflow)

    def test_release_workflow_preserves_safety_boundary(self):
        for value in (
            "only the repository owner may publish a release",
            "timeout-minutes: 10",
            "cancel-in-progress: false",
            "contents: write",
            "issues: write",
            "ref: main",
            "fetch-depth: 0",
            "fetch-tags: true",
            "persist-credentials: false",
            "--stable-ref main",
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.workflow)


if __name__ == "__main__":
    unittest.main()
