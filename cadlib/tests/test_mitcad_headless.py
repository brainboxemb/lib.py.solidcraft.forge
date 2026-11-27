"""Transport contracts for experimental Mitcad headless execution."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scpf.backends.mitcad_headless import (
    MitcadHeadlessError,
    run_document,
    run_saved_configuration,
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
        if name == "document_open":
            path = self.workspace / arguments["path"]
            if not path.is_file():
                raise AssertionError(f"missing saved design: {path}")
            return {"document": "D1"}
        if name == "model_command":
            return {
                "document": "D1",
                "applied": True,
                "failed_features": [],
            }
        if name == "model_query":
            query = arguments["query"]
            if query["query"] == "bodies":
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
            if query["query"] == "faces":
                normal = tuple(query.get("normal", ()))
                face_name = {
                    (0, 0, 1): "F1:top",
                    (0, -1, 0): "F1:side0",
                    (0, 1, 0): "F1:side2",
                }.get(normal)
                if face_name is None:
                    raise AssertionError(query)
                return {
                    "document": "D1",
                    "result": {
                        "total": 1,
                        "offset": 0,
                        "faces": [
                            {
                                "index": 1,
                                "names": [face_name],
                                "surface": "plane",
                                "area": 1200,
                            }
                        ],
                    },
                }
            if query["query"] == "edges":
                return {
                    "document": "D1",
                    "result": [
                        {"name": "E{F1:bottom|F1:side0}", "curve": "line", "length": 40},
                        {"name": "E{F1:bottom|F1:side1}", "curve": "line", "length": 30},
                        {"name": "E{F1:bottom|F1:side2}", "curve": "line", "length": 40},
                        {"name": "E{F1:bottom|F1:side3}", "curve": "line", "length": 30},
                        {"name": "E{F1:side0|F1:top}", "curve": "line", "length": 40},
                        {"name": "E{F1:side1|F1:top}", "curve": "line", "length": 30},
                        {"name": "E{F1:side2|F1:top}", "curve": "line", "length": 40},
                        {"name": "E{F1:side3|F1:top}", "curve": "line", "length": 30},
                        {"name": "E{F1:side0|F1:side1}", "curve": "line", "length": 10},
                        {"name": "E{F1:side1|F1:side2}", "curve": "line", "length": 10},
                        {"name": "E{F1:side2|F1:side3}", "curve": "line", "length": 10},
                        {"name": "E{F1:side3|F1:side0}", "curve": "line", "length": 10},
                    ],
                }
            raise AssertionError(query)
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


def cylinder_cut_document():
    value = document()
    value["commands"].append({
        "cmd": "add_feature",
        "name": "Bore",
        "def": {
            "type": "cylinder",
            "plane": "xy",
            "center": [0, 0],
            "diameter": 10,
            "height": 30,
            "symmetric": True,
            "operation": "cut",
            "participants": [],
        },
    })
    return value


def replay_document():
    value = document()
    value["replay"] = [
        {
            "bind_single_body": "body",
            "bind_face_boundary_edges": {
                "name": "edges",
                "body": "body",
                "face": {
                    "surface": "plane",
                    "normal": [0, 0, 1],
                    "normal_tolerance": 1e-6,
                },
            },
            "commands": [
                {
                    "cmd": "add_feature",
                    "def": {
                        "type": "chamfer",
                        "body": {"$mitcad_bind": "body"},
                        "edges": {"$mitcad_bind": "edges"},
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


def asymmetric_replay_document():
    value = document()
    value["replay"] = [
        {
            "bind_single_body": "body",
            "bind_face_boundary_edges": {
                "name": "edges",
                "body": "body",
                "face_name": "reference_face",
                "face": {
                    "surface": "plane",
                    "normal": [0, 0, 1],
                    "normal_tolerance": 1e-6,
                },
            },
            "commands": [
                {
                    "cmd": "add_feature",
                    "def": {
                        "type": "chamfer",
                        "body": {"$mitcad_bind": "body"},
                        "sets": [
                            {
                                "edges": {"$mitcad_bind": "edges"},
                                "size": {
                                    "type": "two_distances",
                                    "distance1": 0.18,
                                    "distance2": 0.65,
                                },
                                "reference_face": {
                                    "$mitcad_bind": "reference_face"
                                },
                            }
                        ],
                    },
                }
            ],
        }
    ]
    return value


def multi_face_replay_document():
    value = document()
    value["replay"] = [
        {
            "bind_single_body": "body",
            "bind_face_boundary_edges": {
                "name": "edges",
                "body": "body",
                "faces": [
                    {
                        "surface": "plane",
                        "normal": [0, -1, 0],
                        "normal_tolerance": 1e-6,
                    },
                    {
                        "surface": "plane",
                        "normal": [0, 1, 0],
                        "normal_tolerance": 1e-6,
                    },
                ],
            },
            "commands": [
                {
                    "cmd": "add_feature",
                    "def": {
                        "type": "chamfer",
                        "body": {"$mitcad_bind": "body"},
                        "edges": {"$mitcad_bind": "edges"},
                        "size": {
                            "type": "equal_distance",
                            "distance": 1.5,
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
    def test_reopens_saved_design_and_applies_configuration_without_forge(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            saved = root / "configured.mitcad"
            saved.write_text("original native design", encoding="utf-8")
            export = root / "suppressed.stl"
            workspace = root / "reopen-workspace"

            result = run_saved_configuration(
                saved,
                "Suppressed",
                save=saved,
                export=export,
                executable="/opt/mitcad/mitcad-cli",
                work_dir=workspace,
            )

            self.assertEqual(result["completed"], 1)
            self.assertEqual(result["configuration"], "Suppressed")
            self.assertEqual(result["bodies"][0]["volume"], 12000)
            self.assertEqual(saved.read_text(), "native mitcad")
            self.assertEqual(export.read_bytes(), b"solid stl")

            session = FakeSession.instances[-1]
            self.assertEqual(
                [name for name, _ in session.calls],
                [
                    "document_open",
                    "model_command",
                    "model_query",
                    "document_save",
                    "model_export",
                    "document_close",
                ],
            )
            self.assertEqual(
                session.calls[1][1]["command"],
                [{"cmd": "apply_configuration", "name": "Suppressed"}],
            )
            self.assertEqual(
                session.calls[1][1]["timeline"],
                "none",
            )

    @patch("scpf.backends.mitcad_headless._Session", FakeSession)
    def test_native_cylinder_cut_runs_as_one_command_array_without_replay_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = run_document(
                cylinder_cut_document(),
                save=root / "out.mitcad",
                work_dir=root / "workspace",
            )
            self.assertEqual(result["completed"], 2)
            session = FakeSession.instances[-1]
            model_commands = [
                args["command"]
                for name, args in session.calls
                if name == "model_command"
            ]
            self.assertEqual(model_commands, [cylinder_cut_document()["commands"]])
            self.assertEqual(
                model_commands[0][-1]["def"]["operation"],
                "cut",
            )
            self.assertEqual(
                model_commands[0][-1]["def"]["participants"],
                [],
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
            self.assertEqual(
                result["bindings"],
                {
                    "body": "F1.b0",
                    "edges": [
                        "E{F1:side0|F1:top}",
                        "E{F1:side1|F1:top}",
                        "E{F1:side2|F1:top}",
                        "E{F1:side3|F1:top}",
                    ],
                },
            )
            session = FakeSession.instances[-1]
            commands = [
                args["command"]
                for name, args in session.calls
                if name == "model_command"
            ]
            self.assertEqual(len(commands), 2)
            self.assertEqual(commands[1][0]["def"]["body"], "F1.b0")
            self.assertEqual(
                commands[1][0]["def"]["edges"],
                result["bindings"]["edges"],
            )

    @patch("scpf.backends.mitcad_headless._Session", FakeSession)
    def test_replay_binds_selected_native_face_for_asymmetric_chamfer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = run_document(
                asymmetric_replay_document(),
                save=root / "out.mitcad",
                work_dir=root / "workspace",
            )

            self.assertEqual(result["bindings"]["reference_face"], "F1:top")
            self.assertEqual(
                result["bindings"]["edges"],
                [
                    "E{F1:side0|F1:top}",
                    "E{F1:side1|F1:top}",
                    "E{F1:side2|F1:top}",
                    "E{F1:side3|F1:top}",
                ],
            )
            session = FakeSession.instances[-1]
            commands = [
                args["command"]
                for name, args in session.calls
                if name == "model_command"
            ]
            chamfer_set = commands[1][0]["def"]["sets"][0]
            self.assertEqual(chamfer_set["reference_face"], "F1:top")
            self.assertEqual(
                chamfer_set["edges"],
                result["bindings"]["edges"],
            )
            self.assertEqual(
                chamfer_set["size"],
                {
                    "type": "two_distances",
                    "distance1": 0.18,
                    "distance2": 0.65,
                },
            )

    @patch("scpf.backends.mitcad_headless._Session", FakeSession)
    def test_replay_combines_multiple_face_boundaries_for_one_feature(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = run_document(
                multi_face_replay_document(),
                save=root / "out.mitcad",
                work_dir=root / "workspace",
            )

            self.assertEqual(
                result["bindings"]["edges"],
                [
                    "E{F1:bottom|F1:side0}",
                    "E{F1:side0|F1:top}",
                    "E{F1:side0|F1:side1}",
                    "E{F1:side3|F1:side0}",
                    "E{F1:bottom|F1:side2}",
                    "E{F1:side2|F1:top}",
                    "E{F1:side1|F1:side2}",
                    "E{F1:side2|F1:side3}",
                ],
            )
            session = FakeSession.instances[-1]
            commands = [
                args["command"]
                for name, args in session.calls
                if name == "model_command"
            ]
            self.assertEqual(len(commands), 2)
            self.assertEqual(
                commands[1][0]["def"]["edges"],
                result["bindings"]["edges"],
            )
            face_queries = [
                args["query"]["normal"]
                for name, args in session.calls
                if name == "model_query"
                and args["query"]["query"] == "faces"
            ]
            self.assertEqual(face_queries, [[0, -1, 0], [0, 1, 0]])

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
