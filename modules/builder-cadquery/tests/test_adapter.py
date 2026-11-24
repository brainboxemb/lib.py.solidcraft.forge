import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from cad_library_builder_cadquery import build


class AdapterTests(unittest.TestCase):
    def test_exports_model_from_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "model.py"
            source.write_text("model = 'shape'\n")
            output = root / "out" / "model.stl"
            def export(model, path):
                self.assertEqual(model, "shape")
                Path(path).write_bytes(b"stl")
            fake = SimpleNamespace(Assembly=type("Assembly", (), {}), exporters=SimpleNamespace(export=export))
            with patch.dict(sys.modules, {"cadquery": fake}):
                build(source, output)
            self.assertEqual(output.read_bytes(), b"stl")

    def test_missing_model_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "model.py"
            source.write_text("x = 1\n")
            with patch.dict(sys.modules, {"cadquery": SimpleNamespace()}):
                with self.assertRaisesRegex(ValueError, "must expose model"):
                    build(source, root / "model.stl")
