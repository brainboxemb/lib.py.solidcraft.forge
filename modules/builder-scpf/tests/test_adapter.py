import json
from pathlib import Path
from types import ModuleType
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from cad_library_builder_scpf import build


class SCPFBuilderTests(unittest.TestCase):
    def test_compiles_then_delegates_to_generic_solidcraft_builder(self):
        run_script = Mock(
            return_value={
                "commands": [
                    {"command": "solid.box", "params": {}}
                ]
            }
        )
        captured = {}

        def native(commands, output):
            captured["document"] = json.loads(
                commands.read_text()
            )
            captured["output"] = output

        scpf = ModuleType("scpf")
        runner = ModuleType("scpf.runner")
        runner.run_script = run_script
        scpf.runner = runner

        solidcraft = ModuleType(
            "cad_library_builder_solidcraft"
        )
        solidcraft.build = native

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "model.py"
            source.write_text("model")
            output = root / "out/model.stl"
            with patch.dict(
                sys.modules,
                {
                    "scpf": scpf,
                    "scpf.runner": runner,
                    "cad_library_builder_solidcraft": solidcraft,
                },
            ):
                build(source, output)

        run_script.assert_called_once_with(source)
        self.assertEqual(captured["output"], output)
        self.assertEqual(
            captured["document"]["commands"][0]["command"],
            "solid.box",
        )


if __name__ == "__main__":
    unittest.main()
