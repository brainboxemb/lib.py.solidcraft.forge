"""Guard the Forge package/test/release CAD-CI dependency graph."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "scpf" / "ci.yml"
TESTS = ROOT / "ci" / "forge-tests" / "ci.yml"
RELEASE = ROOT / "ci" / "forge-release" / "ci.yml"
EXAMPLES = ROOT / "examples"


def needs(text: str) -> set[str]:
    """Return the simple top-level needs list from one Forge ci.yml."""

    match = re.search(
        r"^needs:\s*\n((?:  - [^\n]+\n)+)",
        text,
        re.MULTILINE,
    )
    if match is None:
        return set()
    return {
        line.removeprefix("  - ").strip()
        for line in match.group(1).splitlines()
    }


class CiPackageDependencyContractTests(unittest.TestCase):
    """Keep package consumers independent from tests/release verification."""

    def test_package_item_only_builds_the_wheel(self):
        text = PACKAGE.read_text(encoding="utf-8")
        self.assertIn("id: forge-package", text)
        self.assertIn("- id: tool_build", text)
        self.assertNotIn("- id: tool_test", text)
        self.assertNotIn("- id: tool_verify", text)
        self.assertIn("outputs: [dist]", text)

    def test_unit_tests_depend_only_on_package(self):
        text = TESTS.read_text(encoding="utf-8")
        self.assertIn("id: forge-tests", text)
        self.assertEqual(needs(text), {"forge-package"})
        self.assertIn("- id: tool_test", text)
        self.assertIn("- scpf/scpf/**", text)
        self.assertNotIn("tool_build", text)
        self.assertNotIn("tool_verify", text)

    def test_release_verification_depends_only_on_package(self):
        text = RELEASE.read_text(encoding="utf-8")
        self.assertIn("id: forge-release", text)
        self.assertEqual(needs(text), {"forge-package"})
        self.assertIn("- id: tool_verify", text)
        self.assertIn("- scpf/scpf/**", text)
        self.assertNotIn("tool_build", text)
        self.assertNotIn("tool_test", text)

    def test_every_model_depends_only_on_package(self):
        configs = sorted(EXAMPLES.glob("*/ci.yml"))
        self.assertEqual(len(configs), 32)
        for path in configs:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(needs(text), {"forge-package"})
                self.assertNotIn("forge-tool", text)
                self.assertNotIn("forge-tests", text)
                self.assertNotIn("forge-release", text)

    def test_root_manifest_discovers_split_checks(self):
        text = (ROOT / "cad-ci.yml").read_text(encoding="utf-8")
        self.assertIn("  - scpf\n", text)
        self.assertIn("  - ci/*\n", text)

    def test_consumers_resolve_dependency_wheel(self):
        tool_ci = (ROOT / "scripts" / "tool_ci.py").read_text(encoding="utf-8")
        tool_verify = (
            ROOT / "scripts" / "tool_verify.py"
        ).read_text(encoding="utf-8")
        forge_example = (
            ROOT / "scripts" / "forge_example.py"
        ).read_text(encoding="utf-8")

        self.assertIn('dependency_wheel("forge-package")', tool_ci)
        self.assertIn('dependency_wheel("forge-package")', tool_verify)
        self.assertIn(
            'def dependency_wheel(name: str = "forge-package")',
            forge_example,
        )


if __name__ == "__main__":
    unittest.main()
