"""Generic image-regression adapter contracts."""

import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from cad_verification import encode_baseline
from cad_verification.adapters.image_regression import (
    run_image_regression_verification_file,
)


class ImageRegressionAdapterTests(unittest.TestCase):
    def _policy(self, root: Path, image: Image.Image) -> Path:
        baseline_dir = root / "baselines"
        baseline_dir.mkdir()
        payload = {
            "schema": 1,
            "approval": "approved",
            "source_commit": "test",
            **encode_baseline(image, encoding="png"),
        }
        (baseline_dir / "sheet.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )
        policy = root / "visual.json"
        policy.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "baseline_payload": "baselines/sheet.json",
                    "normalized_size": [32, 24],
                    "changed_pixel_threshold": 12,
                    "max_mean_difference": 1,
                    "max_changed_fraction": 0.01,
                    "baseline_provenance": {
                        "approval": "approved",
                        "source_commit": "test",
                    },
                }
            ),
            encoding="utf-8",
        )
        return policy

    def test_identical_approved_image_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = Image.new("RGB", (64, 48), "white")
            actual = root / "sheet.png"
            image.save(actual)
            policy = self._policy(root, image)

            report = run_image_regression_verification_file(
                actual,
                root / "verification",
                policy,
                verification_id="drawing-sheet",
            )

            self.assertEqual(report["status"], "pass")
            check = report["checks"][0]
            self.assertEqual(check["status"], "pass")
            self.assertTrue(check["evidence"]["regression"]["pass"])
            self.assertTrue((root / "verification" / "diff.png").is_file())

    def test_changed_image_fails_with_diff_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = Image.new("RGB", (64, 48), "white")
            actual = root / "sheet.png"
            Image.new("RGB", (64, 48), "black").save(actual)
            policy = self._policy(root, baseline)

            report = run_image_regression_verification_file(
                actual,
                root / "verification",
                policy,
                verification_id="drawing-sheet",
            )

            self.assertEqual(report["status"], "fail")
            check = report["checks"][0]
            self.assertEqual(check["status"], "fail")
            self.assertFalse(check["evidence"]["regression"]["pass"])
            self.assertTrue((root / "verification" / "diff.png").is_file())


if __name__ == "__main__":
    unittest.main()
