from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from cad_library_ci.runtime import execute
import json


class RuntimeTests(unittest.TestCase):
    def test_negative_verification_fails_batch(self):
        row = {"id":"box", "builder":"test", "build_entry":"builder:build", "verify_entry":"verifier:run", "adapter":"test", "source":"source", "definition":"definition"}
        def build(source, output):
            output.write_bytes(b"stl")
        def verify(*args, **kwargs):
            return {"status":"fail"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("cad_library_ci.runtime.resolve", side_effect=[build, verify]):
                self.assertEqual(execute({"schema":1,"runtime":"reference","image":"test:1","examples":[row]}, root), 1)
            result = json.loads((root/"examples/box/result.json").read_text())
            self.assertEqual(result["build_status"], "pass")
            self.assertEqual(result["verification_status"], "fail")
