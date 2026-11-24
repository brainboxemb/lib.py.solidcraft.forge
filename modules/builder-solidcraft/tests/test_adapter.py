from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
from cad_library_builder_solidcraft import build


class SolidCraftAdapterTests(unittest.TestCase):
    def test_builds_native_stl_preview_and_command_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root/"commands.json"
            source.write_text('{"commands":[]}')
            output = root/"out/model.stl"
            def run(command, **kwargs):
                if command[1:] == ["--version"]:
                    return SimpleNamespace(stdout="SolidCraft 0.48.1", stderr="")
                if "--save" in command:
                    Path(command[command.index("--save")+1]).write_bytes(b"sc")
                if command[:2] == ["solidcraft-cli", "run"] and "--out" in command:
                    Path(command[command.index("--out")+1]).write_bytes(b"stl")
                if command[:2] == ["solidcraft-cli", "snapshot"]:
                    Path(command[command.index("--out")+1]).write_bytes(b"png")
                return SimpleNamespace(stdout="", stderr="")
            with patch.dict("os.environ", {"CAD_LIBRARY_RUNTIME_VERSION":"0.48.1"}), patch("cad_library_builder_solidcraft.subprocess.run", side_effect=run):
                build(source, output)
            self.assertEqual((output.parent/"model.sc").read_bytes(), b"sc")
            self.assertEqual((output.parent/"model.png").read_bytes(), b"png")
            self.assertEqual((output.parent/"solidcraft.json").read_text(), source.read_text())
