from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from cad_library_pages.api_reference import prepare_api_reference


class ApiReferenceProjectionTests(unittest.TestCase):
    def _write_source(self, root: Path):
        package = root / 'cadlib/src/scpf'
        package.mkdir(parents=True)
        (package / '__init__.py').write_text(
            '__all__ = ["Shape", "Anchor", "component"]\n',
            encoding='utf-8',
        )
        (package / 'core.py').write_text(
            'class Shape:\n    def at(self):\n        pass\n\nclass Anchor:\n    pass\n',
            encoding='utf-8',
        )
        (package / 'runner.py').write_text(
            'def component():\n    pass\n',
            encoding='utf-8',
        )

    def test_projects_routes_and_static_manifest_without_importing_scpf(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_source(root)
            docs = root / 'docs'
            docs.mkdir()
            manifest = {
                'schema': 2,
                'references': [
                    {'kind': 'callable', 'name': 'Shape', 'summary': 'Shape.', 'signature': 'Shape()'},
                    {'kind': 'callable', 'name': 'Shape.at', 'summary': 'Place.', 'signature': 'Shape.at(self)'},
                    {'kind': 'enum', 'name': 'Anchor', 'summary': 'Anchor.', 'members': []},
                    {'kind': 'group', 'name': 'execution-api', 'summary': 'Execution.', 'members': [
                        {'kind': 'callable', 'name': 'component', 'summary': 'Component.', 'signature': 'component()'}
                    ]},
                ],
            }
            (docs / 'api-reference.json').write_text(json.dumps(manifest), encoding='utf-8')
            site = root / 'site'

            prepare_api_reference(root, site)

            self.assertTrue((site / 'content/reference/Shape/index.md').is_file())
            self.assertTrue((site / 'content/reference/Shape.at/index.md').is_file())
            self.assertTrue((site / 'content/reference/execution-api/index.md').is_file())
            self.assertEqual(
                json.loads((site / 'static/reference/api.json').read_text(encoding='utf-8')),
                manifest,
            )

    def test_rejects_manifest_that_loses_public_export(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_source(root)
            docs = root / 'docs'
            docs.mkdir()
            (docs / 'api-reference.json').write_text(
                json.dumps({'schema': 2, 'references': [
                    {'kind': 'callable', 'name': 'Shape', 'summary': 'Shape.'}
                ]}),
                encoding='utf-8',
            )
            with self.assertRaisesRegex(ValueError, 'misses public exports'):
                prepare_api_reference(root, root / 'site')


if __name__ == '__main__':
    unittest.main()
