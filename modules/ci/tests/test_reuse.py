import io
import json
from email.message import Message
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import zipfile

from cad_library_ci.reuse import (
    _download_artifact,
    _rebind_plan,
    _require_same_qualified_tree,
    materialize,
)


class ReuseQualificationTests(unittest.TestCase):
    @patch("cad_library_ci.reuse.request.urlopen")
    @patch("cad_library_ci.reuse.request.build_opener")
    def test_artifact_download_strips_github_auth_on_signed_redirect(
        self,
        build_opener,
        urlopen,
    ):
        headers = Message()
        headers["Location"] = "https://blob.example/artifact.zip?sig=abc"
        build_opener.return_value.open.side_effect = __import__(
            "urllib.error", fromlist=["HTTPError"]
        ).HTTPError(
            "https://api.github.com/artifact",
            302,
            "Found",
            headers,
            None,
        )
        blob = MagicMock()
        blob.__enter__.return_value.read.return_value = b"zip-bytes"
        urlopen.return_value = blob

        self.assertEqual(
            _download_artifact("owner/repo", 99, "secret"),
            b"zip-bytes",
        )

        api_request = build_opener.return_value.open.call_args.args[0]
        self.assertEqual(
            api_request.get_header("Authorization"),
            "Bearer secret",
        )
        blob_request = urlopen.call_args.args[0]
        self.assertIsNone(blob_request.get_header("Authorization"))
        self.assertEqual(
            blob_request.full_url,
            "https://blob.example/artifact.zip?sig=abc",
        )

    @patch("cad_library_ci.reuse._commit")
    def test_same_qualified_tree_requires_exact_pr_merge_parents(self, commit):
        base = "d" * 40
        head = "c" * 40
        tree = "e" * 40
        commit.side_effect = [
            {"tree": {"sha": tree}, "parents": [{"sha": base}]},
            {
                "tree": {"sha": tree},
                "parents": [{"sha": base}, {"sha": head}],
            },
        ]
        _require_same_qualified_tree(
            repository="owner/repo",
            source_sha="b" * 40,
            qualified_source_sha="a" * 40,
            base_sha=base,
            head_sha=head,
            token="token",
        )

    @patch("cad_library_ci.reuse._commit")
    def test_same_qualified_tree_rejects_changed_tree(self, commit):
        commit.side_effect = [
            {"tree": {"sha": "1" * 40}, "parents": []},
            {"tree": {"sha": "2" * 40}, "parents": []},
        ]
        with self.assertRaisesRegex(ValueError, "differs"):
            _require_same_qualified_tree(
                repository="owner/repo",
                source_sha="b" * 40,
                qualified_source_sha="a" * 40,
                base_sha="d" * 40,
                head_sha="c" * 40,
                token="token",
            )

    def test_rebind_plan_records_permanent_and_qualified_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp)
            qualified = "a" * 40
            head = "c" * 40
            source = "b" * 40
            (candidate / "build-plan.json").write_text(
                json.dumps(
                    {
                        "schema": 2,
                        "source_sha": qualified,
                        "active": [],
                        "selected": [],
                        "full": False,
                        "library": False,
                    }
                )
            )
            _rebind_plan(
                candidate,
                source_sha=source,
                qualified_source_sha=qualified,
                qualified_head_sha=head,
                pr_number=12,
                run_id=34,
            )
            plan = json.loads((candidate / "build-plan.json").read_text())
            self.assertEqual(plan["source_sha"], source)
            self.assertEqual(plan["qualified_source_sha"], qualified)
            self.assertEqual(plan["qualified_head_sha"], head)
            self.assertTrue(plan["qualification_reused"])
            self.assertEqual(plan["qualification_pr"], 12)
            self.assertEqual(plan["qualification_run_id"], 34)

    def test_rebind_plan_rejects_artifact_from_other_qualified_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp)
            (candidate / "build-plan.json").write_text(
                json.dumps({"schema": 2, "source_sha": "wrong"})
            )
            with self.assertRaisesRegex(ValueError, "provenance mismatch"):
                _rebind_plan(
                    candidate,
                    source_sha="b" * 40,
                    qualified_source_sha="a" * 40,
                    qualified_head_sha="c" * 40,
                    pr_number=12,
                    run_id=34,
                )

    @patch("cad_library_ci.reuse._require_same_qualified_tree")
    @patch("cad_library_ci.reuse._download_artifact")
    @patch("cad_library_ci.reuse.reusable_pr_qualification")
    def test_materialize_reuses_bound_tree_identical_green_pr(
        self,
        evidence,
        download,
        same_tree,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "build/qualification"
            qualified = "a" * 40
            source = "b" * 40
            head = "c" * 40
            base = "d" * 40
            (root / "ci.yml").write_text(
                "schema: 1\n"
                "branches:\n"
                "  stable: main\n"
                "  development: dev\n"
                "roots:\n"
                "  modules: modules\n"
                "  models: models\n"
                "  output: build\n"
                "qualification:\n"
                "  permanent:\n"
                "    reuse_pr_qualification:\n"
                "      branches: [exp]\n"
            )
            evidence.return_value = SimpleNamespace(
                artifact_id=99,
                head_sha=head,
                base_sha=base,
                pr_number=12,
                run_id=34,
            )
            payload = io.BytesIO()
            with zipfile.ZipFile(payload, "w") as archive:
                archive.writestr(
                    "build-plan.json",
                    json.dumps(
                        {
                            "schema": 2,
                            "source_sha": qualified,
                            "active": [],
                            "selected": [],
                            "full": False,
                            "library": False,
                        }
                    ),
                )
            download.return_value = payload.getvalue()

            result = materialize(
                repo=root,
                repository="owner/repo",
                branch="exp",
                source_sha=source,
                token="token",
                candidate=candidate,
                pr_number=12,
                head_sha=head,
                run_id=34,
            )

            self.assertTrue(result["reuse"])
            plan = json.loads((candidate / "build-plan.json").read_text())
            self.assertEqual(plan["source_sha"], source)
            self.assertEqual(plan["qualified_source_sha"], qualified)
            self.assertEqual(plan["qualified_head_sha"], head)
            same_tree.assert_called_once_with(
                repository="owner/repo",
                source_sha=source,
                qualified_source_sha=qualified,
                base_sha=base,
                head_sha=head,
                token="token",
            )

    def test_materialize_is_disabled_for_unconfigured_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ci.yml").write_text(
                "schema: 1\n"
                "branches:\n"
                "  stable: main\n"
                "  development: dev\n"
                "roots:\n"
                "  modules: modules\n"
                "  models: models\n"
                "  output: build\n"
            )
            result = materialize(
                repo=root,
                repository="owner/repo",
                branch="exp",
                source_sha="b" * 40,
                token="token",
                candidate=root / "candidate",
                pr_number=12,
                head_sha="c" * 40,
                run_id=34,
            )
            self.assertFalse(result["reuse"])
            self.assertEqual(result["reason"], "branch-not-configured")

    @patch("cad_library_ci.reuse._require_same_qualified_tree")
    @patch("cad_library_ci.reuse._download_artifact")
    @patch("cad_library_ci.reuse.discover_reusable_pr_qualification")
    def test_materialize_discovers_reusable_pr_without_merge_policy_binding(
        self,
        discover,
        download,
        same_tree,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "candidate"
            qualified = "a" * 40
            source = "b" * 40
            head = "c" * 40
            base = "d" * 40
            (root / "ci.yml").write_text(
                "schema: 1\n"
                "branches:\n"
                "  stable: main\n"
                "  development: dev\n"
                "roots:\n"
                "  modules: modules\n"
                "  models: models\n"
                "  output: build\n"
                "qualification:\n"
                "  permanent:\n"
                "    reuse_pr_qualification:\n"
                "      branches: [exp]\n"
            )
            discover.return_value = SimpleNamespace(
                artifact_id=99,
                head_sha=head,
                base_sha=base,
                pr_number=12,
                run_id=34,
            )
            payload = io.BytesIO()
            with zipfile.ZipFile(payload, "w") as archive:
                archive.writestr(
                    "build-plan.json",
                    json.dumps(
                        {
                            "schema": 2,
                            "source_sha": qualified,
                            "active": [],
                            "selected": [],
                            "full": False,
                            "library": False,
                        }
                    ),
                )
            download.return_value = payload.getvalue()

            result = materialize(
                repo=root,
                repository="owner/repo",
                branch="exp",
                source_sha=source,
                token="token",
                candidate=candidate,
            )
            self.assertTrue(result["reuse"])
            self.assertEqual(
                result["reason"],
                "discovered-tree-identical-green-pr",
            )
            same_tree.assert_called_once()

    @patch(
        "cad_library_ci.reuse.discover_reusable_pr_qualification",
        return_value=None,
    )
    def test_materialize_without_binding_or_discoverable_evidence_falls_back(
        self,
        _discover,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ci.yml").write_text(
                "schema: 1\n"
                "branches:\n"
                "  stable: main\n"
                "  development: dev\n"
                "roots:\n"
                "  modules: modules\n"
                "  models: models\n"
                "  output: build\n"
                "qualification:\n"
                "  permanent:\n"
                "    reuse_pr_qualification:\n"
                "      branches: [exp]\n"
            )
            result = materialize(
                repo=root,
                repository="owner/repo",
                branch="exp",
                source_sha="b" * 40,
                token="token",
                candidate=root / "candidate",
            )
            self.assertFalse(result["reuse"])
            self.assertEqual(result["reason"], "no-reusable-pr-evidence")


if __name__ == "__main__":
    unittest.main()
