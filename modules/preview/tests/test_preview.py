"""Runtime tests for repository-local verified-STL presentation previews."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "verification" / "src"))

from cad_library_preview import render_reference_preview


class ReferencePreviewTests(unittest.TestCase):
    def test_box_preview_is_deterministic_and_provenanced(self):
        import trimesh
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stl = root / "model.stl"
            mesh = trimesh.creation.box(extents=(40.0, 30.0, 10.0))
            mesh.apply_translation((0.0, 0.0, 5.0))
            mesh.export(stl)

            first_dir = root / "first"
            second_dir = root / "second"
            first = render_reference_preview(
                stl,
                first_dir,
                source_reference="model.stl",
            )
            second = render_reference_preview(
                stl,
                second_dir,
                source_reference="model.stl",
            )

            self.assertEqual(first, second)
            self.assertEqual(first["schema"], 1)
            self.assertEqual(first["view"], "iso")
            self.assertEqual(first["source"], "model.stl")
            self.assertEqual(first["width"], 720)
            self.assertEqual(first["height"], 540)
            self.assertEqual(first["bounds"]["min"], [-20.0, -15.0, 0.0])
            self.assertEqual(first["bounds"]["max"], [20.0, 15.0, 10.0])

            first_png = first_dir / "model.png"
            second_png = second_dir / "model.png"
            self.assertEqual(first_png.read_bytes(), second_png.read_bytes())
            with Image.open(first_png) as image:
                self.assertEqual(image.size, (720, 540))
                self.assertEqual(image.mode, "RGB")
                self.assertGreater(len(set(image.getdata())), 2)

            stored = json.loads(
                (first_dir / "preview.json").read_text(encoding="utf-8")
            )
            self.assertEqual(stored, first)

    def test_renderer_stays_headless_and_consumer_owned(self):
        source = (
            ROOT / "src" / "cad_library_preview" / "__init__.py"
        ).read_text(encoding="utf-8").lower()
        for forbidden in (
            "pyglet",
            "vtk",
            "matplotlib",
            "scene.save_image",
            "solidcraft",
            "cadquery",
            "build123d",
            "pythonscad",
            "pybosl2",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
