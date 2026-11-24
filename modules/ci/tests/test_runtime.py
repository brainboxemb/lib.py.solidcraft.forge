from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from cad_library_ci.runtime import execute


class RuntimeTests(unittest.TestCase):
    def test_negative_verification_stage_is_retained(self):
        build_row = {
            "task_id": "box--cadquery",
            "owner": "box",
            "implementation": "cadquery",
            "builder": "test",
            "build_entry": "builder:build",
            "source": "source",
        }
        verify_row = {
            "task_id": "box--cadquery",
            "owner": "box",
            "implementation": "cadquery",
            "builder": "test",
            "stage_id": "geometry",
            "verify_entry": "verifier:run",
            "adapter": "test",
            "artifact": "model.stl",
            "definition": "definition",
        }

        def build(source, output):
            output.write_bytes(b"stl")

        def verify(*args, **kwargs):
            return {"status": "fail"}

        manifest = {
            "schema": 4,
            "runtime": "reference",
            "image": "test:1",
            "build_items": [build_row],
            "verify_items": [verify_row],
            "preview_items": [],
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch(
                "cad_library_ci.runtime.resolve",
                side_effect=[build, verify],
            ):
                self.assertEqual(execute(manifest, root), 1)

            result = json.loads(
                (
                    root
                    / "models/box/cadquery/verification/geometry/stage-result.json"
                ).read_text()
            )
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["stage_id"], "geometry")

    def test_later_stage_does_not_overwrite_prior_stage_evidence(self):
        target = {
            "task_id": "box--solidcraft",
            "owner": "box",
            "implementation": "solidcraft",
            "builder": "test",
        }
        native = {
            **target,
            "stage_id": "native",
            "verify_entry": "verifier:run",
            "adapter": "native",
            "artifact": "model.sc",
            "definition": "native.py",
        }
        geometry = {
            **target,
            "stage_id": "geometry",
            "verify_entry": "verifier:run",
            "adapter": "mesh",
            "artifact": "model.stl",
            "definition": "geometry.json",
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "models/box/solidcraft"
            model.mkdir(parents=True)
            (model / "build.json").write_text(json.dumps({
                "build_status": "pass",
            }))
            (model / "model.sc").write_text("native")
            (model / "model.stl").write_text("mesh")

            def verify(adapter, artifact, definition, output, **kwargs):
                output.mkdir(parents=True, exist_ok=True)
                (output / "verification.json").write_text(
                    json.dumps({"status": "pass", "adapter": adapter})
                )
                return {"status": "pass"}

            manifest = {
                "schema": 4,
                "runtime": "reference",
                "image": "test:1",
                "build_items": [],
                "verify_items": [native, geometry],
                "preview_items": [],
            }
            with patch(
                "cad_library_ci.runtime.resolve",
                return_value=verify,
            ):
                self.assertEqual(execute(manifest, root), 0)

            self.assertTrue(
                (
                    model
                    / "verification/native/verification.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    model
                    / "verification/geometry/verification.json"
                ).is_file()
            )


if __name__ == "__main__":
    unittest.main()
