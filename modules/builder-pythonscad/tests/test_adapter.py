from pathlib import Path
import tempfile
import unittest
from cad_library_builder_pythonscad import build


class AdapterTests(unittest.TestCase):
    def test_exports_source_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root/"model.py"
            source.write_text("from pathlib import Path\nclass Model:\n    def export(self, target):\n        Path(target).write_bytes(b'stl')\nmodel = Model()\n")
            output = root/"out"/"model.stl"
            build(source, output)
            self.assertEqual(output.read_bytes(), b"stl")

    def test_missing_export_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root/"model.py"
            source.write_text("model = None\n")
            with self.assertRaisesRegex(ValueError, "must expose model"):
                build(source, root/"model.stl")
