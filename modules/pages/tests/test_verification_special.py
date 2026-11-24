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
                '<img src="$diagram_raw_base/example.svg" alt="Example diagram">'
                '<p><a href="example.cadcraft.json">CadCraft source</a></p></section></main>',
                encoding='utf-8',
            )
            (joint / 'example.svg').write_text('<svg/>', encoding='utf-8')
            (joint / 'example.cadcraft.json').write_text('{}', encoding='utf-8')

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
            self.assertIn('## Concept', anatomy)
            self.assertIn('![Example diagram](example.svg)', anatomy)
            self.assertTrue((site / 'static/verification/joint-anatomy/example.svg').is_file())
            self.assertTrue((site / 'static/verification/joint-anatomy/example.cadcraft.json').is_file())

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
