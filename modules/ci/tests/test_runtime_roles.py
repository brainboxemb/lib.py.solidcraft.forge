from pathlib import Path
import unittest

from cad_library_ci.batch import runtime_order
from cad_library_ci.config import load_project
from cad_library_ci.items import discover_modules
from cad_library_ci.models import discover_models


class RuntimeRoleTests(unittest.TestCase):
    def test_solidcraft_precedes_reference_for_multi_engine_owner(self):
        repo = Path.cwd()
        project = load_project(repo)
        modules = discover_modules(repo, project)
        models = discover_models(repo, project, modules)
        self.assertEqual(runtime_order(models), ("solidcraft", "reference"))


if __name__ == "__main__":
    unittest.main()
