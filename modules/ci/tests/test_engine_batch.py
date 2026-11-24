from pathlib import Path
from types import SimpleNamespace
import json
import tempfile
import unittest
from unittest.mock import patch

from cad_library_ci.runtime import execute


class EngineBatchTests(unittest.TestCase):
    def test_one_child_for_two_rows_and_parent_verification(self):
        rows = [
            {
                "task_id": f"box--{impl}",
                "owner": "box",
                "implementation": impl,
                "builder": "test",
                "engine_python": "/opt/isolated/bin/python",
                "build_entry": "builder:build",
                "source": "source",
            }
            for impl in ("a", "b")
        ]
        verify_rows = [
            {
                "task_id": row["task_id"],
                "owner": row["owner"],
                "implementation": row["implementation"],
                "builder": "test",
                "stage_id": "geometry",
                "verify_entry": "verifier:run",
                "adapter": "mesh",
                "artifact": "model.stl",
                "definition": "definition",
            }
            for row in rows
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def run(command, **kwargs):
                self.assertEqual(
                    command[0],
                    "/opt/isolated/bin/python",
                )
                manifest = json.loads(
                    Path(
                        command[
                            command.index("--manifest") + 1
                        ]
                    ).read_text()
                )
                self.assertEqual(
                    len(manifest["items"]),
                    2,
                )
                for row in rows:
                    target = (
                        root
                        / "models"
                        / row["owner"]
                        / row["implementation"]
                    )
                    target.mkdir(parents=True, exist_ok=True)
                    (target / "model.stl").write_bytes(b"stl")
                Path(
                    command[
                        command.index("--build-report") + 1
                    ]
                ).write_text(
                    json.dumps({
                        "schema": 1,
                        "results": {
                            row["task_id"]: {"status": "pass"}
                            for row in rows
                        },
                    })
                )
                return SimpleNamespace(returncode=0)

            manifest = {
                "schema": 4,
                "runtime": "reference",
                "image": "test:1",
                "build_items": rows,
                "verify_items": verify_rows,
                "preview_items": [],
            }
            with patch(
                "cad_library_ci.runtime.subprocess.run",
                side_effect=run,
            ) as child, patch(
                "cad_library_ci.runtime.resolve",
                return_value=lambda *args, **kwargs: {"status": "pass"},
            ) as resolve:
                self.assertEqual(
                    execute(manifest, root),
                    0,
                )
                child.assert_called_once()
                self.assertEqual(
                    resolve.call_count,
                    2,
                )

    def test_missing_child_report_fails_batch(self):
        row = {
            "task_id": "box--a",
            "owner": "box",
            "implementation": "a",
            "builder": "test",
            "engine_python": "/opt/test/python",
            "build_entry": "builder:build",
            "source": "source",
        }
        with tempfile.TemporaryDirectory() as tmp:
            with patch(
                "cad_library_ci.runtime.subprocess.run",
                return_value=SimpleNamespace(returncode=0),
            ):
                self.assertEqual(
                    execute(
                        {
                            "schema": 4,
                            "runtime": "reference",
                            "image": "test:1",
                            "build_items": [row],
                            "verify_items": [],
                            "preview_items": [],
                        },
                        Path(tmp),
                    ),
                    1,
                )


if __name__ == "__main__":
    unittest.main()
