from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cad_library_mitcad_reference import (
    MitcadReferenceError,
    git_blob_sha,
    validate_catalog,
    verify_runtime_snapshot,
    verify_source_snapshot,
    write_snapshot,
)


ROOT = Path(__file__).resolve().parents[3]
VERSION = "0.70.0"
REFERENCE_BLOB = "40240776bc6885e228bf2fbd8e2534875aa61b85"


def catalog():
    commands = ["add_feature", "add_parameter", "edit_feature"]
    commands.extend(f"test.command_{i}" for i in range(60))
    return {
        "contents": "## test",
        "guides": [],
        "queries": ["bodies"],
        "commands": commands,
        "features": ["box", "extrude", "fillet"],
        "schemas": ["add_feature"],
        "usage": "test",
    }


class MitcadReferenceTests(unittest.TestCase):
    def test_checked_source_reference_is_exact_upstream_blob(self):
        snapshot = ROOT / "docs/reference/mitcad/0.70.0"
        verify_source_snapshot(snapshot, reference_blob=REFERENCE_BLOB)
        source = (snapshot / "SOURCE.md").read_text(encoding="utf-8")
        self.assertIn("v0.70.0", source)
        self.assertIn(
            "806a4210126ab977ba678708dd476496ddbd2968",
            source,
        )

    def test_catalog_rejects_curated_subset(self):
        with self.assertRaisesRegex(ValueError, "implausibly small"):
            validate_catalog(
                {
                    "commands": ["add_feature"],
                    "queries": [],
                    "features": ["box"],
                }
            )

    def test_write_snapshot_requires_reference_blob_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            reference = "# exact reference\n"
            blob = git_blob_sha(reference)
            write_snapshot(
                out=out,
                version=VERSION,
                upstream_commit="8" * 40,
                release_tag="v0.70.0",
                reference_blob=blob,
                cli_version="mitcad-cli 0.70.0",
                reference=reference,
                catalog=catalog(),
            )
            self.assertEqual(
                json.loads((out / "commands.json").read_text()),
                catalog(),
            )
            with self.assertRaisesRegex(
                MitcadReferenceError, "differs from the pinned upstream blob"
            ):
                write_snapshot(
                    out=out,
                    version=VERSION,
                    upstream_commit="8" * 40,
                    release_tag="v0.70.0",
                    reference_blob="0" * 40,
                    cli_version="mitcad-cli 0.70.0",
                    reference=reference,
                    catalog=catalog(),
                )

    @patch("cad_library_mitcad_reference.capture_runtime")
    def test_runtime_verify_compares_reference_and_catalog(self, capture):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            reference = "# exact reference\n"
            blob = git_blob_sha(reference)
            (out / "commands.md").write_text(reference, encoding="utf-8")
            (out / "commands.json").write_text(
                json.dumps(catalog()) + "\n", encoding="utf-8"
            )
            capture.return_value = (
                "mitcad-cli 0.70.0",
                reference,
                catalog(),
            )
            self.assertEqual(
                verify_runtime_snapshot(
                    executable="mitcad-cli",
                    version=VERSION,
                    snapshot=out,
                    reference_blob=blob,
                ),
                len(catalog()["commands"]),
            )


if __name__ == "__main__":
    unittest.main()
