"""Qualification tests for change 0003: explicit child publication and inherited bindings."""
import json
import os
from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SOLIDCRAFT_VERSION = "0.30.1"
NATIVE_ROOT = os.environ.get("SCPF_NATIVE_ROOT")
SOLIDCRAFT_VERSION = os.environ.get("SCPF_SOLIDCRAFT_VERSION")


class ParameterScopeCommandTests(unittest.TestCase):
    def test_generated_parameter_contract(self):
        document = run_script(
            ROOT / "examples/parameter-scope/scpf/model.py"
        )

        params = _parameter_commands(document)
        self.assertEqual(
            [(row["name"], row["expression"]) for row in params],
            [
                ("d1_Panel_width", "40"),
                ("d2_Panel_2_width", "60"),
                ("shared_width", "80"),
            ],
        )

        boxes = [
            row["params"]
            for row in document["commands"]
            if row["command"] == "solid.box"
        ]
        self.assertEqual(len(boxes), 4)

        lengths = [row["length"] for row in boxes]
        self.assertIn("d1_Panel_width", lengths)
        self.assertIn("d2_Panel_2_width", lengths)
        self.assertIn("shared_width", lengths)
        self.assertIn("shared_width / 2", lengths)

        self.assertFalse(any(
            row["name"].startswith(("d1_Panel", "d2_Panel")) and row["name"].endswith("_depth")
            for row in params
        ))
        self.assertTrue(all(row["width"] == 20.0 for row in boxes))

        creates = [
            row["params"]["name"]
            for row in document["commands"]
            if row["command"] == "component.create"
        ]
        self.assertEqual(creates, ["Panel", "Panel 2", "Panel 3", "Panel 4"])

        copies = [
            row for row in document["commands"]
            if row["command"] == "occurrence.copy"
        ]
        self.assertEqual(len(copies), 1)


@unittest.skipUnless(NATIVE_ROOT, "native SolidCraft evidence not supplied")
class ParameterScopeNativeTests(unittest.TestCase):
    def test_baseline_native_parameters_and_geometry(self):
        self.assertEqual(SOLIDCRAFT_VERSION, EXPECTED_SOLIDCRAFT_VERSION)

        case = Path(NATIVE_ROOT) / "parameter-scope"
        measurements = _load(case / "measurements.json")
        parameters = _load(case / "parameters.json")
        design = _load(case / "model.json")

        self.assertEqual(measurements["body_count"], 5)
        self.assertEqual(_widths(measurements), [40.0, 40.0, 60.0, 80.0, 80.0])
        self.assertEqual(
            _params(measurements),
            {
                "d1_Panel_width": 40.0,
                "d2_Panel_2_width": 60.0,
                "shared_width": 80.0,
            },
        )
        self.assertEqual(
            {row["name"] for row in parameters},
            {"d1_Panel_width", "d2_Panel_2_width", "shared_width"},
        )

        fmt = design.get("format")
        self.assertIsInstance(fmt, str)
        self.assertTrue(fmt.startswith("solidcraft/"))

    def test_shared_parameter_mutation_remains_associative(self):
        measurements = _load(
            Path(NATIVE_ROOT)
            / "parameter-scope"
            / "measurements-shared-width-100.json"
        )

        params = _params(measurements)
        self.assertEqual(params["d1_Panel_width"], 40.0)
        self.assertEqual(params["d2_Panel_2_width"], 60.0)
        self.assertEqual(params["shared_width"], 100.0)
        self.assertEqual(
            _widths(measurements),
            [40.0, 50.0, 60.0, 100.0, 100.0],
        )


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _parameter_commands(document):
    return [
        row["params"]
        for row in document["commands"]
        if row["command"] == "parameters.add"
    ]


def _widths(measurements):
    return sorted(
        round(body["bbox"]["max"][0] - body["bbox"]["min"][0], 6)
        for body in measurements["bodies"]
    )


def _params(measurements):
    return {row["name"]: row["value"] for row in measurements["params"]}


if __name__ == "__main__":
    unittest.main()
