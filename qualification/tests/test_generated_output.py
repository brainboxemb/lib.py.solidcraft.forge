"""Tests for schema-v2 generated output and sparse overlays."""

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


def load_module():
    path = ROOT / "scripts" / "generated_output.py"
    spec = importlib.util.spec_from_file_location("generated_output", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class GeneratedOutputTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def _metadata(self, scope="pr", commit="abc123"):
        return {
            "scope": scope,
            "source_ref": "feature/test" if scope == "pr" else "main",
            "source_commit": commit,
            "pull_request": 42 if scope == "pr" else None,
            "forge_version": "0.10.0",
            "solidcraft_version": "0.42.0",
            "workflow_run_id": "99",
            "qualification": {
                "level": "affected-q1-q6" if scope == "pr" else "q1-q6-full",
                "status": "pass",
            },
        }

    def test_pr_build_is_sparse_and_schema_v2(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            output = root / "output"
            target = root / "build"
            for slug in ("simple-box", "components"):
                (repo / "examples" / slug / "scpf").mkdir(parents=True)
            (output / "native" / "simple-box").mkdir(parents=True)
            (output / "simple-box.json").write_text('{"commands": []}\n', encoding="utf-8")
            (output / "native" / "simple-box" / "model.step").write_bytes(b"step")

            with patch.object(self.module, "TECHNICAL_CASE_SLUGS", ("simple-box", "components")), \
                 patch.object(self.module, "case_input_hash", return_value="sha256:" + "1" * 64):
                data = self.module.assemble_build(
                    output,
                    target,
                    self._metadata(),
                    cases=("simple-box",),
                    repo_root=repo,
                )

            self.assertEqual(data["schema_version"], 2)
            self.assertEqual(set(data["cases"]), {"simple-box"})
            self.assertTrue((target / "examples" / "simple-box" / "scpf").is_dir())
            self.assertFalse((target / "examples" / "components").exists())
            record = data["cases"]["simple-box"]["implementations"]["scpf"]
            self.assertEqual(record["source_commit"], "abc123")
            self.assertEqual(record["verification_level"], "affected-q1-q6")

    def test_complete_main_baseline_does_not_recalculate_case_hashes(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            build = root / "main"
            for slug in ("simple-box", "components"):
                (build / "examples" / slug / "scpf").mkdir(parents=True)
            manifest = {
                "schema_version": 2,
                "scope": "main",
                "source_ref": "main",
                "source_commit": "qualified",
                "pull_request": None,
                "workflow_run_id": "1",
                "toolchain": {},
                "verification": {"level": "q1-q6-full", "status": "pass"},
                "generated_at": "2026-01-01T00:00:00Z",
                "cases": {},
            }
            for slug in ("simple-box", "components"):
                manifest["cases"][slug] = {
                    "implementations": {
                        "scpf": {
                            "source_commit": "qualified",
                            "build_scope": "main",
                            "input_hash": "sha256:" + "4" * 64,
                            "verification_level": "q1-q6-full",
                            "status": "pass",
                            "generated_at": "2026-01-01T00:00:00Z",
                        }
                    }
                }
            (build / "build.json").write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )

            with patch.object(
                self.module,
                "TECHNICAL_CASE_SLUGS",
                ("simple-box", "components"),
            ), patch.object(
                self.module,
                "case_input_hash",
                side_effect=AssertionError("presentation reuse must not recalculate hashes"),
            ):
                verified = self.module.verify_build(
                    build,
                    require_complete=True,
                    repo_root=root,
                )

            self.assertEqual(verified["source_commit"], "qualified")

    def test_complete_main_baseline_rejects_missing_case(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            build = root / "main"
            (build / "examples" / "simple-box" / "scpf").mkdir(parents=True)
            manifest = {
                "schema_version": 2,
                "scope": "main",
                "source_ref": "main",
                "source_commit": "qualified",
                "pull_request": None,
                "workflow_run_id": "1",
                "toolchain": {},
                "verification": {"level": "q1-q6-full", "status": "pass"},
                "generated_at": "2026-01-01T00:00:00Z",
                "cases": {
                    "simple-box": {
                        "implementations": {
                            "scpf": {
                                "source_commit": "qualified",
                                "build_scope": "main",
                                "input_hash": "sha256:" + "5" * 64,
                                "verification_level": "q1-q6-full",
                                "status": "pass",
                                "generated_at": "2026-01-01T00:00:00Z",
                            }
                        }
                    }
                },
            }
            (build / "build.json").write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )

            with patch.object(
                self.module,
                "TECHNICAL_CASE_SLUGS",
                ("simple-box", "components"),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "main build is missing registered cases",
                ):
                    self.module.verify_build(
                        build,
                        require_complete=True,
                        repo_root=root,
                    )

    def test_promotion_replaces_one_case_and_preserves_other(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            main = root / "main"
            overlay = root / "overlay"
            dest = root / "dest"
            for base, scope, commit in (
                (main, "main", "old"),
                (overlay, "pr", "new"),
            ):
                (base / "examples" / "simple-box" / "scpf").mkdir(parents=True)
                (base / "qualification").mkdir()
                (base / "examples" / "simple-box" / "scpf" / "marker").write_text(
                    commit, encoding="utf-8"
                )
            (main / "examples" / "components" / "scpf").mkdir(parents=True)
            (main / "examples" / "components" / "scpf" / "marker").write_text(
                "keep", encoding="utf-8"
            )

            def record(commit, level, scope):
                return {
                    "source_commit": commit,
                    "build_scope": scope,
                    "input_hash": "sha256:" + "2" * 64,
                    "verification_level": level,
                    "status": "pass",
                    "generated_at": "2026-01-01T00:00:00Z",
                }

            main_manifest = {
                "schema_version": 2,
                "scope": "main",
                "source_ref": "main",
                "source_commit": "old",
                "pull_request": None,
                "workflow_run_id": "1",
                "toolchain": {},
                "verification": {"level": "q1-q6-full", "status": "pass"},
                "generated_at": "2026-01-01T00:00:00Z",
                "cases": {
                    "simple-box": {"implementations": {"scpf": record("old", "q1-q6-full", "main")}},
                    "components": {"implementations": {"scpf": record("old", "q1-q6-full", "main")}},
                },
            }
            overlay_manifest = {
                **main_manifest,
                "scope": "pr",
                "source_ref": "feature",
                "source_commit": "new",
                "pull_request": 42,
                "cases": {
                    "simple-box": {"implementations": {"scpf": record("new", "affected-q1-q6", "pr/42")}},
                },
            }
            (main / "build.json").write_text(json.dumps(main_manifest), encoding="utf-8")
            (overlay / "build.json").write_text(json.dumps(overlay_manifest), encoding="utf-8")

            with patch.object(self.module, "TECHNICAL_CASE_SLUGS", ("simple-box", "components")):
                merged = self.module.promote_overlay(
                    main,
                    overlay,
                    dest,
                    required_level="affected-q1-q6",
                    source_commit="merge",
                    repo_root=root,
                )

            self.assertEqual(
                (dest / "examples" / "simple-box" / "scpf" / "marker").read_text(),
                "new",
            )
            self.assertEqual(
                (dest / "examples" / "components" / "scpf" / "marker").read_text(),
                "keep",
            )
            self.assertEqual(
                merged["cases"]["components"]["implementations"]["scpf"]["source_commit"],
                "old",
            )

    def test_main_candidate_replaces_affected_case_and_preserves_complete_baseline(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            main = root / "main"
            candidate = root / "candidate"
            dest = root / "dest"
            for base in (main, candidate):
                (base / "qualification").mkdir(parents=True)
                (base / "examples" / "simple-box" / "scpf").mkdir(parents=True)

            (main / "examples" / "simple-box" / "scpf" / "marker").write_text("old")
            (candidate / "examples" / "simple-box" / "scpf" / "marker").write_text("new")
            (main / "examples" / "components" / "scpf").mkdir(parents=True)
            (main / "examples" / "components" / "scpf" / "marker").write_text("keep")

            def record(commit, level, scope):
                return {
                    "source_commit": commit,
                    "build_scope": scope,
                    "input_hash": "sha256:" + "4" * 64,
                    "verification_level": level,
                    "status": "pass",
                    "generated_at": "2026-01-01T00:00:00Z",
                }

            main_manifest = {
                "schema_version": 2,
                "scope": "main",
                "source_ref": "main",
                "source_commit": "old",
                "pull_request": None,
                "workflow_run_id": "1",
                "toolchain": {},
                "verification": {"level": "per-case", "status": "pass"},
                "generated_at": "2026-01-01T00:00:00Z",
                "cases": {
                    "simple-box": {"implementations": {"scpf": record("old", "q1-q6-full", "main")}},
                    "components": {"implementations": {"scpf": record("old", "q1-q6-full", "main")}},
                },
            }
            candidate_manifest = {
                **main_manifest,
                "source_commit": "new-main",
                "workflow_run_id": "2",
                "verification": {"level": "affected-q1-q6", "status": "pass"},
                "cases": {
                    "simple-box": {
                        "implementations": {
                            "scpf": record("new-main", "affected-q1-q6", "main")
                        }
                    }
                },
            }
            (main / "build.json").write_text(json.dumps(main_manifest), encoding="utf-8")
            (candidate / "build.json").write_text(
                json.dumps(candidate_manifest), encoding="utf-8"
            )

            with patch.object(
                self.module,
                "TECHNICAL_CASE_SLUGS",
                ("simple-box", "components"),
            ):
                merged = self.module.promote_overlay(
                    main,
                    candidate,
                    dest,
                    required_level="affected-q1-q6",
                    source_commit="new-main",
                    source_ref="main",
                    workflow_run_id="2",
                    repo_root=root,
                )

            self.assertEqual(
                (dest / "examples/simple-box/scpf/marker").read_text(),
                "new",
            )
            self.assertEqual(
                (dest / "examples/components/scpf/marker").read_text(),
                "keep",
            )
            self.assertEqual(merged["source_commit"], "new-main")
            self.assertEqual(merged["scope"], "main")
            self.assertEqual(
                merged["cases"]["simple-box"]["implementations"]["scpf"]["build_scope"],
                "main",
            )

    def test_main_candidate_must_match_promotion_target(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            main = root / "main"
            candidate = root / "candidate"
            dest = root / "dest"
            for base in (main, candidate):
                base.mkdir()
                (base / "build.json").write_text(
                    json.dumps(
                        {
                            "schema_version": 2,
                            "scope": "main",
                            "source_ref": "main",
                            "source_commit": "candidate" if base == candidate else "old",
                            "pull_request": None,
                            "workflow_run_id": "1",
                            "toolchain": {},
                            "verification": {"level": "per-case", "status": "pass"},
                            "generated_at": "2026-01-01T00:00:00Z",
                            "cases": {},
                        }
                    ),
                    encoding="utf-8",
                )
            with patch.object(self.module, "TECHNICAL_CASE_SLUGS", ()):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "main candidate source commit does not match",
                ):
                    self.module.promote_overlay(
                        main,
                        candidate,
                        dest,
                        required_level="affected-q1-q6",
                        source_commit="different",
                        repo_root=root,
                    )

    def test_complete_overlay_can_bootstrap_legacy_main(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            legacy = root / "legacy"
            overlay = root / "overlay"
            dest = root / "dest"
            legacy.mkdir()
            (legacy / "build.json").write_text(
                json.dumps({"schema_version": 1}),
                encoding="utf-8",
            )
            for slug in ("simple-box", "components"):
                (overlay / "examples" / slug / "scpf").mkdir(parents=True)
                (overlay / "examples" / slug / "scpf" / "marker").write_text(slug)
            manifest = {
                "schema_version": 2,
                "scope": "pr",
                "source_ref": "feature",
                "source_commit": "head",
                "pull_request": 7,
                "workflow_run_id": "1",
                "toolchain": {},
                "verification": {"level": "q1-q6-full", "status": "pass"},
                "generated_at": "2026-01-01T00:00:00Z",
                "cases": {},
            }
            for slug in ("simple-box", "components"):
                manifest["cases"][slug] = {
                    "implementations": {
                        "scpf": {
                            "source_commit": "head",
                            "build_scope": "pr/7",
                            "input_hash": "sha256:" + "3" * 64,
                            "verification_level": "q1-q6-full",
                            "status": "pass",
                            "generated_at": "2026-01-01T00:00:00Z",
                        }
                    }
                }
            (overlay / "build.json").write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )
            with patch.object(self.module, "TECHNICAL_CASE_SLUGS", ("simple-box", "components")):
                merged = self.module.promote_overlay(
                    legacy,
                    overlay,
                    dest,
                    required_level="q1-q6-full",
                    source_commit="merge",
                    repo_root=root,
                )
            self.assertEqual(merged["scope"], "main")
            self.assertEqual(set(merged["cases"]), {"simple-box", "components"})
            for case in merged["cases"].values():
                self.assertEqual(
                    case["implementations"]["scpf"]["build_scope"],
                    "main",
                )

    def test_promotion_rejects_insufficient_level(self):
        self.assertLess(
            self.module.LEVEL_RANK["affected-q1-q2"],
            self.module.LEVEL_RANK["affected-q1-q6"],
        )

    def test_stable_pages_preserves_previews(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            site = root / "site"
            current = root / "current"
            destination = root / "destination"
            site.mkdir()
            (site / "index.html").write_text("new", encoding="utf-8")
            (site / "provenance.json").write_text("{}\n", encoding="utf-8")
            (current / "previews" / "pr-7").mkdir(parents=True)
            (current / "previews" / "pr-7" / "index.html").write_text("preview")
            self.module.prepare_stable_pages(site, current, destination)
            self.assertEqual((destination / "index.html").read_text(), "new")
            self.assertEqual(
                (destination / "previews" / "pr-7" / "index.html").read_text(),
                "preview",
            )

    def test_remove_pr_is_scoped(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "pr" / "7").mkdir(parents=True)
            (root / "pr" / "8").mkdir(parents=True)
            self.assertTrue(self.module.remove_pr(root, "build", 7))
            self.assertFalse((root / "pr" / "7").exists())
            self.assertTrue((root / "pr" / "8").exists())


if __name__ == "__main__":
    unittest.main()
