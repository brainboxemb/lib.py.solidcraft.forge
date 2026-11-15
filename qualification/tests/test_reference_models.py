"""Qualification references must exist for every case and remain valid Python."""

import ast
from pathlib import Path
import unittest

from qualification.cases import (
    DEFAULT_REFERENCE_IMPLEMENTATIONS,
    QUALIFICATION_CASES,
    reference_implementations_for,
)


ROOT = Path(__file__).resolve().parents[2]


class ReferenceModelTests(unittest.TestCase):
    def test_default_reference_set_is_three_independent_libraries(self):
        self.assertEqual(
            DEFAULT_REFERENCE_IMPLEMENTATIONS,
            ("pythonscad", "pybosl2", "cadquery"),
        )

    def test_every_qualification_has_python_references(self):
        for case in QUALIFICATION_CASES:
            slug = case["slug"]
            with self.subTest(case=slug):
                for reference in reference_implementations_for(case):
                    path = (
                        ROOT / "examples" / slug / reference / "model.py"
                    )
                    self.assertTrue(path.is_file(), path)
                    source = path.read_text(encoding="utf-8")
                    compile(source, str(path), "exec")
                    self.assertTrue(source.strip(), path)
                    tree = ast.parse(source, filename=str(path))
                    self.assertTrue(ast.get_docstring(tree), path)
                    self.assertTrue(
                        any(
                            isinstance(node, ast.Assign)
                            and any(
                                isinstance(target, ast.Name)
                                and target.id == "model"
                                for target in node.targets
                            )
                            for node in ast.walk(tree)
                        ),
                        f"{path} must expose final geometry as model",
                    )

    def test_references_do_not_become_forge_api_sources(self):
        for case in QUALIFICATION_CASES:
            slug = case["slug"]
            for reference in reference_implementations_for(case):
                source = (
                    ROOT / "examples" / slug / reference / "model.py"
                ).read_text(encoding="utf-8")
                self.assertNotIn("from scpf", source, (slug, reference))


if __name__ == "__main__":
    unittest.main()
