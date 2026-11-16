"""Q1/Q2 qualification for the abstract model-authoring fixture."""
from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "examples/model_authoring/scpf/model.py"


class ModelAuthoringFixtureTests(unittest.TestCase):
    def test_multi_part_material_fixture_uses_component_structure(self):
        commands = run_script(MODEL)["commands"]

        parameters = [
            command["params"]["name"]
            for command in commands
            if command["command"] == "parameters.add"
        ]
        self.assertEqual(len(parameters), 1)
        self.assertTrue(parameters[0].endswith("_Plate_length"), parameters)
        self.assertFalse(any("_plate_y" in name for name in parameters))
        self.assertFalse(any("SIZE" in name for name in parameters))

        material_names = [
            command["params"]["name"]
            for command in commands
            if command["command"] == "material.create"
        ]
        self.assertEqual(material_names, ["Birch", "Steel"])
        self.assertEqual(
            sum(command["command"] == "material.assign" for command in commands),
            2,
        )

        component_names = [
            command["params"]["name"]
            for command in commands
            if command["command"] == "component.create"
        ]
        self.assertEqual(component_names, ["Plate", "Block"])

        copies = [
            command for command in commands
            if command["command"] == "occurrence.copy"
        ]
        self.assertEqual(len(copies), 1)
        self.assertEqual(copies[0]["params"]["component"], "Block")
        self.assertEqual(copies[0]["params"]["translate"], [20.0, 0.0, 0.0])


if __name__ == "__main__":
    unittest.main()
