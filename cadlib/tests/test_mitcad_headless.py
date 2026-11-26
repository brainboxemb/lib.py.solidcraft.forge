"""Transport contracts for experimental Mitcad headless execution."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scpf.backends.mitcad_headless import (
    MitcadHeadlessError,
    run_document,
    validate_document,
)


def document():
    return {
        "format": "scpf-mitcad",
        "version": 1,
        "backend": "mitcad",
        "commands": [
            {
                "cmd": "add_feature",
                "name": "Box",
                "def": {
                    "type": "box",
                    "plane": "xy",
                    "corner": [0, 0],
                    "length": 40,
                    "width": 30,
                    "height": 10,
                    "symmetric": False,
                    "operation": "new_body",
                    "participants": [],
                },
            }
        ],
    }


class FakeSession:
    instances = []

    def __init__(self, executable, workspace):
        self.executable = executable
        self.workspace = Path(workspace)
        self.calls = []
        self.__class__.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def tool(self, name, arguments):
        self.calls.append((name, arguments))
        if name == "document_create":
            return {"document": "D1", "applied": True}
        if name == "model_command":
            return {
                "document": "D1",
                "applied": True,
                "failed_features": [],
            }
        if name == "model_query":
            return {
                "document": "D1",
                "result": [
                    {
                        "uid": "F1.b0",
                        "name": "Body1",
                        "kind": "solid",
                        "volume": 12000,
                        "bbox": {
                            "min": [0, 0, 0],
                            "max": [40, 30, 10],
                        },
                    }
                ],
            }
        if name == "document_save":
            (self.workspace / arguments["path"]).write_text(
                "native mitcad", encoding="utf-8"
            )
            return {"document": "D1", "path": arguments["path"]}
        if name == "model_export":
            (self.workspace / arguments["path"]).write_bytes(b"solid stl")
            return {"document": "D1", "path": arguments["path"]}
        if name == "document_close":
            return {"document": "D1", "closed": True}
        raise AssertionError(name)


def replay_document():
    value = document()
    value["replay"] = [
        {
            "bind_single_body": "body",
            "commands": [
                {
                    "cmd": "add_feature",
                    "def": {
                        "type": "chamfer",
                        "body": {"$mitcad_bind": "body"},
                        "faces": {
                            "surface": "plane",
                            "normal": [0, 0, 1],
                        },
                        "size": {
                            "type": "equal_distance",
                            "distance": 2,
                        },
                    },
                }
            ],
        }
    ]
    return value


class MitcadHeadlessTests(unittest.TestCase):
    def setUp(self):
        FakeSession.instances.clear()

    def test_document_contract_rejects_non_mitcad_input(self):
        with self.assertRaisesRegex(
            MitcadHeadlessError, "not an scpf-mitcad"
        ):
            validate_document({"commands": [{"cmd": "add_feature"}]})

    @patch("scpf.backends.mitcad_headless._Session", FakeSession)
    def test_executes_native_command_array_queries_and_writes_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save = root / "out/design.mitcad"
            export = root / "out/design.stl"
            workspace = root / "workspace"

            result = run_document(
                document(),
                save=save,
                export=export,
                executable="/opt/mitcad/mitcad-cli",
                work_dir=workspace,
            )

            self.assertEqual(result["completed"], 1)
            self.assertEqual(result["bodies"][0]["volume"], 12000)
            self.assertEqual(save.read_text(), "native mitcad")
            self.assertEqual(export.read_bytes(), b"solid stl")

            session = FakeSession.instances[-1]
            self.assertEqual(
                [name for name, _ in session.calls],
                [
                    "document_create",
                    "model_command",
                    "model_query",
                    "document_save",
                    "model_export",
                    "document_close",
                ],
            )
            command = session.calls[1][1]
            self.assertEqual(command["document"], "D1")
            self.assertEqual(command["command"], document()["commands"])
            self.assertEqual(command["timeline"], "none")
            query = session.calls[2][1]["query"]
            self.assertEqual(
                query,
                {"query": "bodies", "properties": True},
            )

    @patch("scpf.backends.mitcad_headless._Session", FakeSession)
    def test_replay_binds_single_native_body_without_predicting_uid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = run_document(
                replay_document(),
                save=root / "out.mitcad",
                work_dir=root / "workspace",
            )
            self.assertEqual(result["completed"], 2)
            self.assertEqual(result["bindings"], {"body": "F1.b0"})
            session = FakeSession.instances[-1]
            commands = [
                args["command"]
                for name, args in session.calls
                if name == "model_command"
            ]
            self.assertEqual(len(commands), 2)
            self.assertEqual(commands[1][0]["def"]["body"], "F1.b0")

    @patch("scpf.backends.mitcad_headless._Session", FakeSession)
    def test_unsupported_export_suffix_fails_before_export_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(
                MitcadHeadlessError, "unsupported Mitcad export suffix"
            ):
                run_document(
                    document(),
                    save=root / "out.mitcad",
                    export=root / "out.xyzzy",
                    work_dir=root / "workspace",
                )


if __name__ == "__main__":
    unittest.main()
