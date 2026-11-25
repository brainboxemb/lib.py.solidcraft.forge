import json
from pathlib import Path
from types import ModuleType
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from cad_library_builder_scpf import build


class SCPFBuilderTests(unittest.TestCase):
    def _scpf_modules(self, document, *, replay):
        run_script = Mock(return_value=document)
        runner = ModuleType("scpf.runner")
        runner.run_script = run_script

        replay_module = ModuleType("scpf.replay")
        replay_module.is_replay_document = Mock(return_value=replay)

        scpf = ModuleType("scpf")
        scpf.runner = runner
        scpf.replay = replay_module
        return scpf, runner, replay_module, run_script

    def test_plain_document_delegates_to_generic_solidcraft_builder(self):
        document = {
            "commands": [
                {"command": "solid.box", "params": {}}
            ]
        }
        scpf, runner, replay, run_script = self._scpf_modules(
            document,
            replay=False,
        )
        captured = {}

        def native(commands, output):
            captured["document"] = json.loads(
                commands.read_text()
            )
            captured["output"] = output

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
                    "scpf.replay": replay,
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

    def test_replay_document_uses_scpf_headless_executor_and_retains_evidence(self):
        document = {
            "format": "scpf-replay",
            "version": 2,
            "commands": [
                {
                    "command": "component.create",
                    "params": {"name": "Part"},
                    "bind": {"$part": "occurrence"},
                },
                {
                    "command": "occurrence.move",
                    "params": {
                        "occurrence": "$part",
                        "translate": [10, 0, 0],
                    },
                },
            ],
        }
        scpf, runner, replay, run_script = self._scpf_modules(
            document,
            replay=True,
        )
        headless = ModuleType("scpf.headless")
        calls = {}

        def run_document(
            value,
            *,
            save,
            export,
            results_out,
            replay_log_out,
            work_dir,
        ):
            calls["document"] = value
            calls["work_dir"] = work_dir
            save.parent.mkdir(parents=True, exist_ok=True)
            save.write_bytes(b"sc")
            export.write_bytes(b"stl")
            results_out.write_text("[]")
            replay_log_out.write_text('{"completed": 2}')
            work_dir.mkdir(parents=True, exist_ok=True)
            return {
                "variables": {
                    "$drawing_1": "D1",
                    "$drawing_1_sheet": "S1",
                    "$drawing_1_orientation": "landscape",
                }
            }

        headless.run_document = run_document
        scpf.headless = headless

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "model.py"
            source.write_text("model")
            output = root / "out/model.stl"

            def command(args, **kwargs):
                if args[1] == "snapshot":
                    Path(args[args.index("--out") + 1]).write_bytes(b"png")
                return Mock(returncode=0)

            with patch.dict(
                sys.modules,
                {
                    "scpf": scpf,
                    "scpf.runner": runner,
                    "scpf.replay": replay,
                    "scpf.headless": headless,
                },
            ), patch(
                "cad_library_builder_scpf.subprocess.run",
                side_effect=command,
            ):
                build(source, output)

            self.assertEqual(calls["document"], document)
            self.assertEqual(
                json.loads(
                    (output.parent / "solidcraft.json").read_text()
                ),
                document,
            )
            self.assertEqual(
                (output.parent / "model.sc").read_bytes(),
                b"sc",
            )
            self.assertEqual(
                (output.parent / "model.png").read_bytes(),
                b"png",
            )
            self.assertTrue(
                (output.parent / "replay-log.json").is_file()
            )
            self.assertTrue(
                (output.parent / "replay-results.json").is_file()
            )
            self.assertEqual(
                calls["work_dir"],
                output.parent / "replay_work",
            )


    def test_replay_document_exports_declared_drawing_pdf_and_preview(self):
        document = {
            "format": "scpf-replay",
            "version": 2,
            "commands": [
                {
                    "command": "drawing.create",
                    "params": {"name": "Part drawing"},
                    "bind": {"$drawing_1": "id"},
                },
            ],
            "artifacts": {
                "drawings": [
                    {
                        "name": "Part drawing",
                        "drawing": "$drawing_1",
                        "sheet": "$drawing_1_sheet",
                        "orientation": "$drawing_1_orientation",
                        "pdf": "drawings/Part-drawing.pdf",
                        "png": "drawings/Part-drawing.png",
                        "inspect": "drawings/Part-drawing.json",
                        "expected": {
                            "orientation": "landscape",
                            "view_count": 4,
                            "dimension_count": 0,
                            "note_count": 0,
                            "properties": {},
                            "title_block": {},
                            "view_styles": {},
                        },
                    }
                ]
            },
        }
        scpf, runner, replay, _ = self._scpf_modules(document, replay=True)
        headless = ModuleType("scpf.headless")

        def run_document(
            value,
            *,
            save,
            export,
            results_out,
            replay_log_out,
            work_dir,
        ):
            save.parent.mkdir(parents=True, exist_ok=True)
            save.write_bytes(b"sc")
            export.write_bytes(b"stl")
            results_out.write_text(json.dumps([
                {
                    "name": "Part drawing",
                    "properties": {},
                    "revisions": {"rows": []},
                    "sheets": [
                        {
                            "orientation": "landscape",
                            "views": [
                                {"dimensions": []},
                                {"dimensions": []},
                                {"dimensions": []},
                                {"dimensions": []},
                            ],
                            "notes": [],
                            "title_block_overrides": {},
                            "title_block_cells": [],
                        }
                    ],
                }
            ]))
            replay_log_out.write_text("{}")
            work_dir.mkdir(parents=True, exist_ok=True)
            return {
                "variables": {
                    "$drawing_1": "D1",
                    "$drawing_1_sheet": "S1",
                    "$drawing_1_orientation": "landscape",
                }
            }

        headless.run_document = run_document
        scpf.headless = headless

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "model.py"
            source.write_text("model")
            output = root / "out/model.stl"
            calls = []

            def command(args, **kwargs):
                calls.append(args)
                if args[1] == "run":
                    script = json.loads(Path(args[2]).read_text())
                    export_cmds = [
                        row for row in script["commands"]
                        if row["command"] == "drawing.export"
                    ]
                    for export_cmd in export_cmds:
                        target = Path(export_cmd["params"]["path"])
                        if export_cmd["params"]["format"] == "pdf":
                            target.write_bytes(b"%PDF-test")
                        else:
                            target.write_bytes(b"\x89PNG\r\n\x1a\npreview")
                elif args[1] == "snapshot":
                    Path(args[args.index("--out") + 1]).write_bytes(b"png")
                return Mock(returncode=0)

            with patch.dict(
                sys.modules,
                {
                    "scpf": scpf,
                    "scpf.runner": runner,
                    "scpf.replay": replay,
                    "scpf.headless": headless,
                },
            ), patch(
                "cad_library_builder_scpf.subprocess.run",
                side_effect=command,
            ):
                build(source, output)

            pdf = output.parent / "drawings/Part-drawing.pdf"
            png = output.parent / "drawings/Part-drawing.png"
            inspect = output.parent / "drawings/Part-drawing.json"
            self.assertEqual(pdf.read_bytes(), b"%PDF-test")
            self.assertEqual(
                png.read_bytes()[:8],
                b"\x89PNG\r\n\x1a\n",
            )
            self.assertEqual(
                json.loads(inspect.read_text())["name"],
                "Part drawing",
            )
            export_run = next(
                args for args in calls
                if args[1] == "run" and "drawing-export" in args[2]
            )
            self.assertIn("--in", export_run)
            self.assertIn(str(output.parent / "model.sc"), export_run)
            export_script = json.loads(Path(export_run[2]).read_text())
            png_export = next(
                row for row in export_script["commands"]
                if row["command"] == "drawing.export"
                and row["params"]["format"] == "png"
            )
            self.assertEqual(png_export["params"]["sheet"], "S1")
            self.assertEqual(png_export["params"]["dpi"], 144)

    def test_replay_document_rejects_portrait_drawing_artifact(self):
        document = {
            "format": "scpf-replay",
            "version": 2,
            "commands": [],
            "artifacts": {
                "drawings": [
                    {
                        "name": "Part drawing",
                        "drawing": "$drawing_1",
                        "sheet": "$drawing_1_sheet",
                        "orientation": "$drawing_1_orientation",
                        "pdf": "drawings/Part-drawing.pdf",
                        "png": "drawings/Part-drawing.png",
                        "inspect": "drawings/Part-drawing.json",
                        "expected": {
                            "orientation": "landscape",
                            "view_count": 4,
                            "dimension_count": 0,
                            "note_count": 0,
                            "properties": {},
                            "title_block": {},
                            "view_styles": {},
                        },
                    }
                ]
            },
        }
        scpf, runner, replay, _ = self._scpf_modules(document, replay=True)
        headless = ModuleType("scpf.headless")

        def run_document(
            value,
            *,
            save,
            export,
            results_out,
            replay_log_out,
            work_dir,
        ):
            save.parent.mkdir(parents=True, exist_ok=True)
            save.write_bytes(b"sc")
            export.write_bytes(b"stl")
            results_out.write_text("[]")
            replay_log_out.write_text("{}")
            work_dir.mkdir(parents=True, exist_ok=True)
            return {
                "variables": {
                    "$drawing_1": "D1",
                    "$drawing_1_sheet": "S1",
                    "$drawing_1_orientation": "portrait",
                }
            }

        headless.run_document = run_document
        scpf.headless = headless

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
                    "scpf.replay": replay,
                    "scpf.headless": headless,
                },
            ), patch(
                "cad_library_builder_scpf.subprocess.run",
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "drawing sheet is not landscape",
                ):
                    build(source, output)

if __name__ == "__main__":
    unittest.main()
