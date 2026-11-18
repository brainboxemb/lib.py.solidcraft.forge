"""Tests for qualification test discovery and in-memory execution."""

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from qualification.testsuite import (
    build_suite,
    model_test_dirs,
    qualification_test_dirs,
    qualification_test_files,
)


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

    def test_test_file_discovery_is_cached_in_memory(self):
        with TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            tooling = root / "qualification" / "tests"
            model = root / "examples" / "case" / "tests"
            tooling.mkdir(parents=True)
            model.mkdir(parents=True)
            (tooling / "test_tooling.py").write_text(
                "import unittest\n",
                encoding="utf-8",
            )
            (model / "test_contract.py").write_text(
                "import unittest\n",
                encoding="utf-8",
            )

            first = qualification_test_files(root)
            second = qualification_test_files(root)

            self.assertIs(first, second)
            self.assertEqual(
                first,
                (
                    tooling / "test_tooling.py",
                    model / "test_contract.py",
                ),
            )

    def test_same_test_filename_from_multiple_models_runs_in_one_suite(self):
        with TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            tooling = root / "qualification" / "tests"
            first = root / "examples" / "first-case" / "tests"
            second = root / "examples" / "second-case" / "tests"
            tooling.mkdir(parents=True)
            first.mkdir(parents=True)
            second.mkdir(parents=True)

            (tooling / "test_tooling.py").write_text(
                "import unittest\n"
                "class ToolingTest(unittest.TestCase):\n"
                "    def test_tooling(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8",
            )
            for directory, class_name in (
                (first, "FirstContractTest"),
                (second, "SecondContractTest"),
            ):
                (directory / "test_contract.py").write_text(
                    "import unittest\n"
                    f"class {class_name}(unittest.TestCase):\n"
                    "    def test_contract(self):\n"
                    "        self.assertTrue(True)\n",
                    encoding="utf-8",
                )

            suite = build_suite(root)
            stream = StringIO()
            result = unittest.TextTestRunner(stream=stream).run(suite)

            self.assertTrue(result.wasSuccessful(), stream.getvalue())
            self.assertEqual(result.testsRun, 3)


if __name__ == "__main__":
    unittest.main()
