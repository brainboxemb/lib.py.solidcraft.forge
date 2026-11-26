from pathlib import Path
import unittest

from cad_library_ci.batch import runtime_order
from cad_library_ci.config import load_project
from cad_library_ci.items import discover_modules
from cad_library_ci.models import discover_models


class RuntimeRoleTests(unittest.TestCase):
    def test_scpf_solidcraft_precedes_reference_verification(self):
        repo = Path.cwd()
        project = load_project(repo)
        modules = discover_modules(repo, project)
        models = discover_models(repo, project, modules)
        self.assertEqual(
            runtime_order(models),
            ("mitcad", "solidcraft", "reference"),
        )


if __name__ == "__main__":
    unittest.main()
