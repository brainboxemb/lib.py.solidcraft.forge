import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from cad_library_builder_build123d import build


class AdapterTests(unittest.TestCase):
    def test_exports_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "model.py"
            source.write_text("model = 'shape'\n")
            output = root / "model.stl"
            def export(model, path):
                self.assertEqual(model, "shape")
                Path(path).write_bytes(b"stl")
            with patch.dict(sys.modules, {"build123d": SimpleNamespace(export_stl=export)}):
                build(source, output)
            self.assertEqual(output.read_bytes(), b"stl")

    def test_missing_model_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "model.py"
            source.write_text("x = 1\n")
            with patch.dict(sys.modules, {"build123d": SimpleNamespace(export_stl=lambda *a: None)}):
                with self.assertRaisesRegex(ValueError, "must expose model"):
                    build(source, root / "model.stl")
