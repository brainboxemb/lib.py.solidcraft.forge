"""Small contract tests for verification setup helpers."""

import unittest

from qualification.setup_solidcraft import checksum_for
from qualification.setup_references import load_toolchain, pip_specs


class SetupTests(unittest.TestCase):
    def test_checksum_parser_selects_exact_archive(self):
        digest = "a" * 64
        text = f"{digest}  solidcraft-0.42.0-linux-x86_64.tar.gz\n"
        self.assertEqual(
            checksum_for(text, "solidcraft-0.42.0-linux-x86_64.tar.gz"),
            digest,
        )

    def test_reference_specs_come_from_versioned_toolchain(self):
        specs = pip_specs(load_toolchain())
        self.assertTrue(any(item.startswith("pythonscad==") for item in specs))
        self.assertTrue(any(item.startswith("cadquery==") for item in specs))
        self.assertTrue(any("pybosl2@" in item for item in specs))


if __name__ == "__main__":
    unittest.main()
