import json
from pathlib import Path
import tempfile
import unittest

from cad_library_build.publish import PublishError, update_scope


class PublishTests(unittest.TestCase):
    def test_full_then_incremental_preserves_unselected_model_owners(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate, target = root / "candidate", root / "target"
            for item in ("a", "b", "c"):
                path = candidate / "models" / item
                path.mkdir(parents=True)
                (path / "result.json").write_text(
                    json.dumps({"id": item, "status": "pass"})
                )
            update_scope(
                target,
                candidate,
                {
                    "active": ["a", "b", "c"],
                    "selected": ["a", "b", "c"],
                    "full": True,
                    "source_sha": "old",
                },
            )
            update_scope(
                target,
                candidate,
                {
                    "active": ["a", "b"],
                    "selected": ["b"],
                    "full": False,
                    "source_sha": "new",
                },
            )
            self.assertFalse((target / "models/c").exists())
            self.assertEqual(
                json.loads((target / "models/a/source.json").read_text())["source_sha"],
                "old",
            )
            self.assertEqual(
                json.loads((target / "models/b/source.json").read_text())["source_sha"],
                "new",
            )

    def test_rejects_missing_active_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(PublishError):
                update_scope(
                    root / "target",
                    root / "candidate",
                    {
                        "active": ["a"],
                        "selected": [],
                        "full": False,
                        "source_sha": "new",
                    },
                )


if __name__ == "__main__":
    unittest.main()
