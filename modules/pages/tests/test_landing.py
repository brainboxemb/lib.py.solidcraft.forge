from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from cad_library_pages.homepage import homepage_manifest
from cad_library_pages.landing import (
    landing_metadata,
    prepare_landing,
    tested_solidcraft_version,
)


class LandingTests(unittest.TestCase):
    def test_landing_metadata_is_read_statically_from_source(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "cadlib/src/scpf").mkdir(parents=True)
            (root / "cadlib/pyproject.toml").write_text(
                '[project]\nname = "scpf"\nversion = "1.2.3"\n',
                encoding="utf-8",
            )
            (root / "cadlib/src/scpf/version.py").write_text(
                'TESTED_SOLIDCRAFT_VERSION = "9.8.7"\n',
                encoding="utf-8",
            )

            self.assertEqual(tested_solidcraft_version(root), "9.8.7")
            expected = {
                "package_version": "1.2.3",
                "tested_solidcraft_version": "9.8.7",
            }
            self.assertEqual(landing_metadata(root), expected)

            site = root / "site"
            self.assertEqual(prepare_landing(root, site), expected)
            self.assertEqual(
                json.loads((site / "data/forge.json").read_text(encoding="utf-8")),
                expected,
            )

    def test_homepage_content_is_generated_not_hardcoded_in_layout(self):
        root = Path(__file__).resolve().parents[3]
        metadata = landing_metadata(root)
        manifest = homepage_manifest(root, context=metadata)
        rendered_source = json.dumps(manifest)

        for marker in (
            "Python API/compiler for SolidCraft",
            "SCPF model",
            "Forge compiler",
            "SolidCraft",
            "Start with the Guide",
            "API Reference",
            "Cheatsheet",
            "Examples",
            "Verification",
            "SolidCraft models",
            "https://brainboxemb.github.io/2026-011-02.cad.solidcraft/",
            f"SCPF {metadata['package_version']}",
            f"Tested with SolidCraft {metadata['tested_solidcraft_version']}",
        ):
            self.assertIn(marker, rendered_source)

        layout = (root / "site/layouts/home.html").read_text(encoding="utf-8")
        self.assertIn("site.Data.home", layout)
        self.assertIn("data-generated-homepage", layout)
        for product_copy in (
            "Start with the Guide",
            "API Reference",
            "SolidCraft models",
            "Python API/compiler for SolidCraft",
        ):
            self.assertNotIn(product_copy, layout)


if __name__ == "__main__":
    unittest.main()
