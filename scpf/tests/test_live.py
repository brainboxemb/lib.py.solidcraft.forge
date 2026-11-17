"""Protocol tests with a local fake SolidCraft control channel.

No real GUI or SolidCraft installation is needed in CI. The server checks
the exact wire request; native GUI execution remains a separate test.
"""
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import unittest
from unittest.mock import patch

from scpf.live import LiveError, new_design, send_commands, send_document
from scpf.replay import apply_bindings, replay_document
from scpf.__main__ import read_command_file, main
from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]


class FakeSolidCraft:
    def __init__(self, reply):
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.bind(("127.0.0.1", 0))
        replies = reply if isinstance(reply, list) else [reply]
        self.listener.listen(len(replies))
        self.port = self.listener.getsockname()[1]
        self.replies = replies
        self.requests = []
        self.request = None
        self.thread = threading.Thread(target=self.serve, daemon=True)
        self.thread.start()

    def serve(self):
        try:
            with self.listener:
                for reply in self.replies:
                    conn, _ = self.listener.accept()
                    with conn:
                        with conn.makefile("rb") as stream:
                            self.request = json.loads(stream.readline())
                            self.requests.append(self.request)
                        conn.sendall((json.dumps(reply) + "\n").encode("utf-8"))
        except OSError:
            pass

    def join(self):
        self.thread.join(timeout=3)
        if self.thread.is_alive():
            self.listener.close()
            raise AssertionError("fake server did not receive a request")


class LiveProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def configure(self, server):
        (self.directory / "current.port").write_text(str(server.port))
        (self.directory / f"{server.port}.token").write_text("abcdeffedcba")

    def test_live_plate_is_single_strict_atomic_batch(self):
        document = run_script(ROOT / "examples/plate/scpf/model.py")
        commands = document["commands"]
        server = FakeSolidCraft({
            "id": 1, "ok": True,
            "result": {"completed": len(commands), "results": [{} for _ in commands],
                       "undone": 0},
        })
        self.configure(server)
        result = send_commands(commands, directory=self.directory)
        server.join()
        self.assertEqual(result["completed"], len(commands))
        self.assertEqual(server.request["method"], "engine.batch")
        self.assertEqual(server.request["token"], "abcdeffedcba")
        self.assertEqual(server.request["params"]["commands"], commands)
        self.assertEqual(server.request["params"]["rollback"], True)
        self.assertEqual(server.request["params"]["param_check"], "strict")

    def test_replay_variables_bind_real_occurrence_ids(self):
        document = replay_document([
            {
                "command": "component.create",
                "params": {
                    "name": "Board",
                    "grounded": False,
                },
                "bind": {
                    "$board_1": "occurrence",
                },
            },
            {
                "command": "occurrence.copy",
                "params": {
                    "component": "Board",
                    "translate": [100, 0, 0],
                },
                "bind": {
                    "$board_2": "occurrence",
                },
            },
            {
                "command": "occurrence.move",
                "params": {
                    "occurrence": "$board_2",
                    "axis": [0, 0, 1],
                    "angle": "90 deg",
                },
            },
        ])
        server = FakeSolidCraft([
            {
                "id": 1,
                "ok": True,
                "result": {"checkpoint": 7},
            },
            {
                "id": 1,
                "ok": True,
                "result": {
                    "completed": 2,
                    "results": [
                        {"component": 20, "occurrence": 101},
                        {"component": 20, "occurrence": 102},
                    ],
                    "undone": 0,
                },
            },
            {
                "id": 1,
                "ok": True,
                "result": {
                    "completed": 1,
                    "results": [
                        {"occurrence": 102},
                    ],
                    "undone": 0,
                },
            },
            {
                "id": 1,
                "ok": True,
                "result": {
                    "checkpoint": 7,
                    "restored": False,
                },
            },
        ])
        self.configure(server)

        result = send_document(document, directory=self.directory)
        server.join()

        self.assertEqual(
            result["variables"],
            {
                "$board_1": 101,
                "$board_2": 102,
            },
        )
        self.assertEqual(
            [request["method"] for request in server.requests],
            [
                "engine.execute",
                "engine.batch",
                "engine.batch",
                "engine.execute",
            ],
        )
        first_batch = server.requests[1]["params"]["commands"]
        self.assertNotIn("bind", first_batch[0])
        self.assertNotIn("bind", first_batch[1])
        self.assertEqual(
            server.requests[2]["params"]["commands"][0]["params"]["occurrence"],
            102,
        )
        self.assertEqual(
            server.requests[3]["params"]["command"],
            "edit.restore_checkpoint",
        )
        self.assertEqual(
            server.requests[3]["params"]["params"],
            {"checkpoint": 7, "forget": True},
        )
        self.assertEqual(
            result["replay_log"]["variables"]["$board_2"],
            102,
        )
        self.assertEqual(
            result["replay_log"]["commands"][2]["resolved_params"]["occurrence"],
            102,
        )

    def test_replay_v2_can_prepend_existing_runtime_list_to_result(self):
        variables = {"$seed_curves": ["c1"]}
        items = [{
            "command": "sketch.pattern.rectangular",
            "params": {"entities": "$seed_curves", "count": 3, "spacing": 20},
            "bind": {
                "$pattern_curves": {
                    "field": "curves",
                    "prepend": "$seed_curves",
                }
            },
        }]
        bound = apply_bindings(
            items,
            [{"curves": ["c2", "c3"]}],
            variables,
        )

        self.assertEqual(
            variables["$pattern_curves"],
            ["c1", "c2", "c3"],
        )
        self.assertEqual(
            bound,
            [{"$pattern_curves": ["c1", "c2", "c3"]}],
        )

    def test_replay_v2_selects_face_result_fields(self):
        document = replay_document([
            {
                "command": "model.faces",
                "params": {"body": "Plate"},
                "bind": {
                    "$face_point": {
                        "field": "faces",
                        "where": {"plane_normal": [0, 0, 1]},
                        "max": "area",
                        "select": "point",
                    },
                    "$face_index": {
                        "field": "faces",
                        "where": {"plane_normal": [0, 0, 1]},
                        "max": "area",
                        "select": "index",
                    },
                },
            },
            {
                "command": "sketch.create",
                "params": {
                    "name": "Top sketch",
                    "project_edges": False,
                    "plane": {
                        "face": "$face_point",
                        "body": "Plate",
                        "index": "$face_index",
                    },
                },
            },
        ])
        server = FakeSolidCraft([
            {"id": 1, "ok": True, "result": {"checkpoint": 11}},
            {
                "id": 1,
                "ok": True,
                "result": {
                    "completed": 1,
                    "results": [{
                        "body": "Plate",
                        "faces": [
                            {
                                "index": 1,
                                "area": 200.0,
                                "plane_normal": [0, 0, 1],
                                "point": [10, 10, 5],
                            },
                            {
                                "index": 4,
                                "area": 9000.0,
                                "plane_normal": [0, 0, 1],
                                "point": [-30, -20, 5],
                            },
                            {
                                "index": 5,
                                "area": 9000.0,
                                "plane_normal": [0, 0, -1],
                                "point": [0, 0, 0],
                            },
                        ],
                    }],
                    "undone": 0,
                },
            },
            {
                "id": 1,
                "ok": True,
                "result": {
                    "completed": 1,
                    "results": [{
                        "sketch": 30,
                        "name": "Top sketch",
                        "projected": None,
                        "attachment": "exact_face",
                    }],
                    "undone": 0,
                },
            },
            {
                "id": 1,
                "ok": True,
                "result": {"checkpoint": 11, "restored": False},
            },
        ])
        self.configure(server)

        result = send_document(document, directory=self.directory)
        server.join()

        self.assertEqual(result["variables"]["$face_index"], 4)
        self.assertEqual(result["variables"]["$face_point"], [-30, -20, 5])
        plane = server.requests[2]["params"]["commands"][0]["params"]["plane"]
        self.assertEqual(
            plane,
            {
                "face": [-30, -20, 5],
                "body": "Plate",
                "index": 4,
            },
        )

    def test_replay_v2_rejects_ambiguous_selected_record(self):
        document = replay_document([
            {
                "command": "model.faces",
                "params": {"body": "Plate"},
                "bind": {
                    "$face_point": {
                        "field": "faces",
                        "where": {"plane_normal": [0, 0, 1]},
                        "max": "area",
                        "select": "point",
                    },
                },
            },
            {
                "command": "sketch.create",
                "params": {"plane": {"face": "$face_point"}},
            },
        ])
        server = FakeSolidCraft([
            {"id": 1, "ok": True, "result": {"checkpoint": 12}},
            {
                "id": 1,
                "ok": True,
                "result": {
                    "completed": 1,
                    "results": [{
                        "body": "Plate",
                        "faces": [
                            {
                                "index": 1,
                                "area": 100.0,
                                "plane_normal": [0, 0, 1],
                                "point": [0, 0, 5],
                            },
                            {
                                "index": 2,
                                "area": 100.0,
                                "plane_normal": [0, 0, 1],
                                "point": [20, 0, 5],
                            },
                        ],
                    }],
                    "undone": 0,
                },
            },
            {
                "id": 1,
                "ok": True,
                "result": {"checkpoint": 12, "restored": True},
            },
        ])
        self.configure(server)

        with self.assertRaisesRegex(LiveError, "matched 2 records"):
            send_document(document, directory=self.directory)
        server.join()

    def test_replay_v1_document_is_rejected(self):
        document = {
            "format": "scpf-replay",
            "version": 1,
            "commands": [{
                "command": "component.create",
                "params": {"name": "Board"},
                "bind": {"$board": "occurrence"},
            }],
        }
        with self.assertRaisesRegex(LiveError, "expected 2"):
            send_document(document, directory=self.directory)

    def test_replay_failure_restores_whole_checkpoint(self):
        document = replay_document([
            {
                "command": "component.create",
                "params": {"name": "Board", "grounded": False},
                "bind": {"$board": "occurrence"},
            },
            {
                "command": "occurrence.move",
                "params": {
                    "occurrence": "$board",
                    "axis": [0, 0, 1],
                    "angle": "90 deg",
                },
            },
        ])
        server = FakeSolidCraft([
            {
                "id": 1,
                "ok": True,
                "result": {"checkpoint": 9},
            },
            {
                "id": 1,
                "ok": True,
                "result": {
                    "completed": 1,
                    "results": [
                        {"component": 30, "occurrence": 201},
                    ],
                    "undone": 0,
                },
            },
            {
                "id": 1,
                "ok": True,
                "result": {
                    "completed": 0,
                    "results": [],
                    "undone": 0,
                    "rolled_back": True,
                    "failed": {
                        "index": 0,
                        "command": "occurrence.move",
                        "error": "bad move",
                    },
                },
            },
            {
                "id": 1,
                "ok": True,
                "result": {
                    "checkpoint": 9,
                    "restored": True,
                },
            },
        ])
        self.configure(server)

        with self.assertRaisesRegex(LiveError, "bad move"):
            send_document(document, directory=self.directory)
        server.join()

        self.assertEqual(
            server.requests[-1]["params"]["command"],
            "edit.restore_checkpoint",
        )
        self.assertEqual(
            server.requests[-1]["params"]["params"],
            {"checkpoint": 9},
        )

    def test_replay_document_rejects_use_before_bind(self):
        document = replay_document([
            {
                "command": "occurrence.move",
                "params": {"occurrence": "$board"},
            },
            {
                "command": "component.create",
                "params": {"name": "Board"},
                "bind": {"$board": "occurrence"},
            },
        ])
        with self.assertRaisesRegex(LiveError, "before binding"):
            send_document(document, directory=self.directory)

    def test_new_design_uses_native_file_new(self):
        server = FakeSolidCraft({
            "id": 1,
            "ok": True,
            "result": {"name": "Untitled"},
        })
        self.configure(server)
        result = new_design(directory=self.directory)
        server.join()
        self.assertEqual(result["name"], "Untitled")
        self.assertEqual(server.request["method"], "engine.execute")
        self.assertEqual(server.request["params"]["command"], "file.new")
        self.assertEqual(server.request["params"]["params"], {})
        self.assertEqual(server.request["params"]["param_check"], "strict")

    def test_cli_new_creates_empty_design_before_model_batch(self):
        document = run_script(ROOT / "examples/plate/scpf/model.py")
        commands = document["commands"]
        server = FakeSolidCraft([
            {
                "id": 1,
                "ok": True,
                "result": {"name": "Untitled"},
            },
            {
                "id": 1,
                "ok": True,
                "result": {
                    "completed": len(commands),
                    "results": [{} for _ in commands],
                    "undone": 0,
                },
            },
        ])
        self.configure(server)
        with patch.dict(os.environ, {"SOLIDCRAFT_CONTROL_DIR": str(self.directory)}):
            self.assertEqual(
                main([
                    str(ROOT / "examples/plate/scpf/model.py"),
                    "--connect",
                    "--new",
                ]),
                0,
            )
        server.join()
        self.assertEqual(
            [request["method"] for request in server.requests],
            ["engine.execute", "engine.batch"],
        )
        self.assertEqual(
            server.requests[0]["params"]["command"],
            "file.new",
        )
        self.assertEqual(
            server.requests[1]["params"]["commands"],
            commands,
        )

    def test_live_bracket_can_send_native_commands(self):
        commands = run_script(ROOT / "examples/bracket/scpf/model.py")["commands"]
        server = FakeSolidCraft({
            "id": 1, "ok": True, "result": {"completed": len(commands), "results": [],
                                              "undone": 0},
        })
        self.configure(server)
        send_commands(commands, connect=f"127.0.0.1:{server.port}", directory=self.directory)
        server.join()
        self.assertEqual(server.request["params"]["commands"][0]["command"], "parameters.add")

    def test_replay_existing_json_unchanged_to_live_gui(self):
        commands_file = ROOT / "examples/bracket/source/bracket.json"
        original = json.loads(commands_file.read_text(encoding="utf-8"))
        self.assertEqual(read_command_file(commands_file), original)
        server = FakeSolidCraft({
            "id": 1, "ok": True,
            "result": {"completed": len(original["commands"]), "results": []},
        })
        self.configure(server)
        with patch.dict(os.environ, {"SOLIDCRAFT_CONTROL_DIR": str(self.directory)}):
            self.assertEqual(main(["replay", str(commands_file)]), 0)
        server.join()
        self.assertEqual(server.request["params"]["commands"], original["commands"])
        self.assertEqual(server.request["params"]["commands"][0]["command"],
                         "parameters.change")

    def test_replay_rejects_invalid_command_document(self):
        invalid = self.directory / "invalid.json"
        invalid.write_text('{"not_commands":[]}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "commands"):
            read_command_file(invalid)

    def test_replay_rejects_out_option(self):
        with self.assertRaises(SystemExit) as error:
            main(["replay", str(ROOT / "examples/bracket/source/bracket.json"),
                  "--out", "copied.json"])
        self.assertEqual(error.exception.code, 2)

    def test_new_requires_connect(self):
        with self.assertRaises(SystemExit) as error:
            main([
                str(ROOT / "examples/plate/scpf/model.py"),
                "--out",
                str(self.directory / "plate.json"),
                "--new",
            ])
        self.assertEqual(error.exception.code, 2)

    def test_live_rollback_failure_is_reported(self):
        commands = [{"command": "solid.box", "params": {}}]
        server = FakeSolidCraft({
            "id": 1, "ok": True,
            "result": {"completed": 0, "undone": 0, "rolled_back": True,
                       "failed": {"index": 0, "command": "solid.box", "error": "invalid size"}},
        })
        self.configure(server)
        with self.assertRaisesRegex(LiveError, "Rolled back: True"):
            send_commands(commands, directory=self.directory)
        server.join()

    def test_auth_failure_does_not_claim_success(self):
        commands = [{"command": "solid.box", "params": {}}]
        server = FakeSolidCraft({"id": 1, "ok": False, "error": "unauthorized"})
        self.configure(server)
        with self.assertRaisesRegex(LiveError, "unauthorized"):
            send_commands(commands, directory=self.directory)
        server.join()

    def test_missing_gui_is_an_error_not_a_new_headless_session(self):
        with self.assertRaisesRegex(LiveError, "No live SolidCraft port"):
            send_commands([{"command": "solid.box", "params": {}}],
                          directory=self.directory)

    def test_nonlocal_destination_is_rejected(self):
        with self.assertRaisesRegex(LiveError, "127.0.0.1"):
            send_commands([{"command": "solid.box", "params": {}}],
                          connect="example.com:1234", directory=self.directory)

    def test_invalid_response_does_not_claim_success(self):
        server = FakeSolidCraft({"id": 1, "ok": True, "result": {"completed": 0}})
        self.configure(server)
        with self.assertRaisesRegex(LiveError, "only 0"):
            send_commands([{"command": "solid.box", "params": {}}],
                          directory=self.directory)
        server.join()


if __name__ == "__main__":
    unittest.main()
