"""Architecture guard: supported replay plans never predict native occurrence names."""

from pathlib import Path
import re
import unittest

from qualification.cases import blocked_qualification_cases, supported_qualification_cases
from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]
GENERATED_OCCURRENCE = re.compile(r".+:\\d+$")


def _occurrence_selectors(command):
    params = command["params"]

    def visit(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "occurrence" and isinstance(item, str):
                    yield item
                yield from visit(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                yield from visit(item)

    yield from visit(params)

    if command["command"] == "joint.as_built":
        for key in ("a", "b"):
            value = params.get(key)
            if isinstance(value, str):
                yield value


class ReplaySafeOccurrenceSelectorTests(unittest.TestCase):
    def test_supported_examples_do_not_predict_solidcraft_occurrence_numbers(self):
        slugs = [case["slug"] for case in supported_qualification_cases()]
        # custom-anchor is a supported public showcase but deliberately not a
        # native qualification case while rotated relationships are deferred.
        slugs.append("custom-anchor")

        for slug in slugs:
            with self.subTest(slug=slug):
                document = run_script(
                    ROOT / "examples" / slug / "scpf" / "model.py"
                )
                selectors = [
                    selector
                    for command in document["commands"]
                    for selector in _occurrence_selectors(command)
                ]
                predicted = [
                    selector
                    for selector in selectors
                    if GENERATED_OCCURRENCE.fullmatch(selector)
                ]
                self.assertEqual(predicted, [])

    def test_blocked_copied_attachment_examples_fail_clearly(self):
        from scpf.compiler import ModelError

        for case in blocked_qualification_cases():
            slug = case["slug"]
            with self.subTest(slug=slug), self.assertRaisesRegex(
                ModelError,
                "cannot attach a copied occurrence",
            ):
                run_script(ROOT / "examples" / slug / "scpf" / "model.py")


if __name__ == "__main__":
    unittest.main()
