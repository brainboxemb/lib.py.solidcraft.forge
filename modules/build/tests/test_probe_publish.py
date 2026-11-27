import json
from pathlib import Path
import tempfile
import unittest

from cad_library_build.probe_publish import update_probe_scope
from cad_library_build.publish import PublishError


class ProbePublishTests(unittest.TestCase):
    def _candidate(self, root, probe_id, status="pass"):
        path = root / "candidate" / "api-probes" / probe_id
        path.mkdir(parents=True)
        (path / "result.json").write_text(
            json.dumps({"id": probe_id, "status": status}),
            encoding="utf-8",
        )
        (path / "artifact.txt").write_text(probe_id, encoding="utf-8")
        return root / "candidate"

    def test_selected_probe_updates_without_touching_models_or_other_probes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target"
            (target / "models").mkdir(parents=True)
            (target / "models" / "sentinel").write_text("model")
            old = target / "api-probes" / "old"
            old.mkdir(parents=True)
            (old / "sentinel").write_text("old")

            candidate = self._candidate(root, "configuration")
            update_probe_scope(
                target,
                candidate,
                {
                    "source_sha": "abc",
                    "available": ["configuration"],
                    "selected": ["configuration"],
                },
            )

            self.assertEqual((target / "models/sentinel").read_text(), "model")
            self.assertEqual((target / "api-probes/old/sentinel").read_text(), "old")
            self.assertEqual(
                (target / "api-probes/configuration/artifact.txt").read_text(),
                "configuration",
            )
            self.assertEqual(
                json.loads(
                    (target / "api-probes/configuration/source.json").read_text()
                )["source_sha"],
                "abc",
            )

    def test_unselected_existing_probe_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target"
            old = target / "api-probes" / "old"
            old.mkdir(parents=True)
            (old / "sentinel").write_text("old")
            candidate = root / "candidate"
            candidate.mkdir()

            update_probe_scope(
                target,
                candidate,
                {
                    "source_sha": "abc",
                    "available": [],
                    "selected": [],
                },
            )

            self.assertEqual((old / "sentinel").read_text(), "old")

    def test_failed_probe_is_not_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = self._candidate(root, "configuration", status="fail")
            with self.assertRaisesRegex(PublishError, "unsuccessful"):
                update_probe_scope(
                    root / "target",
                    candidate,
                    {
                        "source_sha": "abc",
                        "available": ["configuration"],
                        "selected": ["configuration"],
                    },
                )


if __name__ == "__main__":
    unittest.main()
