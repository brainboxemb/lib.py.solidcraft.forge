from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from cad_library_pages.landing import landing_metadata, prepare_landing


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

            self.assertEqual(
                landing_metadata(root),
                {
                    "package_version": "1.2.3",
                    "tested_solidcraft_version": "9.8.7",
                },
            )

            site = root / "site"
            prepare_landing(root, site)
            self.assertEqual(
                json.loads((site / "data/forge.json").read_text(encoding="utf-8")),
                {
                    "package_version": "1.2.3",
                    "tested_solidcraft_version": "9.8.7",
                },
            )

    def test_landing_template_explains_forge_before_site_navigation(self):
        root = Path(__file__).resolve().parents[3]
        source = (root / "site/layouts/home.html").read_text(encoding="utf-8")
        for marker in (
            "Python API/compiler for SolidCraft",
            "SCPF model",
            "Forge compiler",
            "SolidCraft commands",
            "SolidCraft remains the CAD engine",
            "Tested with SolidCraft",
            "Start with the Guide",
            "API Reference",
            "Cheatsheet",
            "Examples",
            "Verification",
        ):
            self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
