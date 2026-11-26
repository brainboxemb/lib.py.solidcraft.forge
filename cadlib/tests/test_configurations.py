"""Configuration-table authoring and replay identity tests."""
import tempfile
import unittest
from pathlib import Path

from scpf import Anchor, Box, Configure, Hole, Param, Parameter, Suppress, compile_model
from scpf.compiler import ModelError
from scpf.replay import resolve_value, validate_replay_document, variables_in
from scpf.runner import run_script


class ConfigurationTests(unittest.TestCase):
    def test_named_parameter_rows_and_active(self):
        shape = Box(Parameter("width", 80), 30, 5)
        design = Configure(shape, active="Medium", columns=(Param("width"),),
                           rows={"Small": ("60 mm",), "Medium": ("80 mm",),
                                 "Large": ("100 mm",)})
        doc = compile_model(design, "Plate")
        commands = doc["commands"]
        self.assertEqual(commands[-7]["params"], {"params": ["width"]})
        self.assertEqual(commands[-6]["params"], {"name": "Default", "rename": "Small"})
        self.assertEqual(commands[-3]["params"], {"name": "Large", "values": {"param:width": "100 mm"}})
        self.assertEqual(commands[-2], {"command": "config.activate", "params": {"row": "Medium"}})
        self.assertEqual(commands[-1]["command"], "config.table")

    def test_feature_binding(self):
        plate = Box(Parameter("width", 80), 30, 5, anchor=Anchor.BOTTOM)
        hole = Hole(d=5).at(0, 0, 5)
        body = plate - hole
        doc = compile_model(Configure(body, active="Medium",
                            columns=(Param("width"), Suppress(hole)),
                            rows={"Medium": ("80 mm", True),
                                  "Large": ("100 mm", False)}), "Plate")
        validate_replay_document(doc)
        feature = next(c for c in doc["commands"] if c["command"] == "solid.hole")
        self.assertNotIn("$config_feature_2", feature["bind"])
        self.assertEqual(feature["bind"]["$config_name_2"], "name")
        cell = {"suppress:$config_name_2": "true"}
        self.assertEqual(variables_in(cell), {"$config_name_2"})
        self.assertEqual(
            resolve_value(cell, {"$config_name_2": "Hole1"}),
            {"suppress:Hole1": "true"},
        )

    def test_reject_unknown_param_and_unapplied_feature(self):
        body = Box(80, 30, 5)
        with self.assertRaisesRegex(ModelError, "unknown native configuration parameter"):
            compile_model(Configure(body, active="A", columns=(Param("missing"),),
                                    rows={"A": (60,)}), "Plate")
        with self.assertRaisesRegex(ModelError, "already-applied"):
            compile_model(Configure(body, active="A", columns=(Suppress(Hole(d=5)),),
                                    rows={"A": (True,)}), "Plate")

    def test_reject_invalid_table(self):
        body = Box(80, 30, 5)
        with self.assertRaisesRegex(ValueError, "active configuration"):
            Configure(body, active="B", columns=(Param("width"),), rows={"A": (60,)})
        with self.assertRaisesRegex(ValueError, "cell count"):
            Configure(body, active="A", columns=(Param("width"),), rows={"A": ()})
        with self.assertRaisesRegex(TypeError, "suppression cells"):
            Configure(body, active="A", columns=(Suppress(body),), rows={"A": (1,)})

    def test_configure_wraps_parametric_assembly_placement(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.py"
            path.write_text(
                "class Screen:\n"
                "    def build(self):\n"
                "        return Box(80, 10, 50)\n"
                "class FrontPlate:\n"
                "    def build(self):\n"
                "        return Box(80, 2, 50)\n"
                "class Display:\n"
                "    plate_y = 8.0\n"
                "    plate_z = 0.0\n"
                "    def build(self):\n"
                "        screen = Screen(name='screen')\n"
                "        plate = FrontPlate(name='front_plate', "
                "placement=Placement(y=self.plate_y, z=self.plate_z))\n"
                "        return Configure(\n"
                "            screen + plate, active='Front',\n"
                "            columns=(Param('plate_y'), Param('plate_z')),\n"
                "            rows={\n"
                "                'Front': ('8 mm', '0 mm'),\n"
                "                'Below': ('0 mm', '-55 mm'),\n"
                "                'Service': ('25 mm', '0 mm'),\n"
                "            },\n"
                "        )\n"
                "Display()\n",
                encoding="utf-8",
            )
            document = run_script(path)

        commands = document["commands"]
        move = next(row for row in commands if row["command"] == "occurrence.move")
        self.assertEqual(move["params"]["translate"][1:], ["plate_y", "plate_z"])
        configure = next(
            row for row in commands if row["command"] == "config.configure"
        )
        self.assertEqual(
            configure["params"],
            {"params": ["plate_y", "plate_z"]},
        )
        self.assertEqual(
            next(row for row in commands if row["command"] == "config.activate")["params"],
            {"row": "Front"},
        )


if __name__ == "__main__":
    unittest.main()
