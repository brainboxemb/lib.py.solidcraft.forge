from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cad_library_pages.documentation import prepare_documentation


class DocumentationProjectionTests(unittest.TestCase):
    def test_reference_markdown_and_json_are_projected(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            reference = root / "docs/reference/solidcraft/0.48.1"
            reference.mkdir(parents=True)
            (root / "docs/reference/README.md").write_text(
                "# Forge external references\n\n[SolidCraft](solidcraft/README.md)\n",
                encoding="utf-8",
            )
            (root / "docs/reference/solidcraft/README.md").write_text(
                "# SolidCraft version references\n\n[0.48.1](0.48.1/SOURCE.md)\n",
                encoding="utf-8",
            )
            (reference / "SOURCE.md").write_text(
                "# SolidCraft 0.48.1 canonical reference snapshot\n\n"
                "[commands](commands.md)\n",
                encoding="utf-8",
            )
            (reference / "commands.md").write_text(
                "# Commands\n\nCatalog.\n",
                encoding="utf-8",
            )
            (reference / "commands.json").write_text(
                '{"schema": 1}\n',
                encoding="utf-8",
            )

            site = root / "site"
            prepare_documentation(root, site)

            self.assertTrue(
                (site / "content/docs/reference/_index.md").is_file()
            )
            self.assertTrue(
                (site / "content/docs/reference/solidcraft/_index.md").is_file()
            )
            source = (
                site
                / "content/docs/reference/solidcraft/0.48.1/_index.md"
            ).read_text(encoding="utf-8")
            self.assertIn("title: \"SolidCraft 0.48.1 canonical reference snapshot\"", source)
            self.assertIn("(commands/)", source)
            commands = (
                site
                / "content/docs/reference/solidcraft/0.48.1/commands/index.md"
            ).read_text(encoding="utf-8")
            self.assertIn("title: \"Commands\"", commands)
            self.assertTrue(
                (
                    site
                    / "static/docs/reference/solidcraft/0.48.1/commands.json"
                ).is_file()
            )


if __name__ == "__main__":
    unittest.main()
