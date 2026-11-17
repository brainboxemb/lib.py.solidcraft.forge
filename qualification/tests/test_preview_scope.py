"""PR preview reference smoke runs only when its layer is affected."""

import unittest

from qualification.cases import DEFAULT_REFERENCE_IMPLEMENTATIONS
from qualification.preview_scope import (
    reference_smoke_reasons,
    reference_smoke_required,
)


class PreviewScopeTests(unittest.TestCase):
    def test_ordinary_forge_api_change_skips_reference_smoke(self):
        self.assertFalse(reference_smoke_required([
            "scpf/scpf/explicit_sketch.py",
            "scpf/tests/test_explicit_sketch_primitives.py",
        ]))

    def test_site_and_normal_docs_changes_skip_reference_smoke(self):
        self.assertFalse(reference_smoke_required([
            "site/build.py",
            "site/style.css",
            "docs/05-cad-api-design.md",
            "CHANGELOG.md",
        ]))

    def test_scpf_fixture_change_alone_skips_reference_smoke(self):
        self.assertFalse(reference_smoke_required([
            "examples/slot-family/scpf/model.py",
        ]))

    def test_qualification_python_requires_reference_smoke(self):
        paths = [
            "qualification/geometry_contracts.py",
            "qualification/tests/test_geometry_contracts.py",
        ]
        self.assertTrue(reference_smoke_required(paths))
        self.assertEqual(reference_smoke_reasons(paths), tuple(paths))

    def test_non_python_qualification_assets_do_not_require_reference_smoke(self):
        self.assertFalse(reference_smoke_required([
            "qualification/diagrams/example.cadcraft.json",
            "qualification/templates/case.html",
            "qualification/commands/example/change.json",
        ]))

    def test_each_registered_reference_directory_requires_smoke(self):
        for implementation in DEFAULT_REFERENCE_IMPLEMENTATIONS:
            with self.subTest(implementation=implementation):
                self.assertTrue(reference_smoke_required([
                    f"examples/simple-box/{implementation}/model.py",
                ]))

    def test_reference_library_cache_requires_smoke(self):
        self.assertTrue(reference_smoke_required([
            "docs/agent/reference-libraries.md",
        ]))

    def test_preview_workflow_exercises_its_own_reference_path(self):
        self.assertTrue(reference_smoke_required([
            ".github/workflows/preview.yml",
        ]))
        self.assertTrue(reference_smoke_required([
            "./.github/workflows/preview.yml",
        ]))


if __name__ == "__main__":
    unittest.main()
