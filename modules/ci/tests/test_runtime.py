from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from cad_library_ci.runtime import execute


class RuntimeTests(unittest.TestCase):
    def test_negative_verification_fails_implementation(self):
        row = {
            "task_id": "box--cadquery",
            "owner": "box",
            "implementation": "cadquery",
            "builder": "test",
            "build_entry": "builder:build",
            "verify_entry": "verifier:run",
            "adapter": "test",
            "source": "source",
            "definition": "definition",
        }

        def build(source, output):
            output.write_bytes(b"stl")

        def verify(*args, **kwargs):
            return {"status": "fail"}

        manifest = {
            "schema": 3,
            "runtime": "reference",
            "image": "test:1",
            "build_items": [row],
            "verify_items": [row],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch(
                "cad_library_ci.runtime.resolve",
                side_effect=[build, verify],
            ):
                self.assertEqual(execute(manifest, root), 1)
            result = json.loads(
                (root / "models/box/cadquery/result.json").read_text()
            )
            self.assertEqual(result["build_status"], "pass")
            self.assertEqual(result["verification_status"], "fail")


if __name__ == "__main__":
    unittest.main()
