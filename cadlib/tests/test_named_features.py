from pathlib import Path
import tempfile
import unittest

from scpf import Axis, Box, Cylinder, compile_model, feature, run_script


class NamedFeatureTests(unittest.TestCase):
    def test_scope_names_one_history_feature_and_sets_initial_state(self):
        body = Box(40, 30, 10)
        with feature("installed", suppressed=True) as installed:
            body = body - Cylinder(d=8, h=20)

        self.assertEqual(body.kind, "named_feature")
        self.assertIs(installed.shape, body)

        body.configure(
            active="Free",
            columns=(installed,),
            rows={
                "Free": (True,),
                "Installed": (False,),
            },
        )
        commands = compile_model(body, "Clamp")["commands"]

        cut = next(
            command
            for command in commands
            if command["command"] == "solid.cylinder"
            and command["params"].get("operation") == "cut"
        )
        self.assertEqual(cut["bind"]["$feature_installed_name"], "name")
        self.assertEqual(cut["bind"]["$config_name_1"], "name")

        initial = next(
            command
            for command in commands
            if command["command"] == "timeline.suppress"
        )
        self.assertEqual(
            initial["params"],
            {
                "features": ["$feature_installed_name"],
                "suppressed": True,
            },
        )

        rows = [
            command
            for command in commands
            if command["command"] == "config.row"
        ]
        self.assertTrue(any(
            row["params"].get("values") == {"suppress:$config_name_1": "true"}
            for row in rows
        ))
        self.assertTrue(any(
            row["params"].get("values") == {"suppress:$config_name_1": "false"}
            for row in rows
        ))

    def test_compound_transform_is_one_suppressible_history_feature(self):
        body = Box(40, 12, 10)
        with feature("installed_position", suppressed=True) as installed:
            body = body.transform(
                translate=(30, 20, 5),
                axis=Axis.Z,
                angle=30,
                origin=(0, 0, 0),
            )

        body.configure(
            active="Normal",
            columns=(installed,),
            rows={"Normal": (True,)},
        )
        commands = compile_model(body, "Panel")["commands"]

        moves = [
            command
            for command in commands
            if command["command"] == "solid.move"
        ]
        self.assertEqual(len(moves), 1)
        move = moves[0]
        self.assertEqual(
            move["params"],
            {
                "bodies": ["Panel"],
                "translate": [30, 20, 5],
                "axis": [0.0, 0.0, 1.0],
                "angle": "30 deg",
                "origin": [0, 0, 0],
            },
        )
        self.assertEqual(
            move["bind"]["$feature_installed_position_name"],
            "name",
        )
        self.assertEqual(move["bind"]["$config_name_1"], "name")

        suppression = [
            command
            for command in commands
            if command["command"] == "timeline.suppress"
        ]
        self.assertEqual(len(suppression), 1)
        self.assertEqual(
            suppression[0]["params"],
            {
                "features": ["$feature_installed_position_name"],
                "suppressed": True,
            },
        )

        rows = [
            command["params"]
            for command in commands
            if command["command"] == "config.row"
        ]
        self.assertEqual(
            [
                row["values"]
                for row in rows
                if row.get("name") == "Normal" and "values" in row
            ],
            [{"suppress:$config_name_1": "true"}],
        )

    def test_transform_requires_real_finite_rigid_motion(self):
        body = Box(10, 10, 10)
        with self.assertRaisesRegex(ValueError, "non-zero"):
            body.transform()
        with self.assertRaisesRegex(ValueError, "Axis.X"):
            body.transform(translate=(1, 0, 0), axis="Q")
        with self.assertRaisesRegex(ValueError, "XYZ"):
            body.transform(translate=(1, 2))

    def test_scope_requires_public_name_boolean_state_and_one_history_step(self):
        with self.assertRaisesRegex(ValueError, "public Python identifier"):
            feature("_installed")
        with self.assertRaisesRegex(TypeError, "True or False"):
            feature("installed", suppressed=1)

        body = Box(40, 30, 10)
        with self.assertRaisesRegex(ValueError, "exactly one CAD history feature"):
            with feature("too_much"):
                body = body - Cylinder(d=8, h=20)
                body = body - Cylinder(d=4, h=20)

        with self.assertRaisesRegex(ValueError, "exactly one terminal Shape"):
            with feature("ambiguous"):
                Cylinder(d=8, h=20)
                Cylinder(d=4, h=20)

    def test_feature_scopes_cannot_nest(self):
        with feature("outer"):
            with self.assertRaisesRegex(RuntimeError, "cannot be nested"):
                with feature("inner"):
                    Cylinder(d=4, h=10)
            Cylinder(d=8, h=20)

    def test_reusable_component_exports_scoped_feature_for_parent_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.py"
            path.write_text(
                "from scpf import *\n"
                "@component\n"
                "class Coupler:\n"
                "    def build(self):\n"
                "        body = Box(40, 24, 12, anchor=Anchor.BOTTOM)\n"
                "        with feature('panel_pin', suppressed=True):\n"
                "            body = body - Hole(d=5).at(0, 0, 12)\n"
                "        return body\n"
                "class Model:\n"
                "    def build(self):\n"
                "        child = Coupler()\n"
                "        child.configure(\n"
                "            active='Medium',\n"
                "            columns=(child.feature('panel_pin'),),\n"
                "            rows={\n"
                "                'Medium': (True,),\n"
                "                'Large': (False,),\n"
                "            },\n"
                "        )\n"
                "        return child\n"
                "Model()\n",
                encoding="utf-8",
            )

            commands = run_script(path)["commands"]

        hole = next(
            command
            for command in commands
            if command["command"] == "solid.hole"
        )
        feature_bindings = [
            variable
            for variable, field in hole.get("bind", {}).items()
            if "feature_panel_pin_name" in variable and field == "name"
        ]
        self.assertEqual(len(feature_bindings), 1)
        self.assertIn("$config_name_1", hole.get("bind", {}))

        initial = next(
            command
            for command in commands
            if command["command"] == "timeline.suppress"
        )
        self.assertTrue(initial["params"]["suppressed"])
        self.assertEqual(len(initial["params"]["features"]), 1)
        self.assertIn("feature_panel_pin_name", initial["params"]["features"][0])


if __name__ == "__main__":
    unittest.main()
