"""Tests for translating the generic CI build store into Forge site inputs."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import generic_site


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class GenericSiteTests(unittest.TestCase):
    def test_materialize_uses_physical_generic_item_paths(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            generic = root / "resolved"
            out = root / "site-evidence"
            write_json(
                generic / "build.json",
                {
                    "schema": 1,
                    "scope": "main",
                    "source_commit": "a" * 40,
                    "items": {
                        "examples/simple-box": {
                            "source_commit": "b" * 40,
                            "input_fingerprint": "case-input",
                            "result_fingerprint": "case-result",
                        },
                        "qualification/reference_suite": {
                            "source_commit": "c" * 40,
                            "input_fingerprint": "ref-input",
                            "result_fingerprint": "ref-result",
                        },
                        "qualification/diagrams": {
                            "source_commit": "d" * 40,
                            "input_fingerprint": "diagram-input",
                            "result_fingerprint": "diagram-result",
                        },
                    },
                },
            )
            native = (
                generic
                / "examples/simple-box/case/native/simple-box"
            )
            write_json(
                native / "qualification-result.json",
                {"status": "pass"},
            )
            (native / "model.png").write_bytes(b"png")

            reference = (
                generic
                / "qualification/reference_suite/references/simple-box/cadquery"
            )
            reference.mkdir(parents=True)
            (reference / "result.json").write_text("{}\n", encoding="utf-8")
            diagrams = generic / "qualification/diagrams/rendered"
            diagrams.mkdir(parents=True)
            (diagrams / "proof.svg").write_text("<svg/>\n", encoding="utf-8")

            with patch.object(
                generic_site,
                "supported_case_slugs",
                return_value=("simple-box",),
            ), patch.object(
                generic_site,
                "reference_implementations_for",
                return_value=("cadquery",),
            ):
                manifest = generic_site.materialize(
                    generic_root=generic,
                    out=out,
                    pull_request=12,
                    overlay_items=("simple-box", "reference-suite"),
                )

            scpf = manifest["cases"]["simple-box"]["implementations"]["scpf"]
            self.assertEqual(scpf["build_scope"], "pr/12")
            self.assertEqual(
                scpf["artifact_path"],
                "examples/simple-box/case/native/simple-box",
            )
            self.assertEqual(
                scpf["command_path"],
                "examples/simple-box/case/simple-box.json",
            )
            reference_record = manifest["cases"]["simple-box"][
                "implementations"
            ]["cadquery"]
            self.assertEqual(reference_record["build_scope"], "pr/12")
            self.assertEqual(
                reference_record["artifact_path"],
                "qualification/reference_suite/references/simple-box/cadquery",
            )
            self.assertTrue((out / "native/simple-box/model.png").is_file())
            self.assertTrue((out / "diagrams/proof.svg").is_file())

    def test_masked_case_does_not_claim_stale_native_evidence(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            generic = root / "resolved"
            write_json(
                generic / "build.json",
                {
                    "schema": 1,
                    "scope": "main",
                    "source_commit": "a" * 40,
                    "items": {
                        "examples/simple-box": {
                            "source_commit": "b" * 40,
                            "input_fingerprint": "case-input",
                            "result_fingerprint": "case-result",
                        }
                    },
                },
            )
            native = generic / "examples/simple-box/case/native/simple-box"
            write_json(native / "qualification-result.json", {"status": "pass"})

            with patch.object(
                generic_site,
                "supported_case_slugs",
                return_value=("simple-box",),
            ):
                manifest = generic_site.materialize(
                    generic_root=generic,
                    out=root / "out",
                    mask_cases=("simple-box",),
                )

            self.assertEqual(
                manifest["cases"]["simple-box"]["implementations"],
                {},
            )


if __name__ == "__main__":
    unittest.main()
