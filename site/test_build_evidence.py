#!/usr/bin/env python3
"""Tests for stable Pages durable build evidence loading."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from build_evidence import IMPLEMENTATIONS, load_stable_build_evidence


def write_json(path: Path, value) -> None:
    """Write one deterministic JSON fixture."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_bytes(path: Path, value: bytes = b"evidence") -> None:
    """Write one non-empty fixture artifact."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


class StableBuildEvidenceTests(unittest.TestCase):
    def make_item(
        self,
        root: Path,
        items: dict,
        source_path: str,
        *,
        item_id: str,
        source_commit: str,
        final_step: str,
    ) -> Path:
        """Create one generic durable item and manifest row."""

        items[source_path] = {
            "engine": "scons",
            "engine_schema": 1,
            "final_bundle_sha256": "a" * 64,
            "final_step": final_step,
            "final_target_spec_digest": "b" * 64,
            "item_id": item_id,
            "outputs": [],
            "source_commit": source_commit,
        }
        item_root = root / source_path
        write_json(
            item_root / ".cad-ci" / "item.json",
            {
                "schema": 2,
                "engine": "scons",
                "engine_schema": 1,
                "item": item_id,
                "final_step": final_step,
                "status": "pass",
            },
        )
        return item_root

    def make_preview(
        self,
        evidence_root: Path,
        *,
        renderer: str,
        source: str,
    ) -> None:
        """Create one presentation preview under an evidence root."""

        write_bytes(evidence_root / source)
        presentation = evidence_root / "presentation"
        write_bytes(presentation / "preview-iso.png", b"png")
        write_json(
            presentation / "preview.json",
            {
                "schema": 1,
                "kind": "presentation-preview",
                "renderer": renderer,
                "view": "iso",
                "image": "preview-iso.png",
                "source": source,
                "width": 720,
                "height": 540,
            },
        )

    def make_complete_tree(self, root: Path) -> None:
        """Create one complete example plus four accepted references."""

        items = {}
        slug = "simple-box"
        model_root = self.make_item(
            root,
            items,
            f"examples/{slug}",
            item_id=slug,
            source_commit="model-commit",
            final_step="model_verify",
        )
        write_bytes(model_root / "solidcraft.json", b"{}")
        model_verify = model_root / "model_verify"
        write_json(model_verify / "verification.json", {"status": "pass"})
        write_bytes(model_verify / "native" / "model.sc", b"solidcraft")
        write_bytes(model_verify / "native" / "model.step", b"step")
        write_json(model_verify / "native" / "results.json", {"status": "ok"})
        write_json(
            model_verify / "baseline" / "measurements.json",
            {
                "bodies": [
                    {
                        "bbox": {
                            "min": [-20, -15, 0],
                            "max": [20, 15, 10],
                        }
                    }
                ]
            },
        )
        self.make_preview(
            model_verify,
            renderer="solidcraft-snapshot",
            source="native/model.sc",
        )
        write_json(
            model_verify / "saved_designs" / "length_50" / "measurements.json",
            {"parameters": {"length": 50}},
        )

        for index, implementation in enumerate(IMPLEMENTATIONS):
            item_root = self.make_item(
                root,
                items,
                f"examples/{slug}/{implementation}",
                item_id=f"{slug}-{implementation}",
                source_commit=f"reference-commit-{index}",
                final_step="verify_reference",
            )
            result_root = (
                item_root / "references" / slug / implementation
            )
            write_bytes(result_root / "model.stl", b"solid stl")
            self.make_preview(
                result_root,
                renderer="forge-trimesh-pillow-v1",
                source="model.stl",
            )
            write_json(
                result_root / "verification.json",
                {
                    "implementation": implementation,
                    "status": "pass",
                    "geometry": {"bounds": {"pass": True}},
                    "presentation": {
                        "status": "pass",
                        "preview": "presentation/preview-iso.png",
                        "metadata": "presentation/preview.json",
                    },
                },
            )

        write_bytes(
            root
            / "ci"
            / "cad-verification-package"
            / "dist"
            / "brainboxemb_cad_verification_lib-0.14.0-py3-none-any.whl",
            b"wheel",
        )
        write_json(
            root
            / "ci"
            / "verification-diagrams"
            / "diagrams"
            / "provenance.json",
            {
                "schema": 1,
                "status": "pass",
                "cadcraft_version": "0.20.1",
            },
        )

        write_json(
            root / "build.json",
            {
                "schema": 1,
                "scope": "main",
                "source_commit": "manifest-commit",
                "items": items,
            },
        )
        write_bytes(
            root
            / "ci"
            / "verification-diagrams"
            / "diagrams"
            / "rendered"
            / "joint.svg",
            b"<svg/>",
        )

    def test_complete_tree_preserves_per_item_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_complete_tree(root)

            evidence = load_stable_build_evidence(
                root,
                "c" * 40,
                ("simple-box",),
            )

            self.assertEqual(evidence.build_commit, "c" * 40)
            self.assertIn("/" + ("c" * 40) + "/main/", evidence.raw_url(
                evidence.examples[0].preview_path
            ))
            self.assertEqual(
                evidence.manifest_source_commit,
                "manifest-commit",
            )
            self.assertEqual(len(evidence.examples), 1)
            example = evidence.examples[0]
            self.assertEqual(example.item.source_commit, "model-commit")
            self.assertEqual(example.item.status, "pass")
            self.assertEqual(example.preview["view"], "iso")
            self.assertEqual(
                [row.implementation for row in example.references],
                list(IMPLEMENTATIONS),
            )
            self.assertEqual(
                [row.item.source_commit for row in example.references],
                [
                    "reference-commit-0",
                    "reference-commit-1",
                    "reference-commit-2",
                    "reference-commit-3",
                ],
            )
            self.assertEqual(len(example.saved_designs), 1)
            self.assertEqual(example.saved_designs[0][0], "length_50")
            self.assertTrue(evidence.verification_wheel_path.is_file())
            self.assertEqual(evidence.diagram_provenance["status"], "pass")
            self.assertEqual(
                [path.name for path in evidence.diagram_paths],
                ["joint.svg"],
            )

    def test_reference_item_must_itself_be_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_complete_tree(root)
            item = (
                root
                / "examples"
                / "simple-box"
                / "cadquery"
                / ".cad-ci"
                / "item.json"
            )
            value = json.loads(item.read_text(encoding="utf-8"))
            value["status"] = "fail"
            write_json(item, value)

            with self.assertRaisesRegex(
                ValueError,
                "durable reference item is not pass",
            ):
                load_stable_build_evidence(
                    root,
                    "c" * 40,
                    ("simple-box",),
                )

    def test_moving_build_ref_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_complete_tree(root)

            with self.assertRaisesRegex(
                ValueError,
                "full immutable Git SHA",
            ):
                load_stable_build_evidence(
                    root,
                    "build",
                    ("simple-box",),
                )

    def test_missing_current_preview_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_complete_tree(root)
            (
                root
                / "examples"
                / "simple-box"
                / "model_verify"
                / "presentation"
                / "preview-iso.png"
            ).unlink()

            with self.assertRaisesRegex(
                ValueError,
                "preview image is missing or empty",
            ):
                load_stable_build_evidence(
                    root,
                    "c" * 40,
                    ("simple-box",),
                )

    def test_preview_source_may_not_escape_its_evidence_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_complete_tree(root)
            metadata = (
                root
                / "examples"
                / "simple-box"
                / "model_verify"
                / "presentation"
                / "preview.json"
            )
            value = json.loads(metadata.read_text(encoding="utf-8"))
            value["source"] = "../other-item/model.sc"
            write_json(metadata, value)

            with self.assertRaisesRegex(
                ValueError,
                "escapes its item root",
            ):
                load_stable_build_evidence(
                    root,
                    "c" * 40,
                    ("simple-box",),
                )


if __name__ == "__main__":
    unittest.main()
