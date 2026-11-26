"""Configuration-table authoring and replay identity tests."""
import unittest

from scpf import Anchor, Box, Configure, Hole, Param, Parameter, Suppress, compile_model
from scpf.compiler import ModelError
from scpf.replay import resolve_value, validate_replay_document, variables_in


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


if __name__ == "__main__":
    unittest.main()
