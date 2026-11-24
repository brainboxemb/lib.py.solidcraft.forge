from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from cad_library_builder_scpf import build


class SCPFBuilderTests(unittest.TestCase):
    def test_compiles_then_delegates_to_generic_solidcraft_builder(self):
        run_script = Mock(return_value={"commands":[{"command":"solid.box","params":{}}]})
        native = Mock()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=root/"model.py"
            source.write_text("model")
            output=root/"out/model.stl"
            modules={
                "scpf.runner": SimpleNamespace(run_script=run_script),
                "cad_library_builder_solidcraft": SimpleNamespace(build=native),
            }
            with patch.dict(sys.modules, modules):
                build(source, output)
            run_script.assert_called_once_with(source)
            native.assert_called_once()
            command_path=native.call_args.args[0]
            self.assertEqual(native.call_args.args[1], output)
            self.assertEqual(json.loads(command_path.read_text())["commands"][0]["command"], "solid.box")
