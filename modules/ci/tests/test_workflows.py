from pathlib import Path
import unittest

class WorkflowTests(unittest.TestCase):
    def test_ci_and_pages_boundaries(self):
        ci = Path(".github/workflows/ci.yml").read_text()
        pages = Path(".github/workflows/pages.yml").read_text()
        release = Path(".github/workflows/release.yml").read_text()
        self.assertIn("cancel-in-progress: true", ci)
        self.assertIn("Validate release metadata delta", ci)
        self.assertIn("cad_library_release.delta", ci)
        self.assertIn("--base-ref origin/main", ci)
        self.assertIn("gh workflow run pages.yml --ref main", ci)
        self.assertIn("branches: [dev, main, exp]", ci)
        self.assertIn("github.ref_name == 'exp'", ci)
        self.assertIn("branches: [dev, main, exp]", pages)
        self.assertIn("prepared-build/exp", pages)
        self.assertIn("generated-site/exp", pages)
        self.assertIn("steps.exp.outputs.exists", pages)
        self.assertNotIn("actions-hugo", ci)
        self.assertIn("workflow_dispatch:", pages)
        self.assertIn("cad_library_pages.publish", pages)
        self.assertIn("source-dev", pages)
        self.assertNotIn("actions/deploy-pages", pages)
        self.assertIn("issue_comment:", release)
        self.assertIn("python -m cad_library_release", release)
        self.assertIn(
            "tool.py.lib.ci/.github/workflows/reusable-release.yml@58ead6897a4ac8cafef22a3c1f834491bf61568d",
            release,
        )
        self.assertIn("validator_path: cadlib/release.py", release)
        self.assertIn("--source-root", release)
        self.assertIn("path: source", release)
        self.assertIn("fetch-depth: 0", release)
        self.assertNotIn("tool.cad.ci", release)
