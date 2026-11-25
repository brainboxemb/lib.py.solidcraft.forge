import json
from pathlib import Path
import tempfile
import unittest

from cad_library_release.__main__ import (
    ReleaseQualificationError,
    validate_build_scope,
)


SHA = "a" * 40


class ReleaseQualificationTests(unittest.TestCase):
    def _scope(self, root: Path, *, source_sha=SHA, full=True, library=True,
               active=("one",), selected=None, status="pass", provenance=SHA):
        if selected is None:
            selected = active
        scope = root / "main"
        scope.mkdir(parents=True)
        (scope / "build-plan.json").write_text(
            json.dumps(
                {
                    "schema": 2,
                    "source_sha": source_sha,
                    "library": library,
                    "full": full,
                    "active": list(active),
                    "selected": list(selected),
                    "models": [{"id": item} for item in active],
                }
            ),
            encoding="utf-8",
        )
        for item in active:
            model = scope / "models" / item
            model.mkdir(parents=True)
            (model / "result.json").write_text(
                json.dumps({"id": item, "status": status}), encoding="utf-8"
            )
            (model / "source.json").write_text(
                json.dumps({"source_sha": provenance}), encoding="utf-8"
            )
        return scope

    def test_accepts_exact_full_library_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            scope = self._scope(Path(tmp), active=("one", "two"))
            plan = validate_build_scope(scope, SHA)
            self.assertTrue(plan["library"])
            self.assertEqual(plan["selected"], ["one", "two"])

    def test_rejects_source_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            scope = self._scope(Path(tmp), source_sha="b" * 40)
            with self.assertRaisesRegex(ReleaseQualificationError, "does not match"):
                validate_build_scope(scope, SHA)

    def test_requires_full_library_qualification(self):
        for field, kwargs, message in (
            ("full", {"full": False}, "full stable build"),
            ("library", {"library": False}, "qualify the library"),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                scope = self._scope(Path(tmp), **kwargs)
                with self.assertRaisesRegex(ReleaseQualificationError, message):
                    validate_build_scope(scope, SHA)

    def test_requires_all_active_owners_selected(self):
        with tempfile.TemporaryDirectory() as tmp:
            scope = self._scope(Path(tmp), active=("one", "two"), selected=("one",))
            with self.assertRaisesRegex(ReleaseQualificationError, "every active"):
                validate_build_scope(scope, SHA)

    def test_requires_successful_matching_model_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            scope = self._scope(Path(tmp), status="fail")
            with self.assertRaisesRegex(ReleaseQualificationError, "not successful"):
                validate_build_scope(scope, SHA)
        with tempfile.TemporaryDirectory() as tmp:
            scope = self._scope(Path(tmp), provenance="b" * 40)
            with self.assertRaisesRegex(ReleaseQualificationError, "model source"):
                validate_build_scope(scope, SHA)


if __name__ == "__main__":
    unittest.main()
