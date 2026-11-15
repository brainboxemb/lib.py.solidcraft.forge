"""Headless execution-plan tests without a real SolidCraft binary."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scpf.headless import HeadlessPlanError, execute_document
from scpf.plan import result_ref


class HeadlessExecutionTests(unittest.TestCase):
    def test_headless_phases_bind_runtime_id_and_publish_only_final_files(self):
        document = {
            "commands": [
                {
                    "command": "occurrence.copy",
                    "params": {"component": "Block"},
                },
                {
                    "command": "occurrence.move",
                    "params": {
                        "occurrence": result_ref("occurrence:right"),
                        "translate": [20, 0, 0],
                    },
                },
            ],
            "bindings": {
                "occurrence:right": {
                    "command": 0,
                    "field": "occurrence",
                },
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            final_model = root / "model.sc"
            final_step = root / "model.step"
            final_results = root / "results.json"
            phases = []

            def fake_run(command, check):
                self.assertTrue(check)
                phase_file = Path(command[2])
                phases.append(json.loads(phase_file.read_text(encoding="utf-8")))

                result_path = Path(
                    command[command.index("--json-out") + 1]
                )
                save_path = Path(command[command.index("--save") + 1])
                result_path.write_text(
                    json.dumps([
                        {"occurrence": 41}
                    ]),
                    encoding="utf-8",
                )
                save_path.write_text("native-model", encoding="utf-8")
                if "--out" in command:
                    export_path = Path(command[command.index("--out") + 1])
                    export_path.write_text("step", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0)

            with patch("scpf.headless.subprocess.run", side_effect=fake_run):
                result = execute_document(
                    document,
                    save=final_model,
                    export=final_step,
                    json_out=final_results,
                )

            self.assertEqual(result["bindings"], {"occurrence:right": 41})
            self.assertEqual(result["phases"], 2)
            self.assertEqual(
                phases[1]["commands"][0]["params"]["occurrence"],
                41,
            )
            self.assertEqual(final_model.read_text(encoding="utf-8"), "native-model")
            self.assertEqual(final_step.read_text(encoding="utf-8"), "step")
            self.assertEqual(
                json.loads(final_results.read_text(encoding="utf-8")),
                [{"occurrence": 41}, {"occurrence": 41}],
            )

    def test_failed_later_phase_does_not_replace_requested_output(self):
        document = {
            "commands": [
                {
                    "command": "occurrence.copy",
                    "params": {"component": "Block"},
                },
                {
                    "command": "occurrence.move",
                    "params": {
                        "occurrence": result_ref("occurrence:right"),
                        "translate": [20, 0, 0],
                    },
                },
            ],
            "bindings": {
                "occurrence:right": {
                    "command": 0,
                    "field": "occurrence",
                },
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            final_model = root / "model.sc"
            final_model.write_text("old-model", encoding="utf-8")
            calls = 0

            def fake_run(command, check):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise subprocess.CalledProcessError(1, command)
                result_path = Path(
                    command[command.index("--json-out") + 1]
                )
                save_path = Path(command[command.index("--save") + 1])
                result_path.write_text(
                    json.dumps([{"occurrence": 41}]),
                    encoding="utf-8",
                )
                save_path.write_text("partial", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0)

            with patch("scpf.headless.subprocess.run", side_effect=fake_run):
                with self.assertRaisesRegex(HeadlessPlanError, "phase 1"):
                    execute_document(document, save=final_model)

            self.assertEqual(final_model.read_text(encoding="utf-8"), "old-model")


if __name__ == "__main__":
    unittest.main()
