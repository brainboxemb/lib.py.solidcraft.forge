"""Integration tests for compare-and-swap generated-branch publication."""

from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.publish_generated import StaleSource, publish


def run(args, cwd):
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


class PublishGeneratedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.remote = self.root / "remote.git"
        self.repo = self.root / "repo"
        run(["git", "init", "--bare", str(self.remote)], self.root)
        run(["git", "init", str(self.repo)], self.root)
        run(["git", "config", "user.name", "test"], self.repo)
        run(["git", "config", "user.email", "test@example.com"], self.repo)
        run(["git", "remote", "add", "origin", str(self.remote)], self.repo)
        (self.repo / "seed").write_text("seed", encoding="utf-8")
        run(["git", "add", "."], self.repo)
        run(["git", "commit", "-m", "seed"], self.repo)
        source = run(["git", "rev-parse", "HEAD"], self.repo)
        run(["git", "branch", "-M", "main"], self.repo)
        run(["git", "push", "-u", "origin", "main"], self.repo)
        run(["git", "branch", "build"], self.repo)
        run(["git", "push", "origin", "build"], self.repo)
        run(["git", "branch", "gh-pages"], self.repo)
        run(["git", "push", "origin", "gh-pages"], self.repo)
        self.source = source

    def tearDown(self):
        self.tmp.cleanup()

    def test_replaces_only_owned_directory(self):
        source = self.root / "payload"
        source.mkdir()
        (source / "build.json").write_text("new", encoding="utf-8")

        publish(
            branch="build",
            operation="replace-dir",
            source=source,
            destination="pr/7",
            source_ref="main",
            expected_source=self.source,
            message="publish pr 7",
            cwd=self.repo,
        )

        run(["git", "fetch", "origin", "build"], self.repo)
        self.assertEqual(
            run(["git", "show", "FETCH_HEAD:pr/7/build.json"], self.repo),
            "new",
        )

    def test_stale_source_is_rejected_before_write(self):
        source = self.root / "payload"
        source.mkdir()
        (source / "x").write_text("x", encoding="utf-8")
        with self.assertRaises(StaleSource):
            publish(
                branch="build",
                operation="replace-dir",
                source=source,
                destination="pr/7",
                source_ref="main",
                expected_source="0" * 40,
                message="stale",
                cwd=self.repo,
            )

    def test_stable_pages_preserves_previews(self):
        preview = self.root / "preview"
        preview.mkdir()
        (preview / "index.html").write_text("preview", encoding="utf-8")
        publish(
            branch="gh-pages",
            operation="replace-dir",
            source=preview,
            destination="previews/pr-7",
            source_ref="main",
            expected_source=self.source,
            message="preview",
            cwd=self.repo,
        )

        stable = self.root / "stable"
        stable.mkdir()
        (stable / "index.html").write_text("stable", encoding="utf-8")
        publish(
            branch="gh-pages",
            operation="replace-stable-pages",
            source=stable,
            source_ref="main",
            expected_source=self.source,
            message="stable",
            cwd=self.repo,
        )

        run(["git", "fetch", "origin", "gh-pages"], self.repo)
        self.assertEqual(
            run(["git", "show", "FETCH_HEAD:index.html"], self.repo),
            "stable",
        )
        self.assertEqual(
            run(["git", "show", "FETCH_HEAD:previews/pr-7/index.html"], self.repo),
            "preview",
        )


if __name__ == "__main__":
    unittest.main()
