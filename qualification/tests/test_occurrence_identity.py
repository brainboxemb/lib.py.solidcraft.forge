"""Qualification guard for Forge-owned occurrence identity."""

import re
from pathlib import Path
import unittest

from qualification.cases import QUALIFICATION_CASES
from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]
GENERATED_OCCURRENCE_LABEL = re.compile(r"^[^:]+:\\d+$")


def occurrence_selectors(value):
    """Yield values stored under native occurrence selector keys."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "occurrence":
                yield child
            yield from occurrence_selectors(child)
    elif isinstance(value, list):
        for child in value:
            yield from occurrence_selectors(child)


class OccurrenceIdentityQualificationTests(unittest.TestCase):
    def test_documented_cases_never_use_generated_occurrence_labels_as_selectors(self):
        checked = 0
        for case in QUALIFICATION_CASES:
            path = ROOT / "examples" / case["slug"] / "scpf" / "model.py"
            document = run_script(path)
            checked += 1

            for command in document["commands"]:
                for selector in occurrence_selectors(
                    command.get("params", {})
                ):
                    self.assertFalse(
                        isinstance(selector, str)
                        and GENERATED_OCCURRENCE_LABEL.fullmatch(selector),
                        (
                            f"{case['slug']}: {command['command']} uses "
                            f"generated occurrence label {selector!r}"
                        ),
                    )

                if command["command"] == "joint.as_built":
                    for key in ("a", "b"):
                        selector = command["params"][key]
                        self.assertFalse(
                            isinstance(selector, str)
                            and GENERATED_OCCURRENCE_LABEL.fullmatch(selector),
                            (
                                f"{case['slug']}: joint.as_built {key} uses "
                                f"generated occurrence label {selector!r}"
                            ),
                        )

        self.assertEqual(checked, len(QUALIFICATION_CASES))


if __name__ == "__main__":
    unittest.main()
