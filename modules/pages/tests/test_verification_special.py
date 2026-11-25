from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from cad_library_pages.verification_special import prepare_verification_special


class VerificationSpecialProjectionTests(unittest.TestCase):
    def test_coverage_results_and_joint_anatomy_use_source_and_durable_evidence(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            owner = root / 'models/example'
            owner.mkdir(parents=True)
            (owner / 'model.yml').write_text(
                'purpose: verification\ntitle: Example\nsection: fundamentals\n',
                encoding='utf-8',
            )

            version = root / 'cadlib/src/scpf'
            version.mkdir(parents=True)
            (version / 'version.py').write_text(
                'TESTED_SOLIDCRAFT_VERSION = "9.8.7"\n',
                encoding='utf-8',
            )

            docs = root / 'docs/verification'
            docs.mkdir(parents=True)
            (docs / 'api-coverage.py').write_text(
                'EXPORT_COVERAGE = {"Box": ("Visual", "Visual", ["example"], "Baseline.")}\n'
                'CAPABILITY_COVERAGE = [("Primitive objects", "Box", "Visual", "Visual", ["example"], "Baseline.")]\n',
                encoding='utf-8',
            )
            joint = docs / 'joint-anatomy'
            joint.mkdir()
            (joint / 'body.html').write_text(
                '<main><section class="hero"><h1>Old title</h1></section>'
                '<section class="panel"><h2>Concept</h2><p>Body.</p>'
                '<p>Qualified with SolidCraft $solidcraft_version.</p>'
                '<div class="concept-steps">\n'
                '    <div><strong>4 brackets</strong><br>One bracket.</div>\n'
                '</div>'
                '<h3>Diagram</h3>'
                '<figure><a href="$diagram_raw_base/example.svg">'
                '<img src="$diagram_raw_base/example.svg" alt="Example diagram"></a>'
                '<figcaption>Caption. <a href="$diagram_blob_base/example.dxf">DXF</a></figcaption>'
                '</section></main>',
                encoding='utf-8',
            )
            (joint / 'example.svg').write_text('<svg/>', encoding='utf-8')
            (joint / 'example.dxf').write_text('0\nEOF\n', encoding='utf-8')

            build_scope = root / 'build/dev'
            evidence = build_scope / 'models/example'
            evidence.mkdir(parents=True)
            (evidence / 'result.json').write_text(json.dumps({
                'id': 'example',
                'status': 'pass',
                'primary': 'scpf',
                'implementations': {
                    'scpf': {
                        'verification_stages': {
                            'native': {'status': 'pass'},
                            'visual': {'status': 'pass'},
                        }
                    }
                },
            }), encoding='utf-8')
            (evidence / 'source.json').write_text(
                json.dumps({'source_sha': '1234567890abcdef'}), encoding='utf-8'
            )

            site = root / 'site'
            prepare_verification_special(root, site, build_scope)

            coverage = (site / 'content/verification/coverage/index.md').read_text(encoding='utf-8')
            self.assertIn('[`example`](../example/)', coverage)
            self.assertIn('| `Box` | Visual | Visual | pass |', coverage)

            results = (site / 'content/verification/results/index.md').read_text(encoding='utf-8')
            self.assertIn('| [`example`](../example/) | pass | `1234567890ab` | `scpf` | 1 | 2 |', results)

            anatomy = (site / 'content/verification/joint-anatomy/index.md').read_text(encoding='utf-8')
            self.assertIn('9.8.7', anatomy)
            self.assertNotIn('0.48.1', anatomy)
            self.assertIn('## Concept', anatomy)
            self.assertIn('**4 brackets**\nOne bracket.', anatomy)
            self.assertIn('### Diagram', anatomy)
            self.assertIn('[![Example diagram](example.svg)](example.svg)', anatomy)
            self.assertNotIn('    **4 brackets**', anatomy)
            self.assertNotIn('    ![Example diagram]', anatomy)
            self.assertNotIn('CadCraft', anatomy)
            self.assertNotIn('.cadcraft.json', anatomy)
            self.assertTrue((site / 'static/verification/joint-anatomy/example.svg').is_file())
            self.assertTrue((site / 'static/verification/joint-anatomy/example.dxf').is_file())
            self.assertFalse(list((site / 'static/verification/joint-anatomy').glob('*.cadcraft.json')))

    def test_repository_joint_anatomy_has_no_cadcraft_sources(self):
        root = Path(__file__).resolve().parents[3]
        joint = root / 'docs/verification/joint-anatomy'
        self.assertFalse(list(joint.glob('*.cadcraft.json')))
        body = (joint / 'body.html').read_text(encoding='utf-8')
        self.assertNotIn('CadCraft source', body)
        self.assertNotIn('.cadcraft.json', body)

    def test_coverage_rejects_unknown_owner(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / 'docs/verification'
            docs.mkdir(parents=True)
            (docs / 'api-coverage.py').write_text(
                'EXPORT_COVERAGE = {"Box": ("Visual", "Visual", ["missing"], "Baseline.")}\n'
                'CAPABILITY_COVERAGE = []\n',
                encoding='utf-8',
            )
            with self.assertRaisesRegex(ValueError, 'unknown owners'):
                prepare_verification_special(root, root / 'site', None)


if __name__ == '__main__':
    unittest.main()
