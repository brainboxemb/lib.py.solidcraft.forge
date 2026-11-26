from pathlib import Path
import json
from types import ModuleType
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from cad_library_builder_scpf_mitcad import build


class SCPFMitcadBuilderTests(unittest.TestCase):
    def _modules(self, document):
        run_script = Mock(return_value=document)
        runner = ModuleType("scpf.runner")
        runner.run_script = run_script

        validate_document = Mock()
        run_document = Mock()
        headless = ModuleType("scpf.backends.mitcad_headless")
        headless.validate_document = validate_document
        headless.run_document = run_document

        backends = ModuleType("scpf.backends")
        backends.mitcad_headless = headless
        scpf = ModuleType("scpf")
        scpf.runner = runner
        scpf.backends = backends
        return scpf, runner, backends, headless, run_script, validate_document, run_document

    def test_builds_native_document_and_stl_through_mitcad_backend(self):
        document = {
            "format": "scpf-mitcad",
            "version": 1,
            "backend": "mitcad",
            "commands": [{"cmd": "add_feature"}],
        }
        modules = self._modules(document)
        scpf, runner, backends, headless, run_script, validate_document, run_document = modules

        def execute(value, *, save, export, executable, work_dir):
            self.assertIs(value, document)
            self.assertEqual(executable, "mitcad-cli")
            self.assertEqual(work_dir.name, "mitcad-work")
            save.write_bytes(b"mitcad")
            export.write_bytes(b"stl")
            return {"completed": 1}

        run_document.side_effect = execute

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "model.py"
            source.write_text("model", encoding="utf-8")
            output = root / "out/model.stl"
            with patch.dict(
                sys.modules,
                {
                    "scpf": scpf,
                    "scpf.runner": runner,
                    "scpf.backends": backends,
                    "scpf.backends.mitcad_headless": headless,
                },
            ), patch.dict("os.environ", {}, clear=True):
                build(source, output)

            self.assertEqual((output.parent / "model.mitcad").read_bytes(), b"mitcad")
            self.assertEqual(
                json.loads((output.parent / "mitcad.json").read_text()),
                document,
            )
            self.assertEqual(output.read_bytes(), b"stl")

        run_script.assert_called_once_with(source, backend="mitcad")
        validate_document.assert_called_once_with(document)
        self.assertEqual(run_document.call_count, 1)

    def test_runtime_may_supply_explicit_cli_path(self):
        document = {
            "format": "scpf-mitcad",
            "version": 1,
            "backend": "mitcad",
            "commands": [{"cmd": "add_feature"}],
        }
        modules = self._modules(document)
        scpf, runner, backends, headless, _, _, run_document = modules

        def execute(value, *, save, export, executable, work_dir):
            self.assertEqual(executable, "/opt/mitcad/bin/mitcad-cli")
            save.write_bytes(b"mitcad")
            export.write_bytes(b"stl")

        run_document.side_effect = execute

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "model.py"
            source.write_text("model", encoding="utf-8")
            output = root / "out/model.stl"
            with patch.dict(
                sys.modules,
                {
                    "scpf": scpf,
                    "scpf.runner": runner,
                    "scpf.backends": backends,
                    "scpf.backends.mitcad_headless": headless,
                },
            ), patch.dict(
                "os.environ",
                {"CAD_LIBRARY_MITCAD_EXECUTABLE": "/opt/mitcad/bin/mitcad-cli"},
                clear=True,
            ):
                build(source, output)

    def test_missing_native_artifact_fails_closed(self):
        document = {
            "format": "scpf-mitcad",
            "version": 1,
            "backend": "mitcad",
            "commands": [{"cmd": "add_feature"}],
        }
        modules = self._modules(document)
        scpf, runner, backends, headless, _, _, run_document = modules

        def execute(value, *, save, export, executable, work_dir):
            export.write_bytes(b"stl")

        run_document.side_effect = execute

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "model.py"
            source.write_text("model", encoding="utf-8")
            output = root / "out/model.stl"
            with patch.dict(
                sys.modules,
                {
                    "scpf": scpf,
                    "scpf.runner": runner,
                    "scpf.backends": backends,
                    "scpf.backends.mitcad_headless": headless,
                },
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Mitcad build produced no artifact: model.mitcad",
                ):
                    build(source, output)


if __name__ == "__main__":
    unittest.main()
