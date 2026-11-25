import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from cad_library_release.__main__ import (
    ReleaseQualificationError,
    validate_build_scope,
    validate_release_source,
)
from cad_library_release.delta import (
    ReleaseDeltaError,
    validate_metadata_delta,
)


SHA = "a" * 40


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        text=True,
    ).strip()


class ReleaseQualificationTests(unittest.TestCase):
    def _scope(self, root: Path, *, source_sha=SHA, full=True, library=True,
               active=("one",), selected=None, status="pass", provenance=None):
        if selected is None:
            selected = active
        if provenance is None:
            provenance = source_sha
        scope = root / "main"
        scope.mkdir(parents=True)
        (scope / "build-plan.json").write_text(
            json.dumps(
                {
                    "schema": 2,
                    "source_sha": source_sha,
                    "library": library,
                    "full": full,
                    "active": list(active),
                    "selected": list(selected),
                    "models": [{"id": item} for item in active],
                }
            ),
            encoding="utf-8",
        )
        for item in active:
            model = scope / "models" / item
            model.mkdir(parents=True)
            (model / "result.json").write_text(
                json.dumps({"id": item, "status": status}), encoding="utf-8"
            )
            (model / "source.json").write_text(
                json.dumps({"source_sha": provenance}), encoding="utf-8"
            )
        return scope

    def _repo(self, root: Path) -> tuple[Path, str]:
        repo = root / "source"
        repo.mkdir()
        subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True,
                       capture_output=True, text=True)
        subprocess.run(["git", "config", "user.name", "Tests"], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "user.email", "tests@example.invalid"],
            cwd=repo,
            check=True,
        )
        (repo / "cadlib").mkdir()
        (repo / "cadlib" / "pyproject.toml").write_text(
            '[project]\nname = "demo"\nversion = "1.0.0"\n',
            encoding="utf-8",
        )
        (repo / "CHANGELOG.md").write_text(
            "## [Unreleased]\n",
            encoding="utf-8",
        )
        (repo / "product.py").write_text("VALUE = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", "product baseline"], cwd=repo, check=True,
                       capture_output=True, text=True)
        return repo, git(repo, "rev-parse", "HEAD")

    def _commit(self, repo: Path, message: str) -> str:
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True,
                       capture_output=True, text=True)
        return git(repo, "rev-parse", "HEAD")

    def test_accepts_exact_full_library_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            scope = self._scope(Path(tmp), active=("one", "two"))
            plan = validate_build_scope(scope, SHA)
            self.assertTrue(plan["library"])
            self.assertEqual(plan["selected"], ["one", "two"])

    def test_rejects_source_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            scope = self._scope(Path(tmp), source_sha="b" * 40)
            with self.assertRaisesRegex(ReleaseQualificationError, "does not match"):
                validate_build_scope(scope, SHA)

    def test_requires_full_library_qualification(self):
        for field, kwargs, message in (
            ("full", {"full": False}, "full stable build"),
            ("library", {"library": False}, "qualify the library"),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                scope = self._scope(Path(tmp), **kwargs)
                with self.assertRaisesRegex(ReleaseQualificationError, message):
                    validate_build_scope(scope, SHA)

    def test_requires_all_active_owners_selected(self):
        with tempfile.TemporaryDirectory() as tmp:
            scope = self._scope(Path(tmp), active=("one", "two"), selected=("one",))
            with self.assertRaisesRegex(ReleaseQualificationError, "every active"):
                validate_build_scope(scope, SHA)

    def test_requires_successful_matching_model_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            scope = self._scope(Path(tmp), status="fail")
            with self.assertRaisesRegex(ReleaseQualificationError, "not successful"):
                validate_build_scope(scope, SHA)
        with tempfile.TemporaryDirectory() as tmp:
            scope = self._scope(Path(tmp), provenance="b" * 40)
            with self.assertRaisesRegex(ReleaseQualificationError, "model source"):
                validate_build_scope(scope, SHA)

    def test_accepts_one_or_more_release_metadata_commits_after_full_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, base = self._repo(root)
            scope = self._scope(root / "build", source_sha=base)

            (repo / "cadlib" / "pyproject.toml").write_text(
                '[project]\nname = "demo"\nversion = "1.0.1"\n',
                encoding="utf-8",
            )
            first = self._commit(repo, "release 1.0.1")
            (repo / "CHANGELOG.md").write_text(
                "## [Unreleased]\n\n## [1.0.1] - 2026-11-25\n",
                encoding="utf-8",
            )
            target = self._commit(repo, "release notes")

            plan, paths = validate_release_source(scope, repo, target)
            self.assertEqual(plan["source_sha"], base)
            self.assertEqual(
                set(paths),
                {"CHANGELOG.md", "cadlib/pyproject.toml"},
            )
            self.assertNotEqual(first, target)

    def test_rejects_non_version_pyproject_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, base = self._repo(root)
            (repo / "cadlib" / "pyproject.toml").write_text(
                '[project]\n'
                'name = "demo"\n'
                'version = "1.0.1"\n'
                'dependencies = ["new-runtime"]\n',
                encoding="utf-8",
            )
            target = self._commit(repo, "change release version and dependency")

            with self.assertRaisesRegex(
                ReleaseDeltaError,
                "more than project.version",
            ):
                validate_metadata_delta(repo, base, target)

    def test_rejects_product_change_after_full_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo, base = self._repo(root)
            scope = self._scope(root / "build", source_sha=base)

            (repo / "product.py").write_text("VALUE = 2\n", encoding="utf-8")
            target = self._commit(repo, "product change")

            with self.assertRaisesRegex(
                ReleaseQualificationError,
                "product/non-release",
            ):
                validate_release_source(scope, repo, target)


if __name__ == "__main__":
    unittest.main()
