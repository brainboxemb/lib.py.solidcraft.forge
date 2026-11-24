from pathlib import Path
import unittest

class WorkflowTests(unittest.TestCase):
    def test_ci_and_pages_boundaries(self):
        ci = Path(".github/workflows/ci.yml").read_text()
        pages = Path(".github/workflows/pages.yml").read_text()
        self.assertIn("cancel-in-progress: true", ci)
        self.assertIn("gh workflow run pages.yml --ref main", ci)
        self.assertIn("branches: [dev, main]", ci)
        self.assertNotIn("actions-hugo", ci)
        self.assertIn("workflow_dispatch:", pages)
        self.assertIn("cad_library_pages.publish", pages)
        self.assertIn("source-dev", pages)
        self.assertNotIn("actions/deploy-pages", pages)
