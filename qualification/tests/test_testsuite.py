"""Tests for qualification test discovery."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from qualification.testsuite import model_test_dirs, qualification_test_dirs


class TestSuiteDiscoveryTests(unittest.TestCase):
    def test_model_test_dirs_find_only_examples_with_tests(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "examples" / "b" / "tests").mkdir(parents=True)
            (root / "examples" / "a" / "tests").mkdir(parents=True)
            (root / "examples" / "empty" / "tests").mkdir(parents=True)
            (root / "examples" / "b" / "tests" / "test_contract.py").write_text(
                "import unittest\n",
                encoding="utf-8",
            )
            (root / "examples" / "a" / "tests" / "test_contract.py").write_text(
                "import unittest\n",
                encoding="utf-8",
            )

            self.assertEqual(
                model_test_dirs(root),
                (
                    root / "examples" / "a" / "tests",
                    root / "examples" / "b" / "tests",
                ),
            )

    def test_qualification_test_dirs_include_tooling_tests_first(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "qualification" / "tests").mkdir(parents=True)
            (root / "examples" / "case" / "tests").mkdir(parents=True)
            (root / "examples" / "case" / "tests" / "test_contract.py").write_text(
                "import unittest\n",
                encoding="utf-8",
            )

            self.assertEqual(
                qualification_test_dirs(root),
                (
                    root / "qualification" / "tests",
                    root / "examples" / "case" / "tests",
                ),
            )


if __name__ == "__main__":
    unittest.main()
