from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock
from cad_library_builder_pybosl2 import build


class AdapterTests(unittest.TestCase):
    def test_delegates_to_shared_exporter(self):
        export = Mock()
        with patch.dict("sys.modules", {"cad_library_builder_pythonscad": SimpleNamespace(build=export)}):
            build(Path("model.py"), Path("model.stl"))
        export.assert_called_once_with(Path("model.py"), Path("model.stl"))
