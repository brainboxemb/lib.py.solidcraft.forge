import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cad_library_build.publish import (
    PublishError,
    _preserve_release_baseline,
    publish,
    update_scope,
)


class PublishTests(unittest.TestCase):
    def test_full_then_incremental_preserves_unselected_model_owners(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate, target = root / "candidate", root / "target"
            for item in ("a", "b", "c"):
                path = candidate / "models" / item
                path.mkdir(parents=True)
                (path / "result.json").write_text(
                    json.dumps({"id": item, "status": "pass"})
                )
            update_scope(
                target,
                candidate,
                {
                    "active": ["a", "b", "c"],
                    "selected": ["a", "b", "c"],
                    "full": True,
                    "source_sha": "old",
                },
            )
            update_scope(
                target,
                candidate,
                {
                    "active": ["a", "b"],
                    "selected": ["b"],
                    "full": False,
                    "source_sha": "new",
                },
            )
            self.assertFalse((target / "models/c").exists())
            self.assertEqual(
                json.loads((target / "models/a/source.json").read_text())["source_sha"],
                "old",
            )
            self.assertEqual(
                json.loads((target / "models/b/source.json").read_text())["source_sha"],
                "new",
            )

    def test_release_only_stable_candidate_preserves_full_baseline(self):
        plan = {
            "release_only": True,
            "full": False,
            "library": True,
            "selected": [],
        }
        self.assertTrue(_preserve_release_baseline(plan, "main", "main"))

    @patch("cad_library_build.publish._prepare_worktree")
    @patch("cad_library_build.publish._require_fresh_source")
    def test_release_only_publish_does_not_replace_build_scope(
        self,
        fresh,
        prepare,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "candidate"
            candidate.mkdir()
            (root / "ci.yml").write_text(
                "branches:\n"
                "  stable: main\n"
                "  development: dev\n"
                "generated:\n"
                "  build_branch: build\n"
            )
            sha = "f" * 40
            (candidate / "build-plan.json").write_text(
                json.dumps(
                    {
                        "schema": 2,
                        "source_sha": sha,
                        "release_only": True,
                        "full": False,
                        "library": True,
                        "active": ["a"],
                        "selected": [],
                    }
                )
            )

            publish(root, candidate, "main", sha)

            fresh.assert_called_once_with(root.resolve(), "main", sha)
            prepare.assert_not_called()

    def test_release_only_candidate_is_rejected_outside_stable(self):
        plan = {
            "release_only": True,
            "full": False,
            "library": True,
            "selected": [],
        }
        with self.assertRaisesRegex(PublishError, "stable source"):
            _preserve_release_baseline(plan, "dev", "main")

    @patch("cad_library_build.publish._run")
    @patch("cad_library_build.publish._prepare_worktree")
    @patch("cad_library_build.publish._require_fresh_source")
    def test_exp_publication_updates_only_exp_scope(self, fresh, prepare, run):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "candidate"
            candidate.mkdir()
            (root / "ci.yml").write_text("branches:\n  stable: main\n  development: dev\ngenerated:\n  build_branch: build\n")
            sha = "e" * 40
            plan = {"schema": 2, "source_sha": sha, "active": [], "selected": [], "full": True, "library": True}
            (candidate / "build-plan.json").write_text(json.dumps(plan))
            def setup(repo, branch, target):
                target.mkdir()
                for scope in ("main", "dev"):
                    (target / scope).mkdir()
                    (target / scope / "sentinel").write_text(scope)
            def inspect(command, *, cwd, check=True):
                if command[:2] == ["git", "add"]:
                    self.assertEqual(command, ["git", "add", "-A", "--", "exp"])
                    self.assertEqual((cwd / "main/sentinel").read_text(), "main")
                    self.assertEqual((cwd / "dev/sentinel").read_text(), "dev")
                    self.assertEqual(json.loads((cwd / "exp/build-plan.json").read_text()), plan)
                return type("Result", (), {"returncode": 0})()
            prepare.side_effect = setup
            run.side_effect = inspect
            publish(root, candidate, "exp", sha)
            fresh.assert_called_once_with(root.resolve(), "exp", sha)

    def test_rejects_missing_active_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(PublishError):
                update_scope(
                    root / "target",
                    root / "candidate",
                    {
                        "active": ["a"],
                        "selected": [],
                        "full": False,
                        "source_sha": "new",
                    },
                )


if __name__ == "__main__":
    unittest.main()
