"""Final-model configuration authoring and replay identity tests."""
import tempfile
import unittest
from pathlib import Path

from scpf import Anchor, Box, Hole, Parameter, compile_model, component
from scpf.compiler import ModelError
from scpf.replay import resolve_value, validate_replay_document, variables_in
from scpf.configurations import _row_variable
from scpf.runner import run_script


class ConfigurationTests(unittest.TestCase):
    def test_named_parameter_rows_and_active(self):
        width = Parameter("width", 80)
        shape = Box(width, 30, 5)
        returned = shape.configure(
            active="Medium",
            columns=(width,),
            rows={
                "Small": ("60 mm",),
                "Medium": ("80 mm",),
                "Large": ("100 mm",),
            },
        )
        self.assertIs(returned, shape)

        commands = compile_model(shape, "Plate")["commands"]
        self.assertEqual(commands[-7]["params"], {"params": ["width"]})
        self.assertEqual(
            commands[-6]["params"],
            {"name": "Default", "rename": "Small"},
        )
        self.assertEqual(
            commands[-3]["params"],
            {"name": "Large", "values": {"param:width": "100 mm"}},
        )
        self.assertEqual(
            commands[-2],
            {
                "command": "config.activate",
                "params": {"row": _row_variable("Medium")},
            },
        )
        self.assertEqual(commands[-1]["command"], "config.table")
        self.assertEqual(
            commands[-6]["bind"][_row_variable("Small")],
            {"field": "rows", "where": {"name": "Small"}, "select": "id"},
        )
        self.assertEqual(
            commands[-4]["bind"][_row_variable("Medium")],
            {"field": "rows", "where": {"name": "Medium"}, "select": "id"},
        )

    def test_feature_binding_uses_direct_feature_handle(self):
        width = Parameter("width", 80)
        plate = Box(width, 30, 5, anchor=Anchor.BOTTOM)
        hole = Hole(d=5).at(0, 0, 5)
        body = plate - hole
        body.configure(
            active="Medium",
            columns=(width, hole),
            rows={
                "Medium": ("80 mm", True),
                "Large": ("100 mm", False),
            },
        )

        doc = compile_model(body, "Plate")
        validate_replay_document(doc)
        feature = next(
            command
            for command in doc["commands"]
            if command["command"] == "solid.hole"
        )
        self.assertEqual(feature["bind"]["$config_name_2"], "name")
        cell = {"suppress:$config_name_2": "true"}
        self.assertEqual(variables_in(cell), {"$config_name_2"})
        self.assertEqual(
            resolve_value(cell, {"$config_name_2": "Hole1"}),
            {"suppress:Hole1": "true"},
        )

    def test_reject_unknown_parameter_and_unapplied_feature(self):
        body = Box(80, 30, 5)
        missing = Parameter("missing", 60)
        body.configure(
            active="A",
            columns=(missing,),
            rows={"A": (60,)},
        )
        with self.assertRaisesRegex(
            ModelError,
            "unknown native configuration parameter",
        ):
            compile_model(body, "Plate")

        second = Box(80, 30, 5)
        second.configure(
            active="A",
            columns=(Hole(d=5),),
            rows={"A": (True,)},
        )
        with self.assertRaisesRegex(ModelError, "already-applied"):
            compile_model(second, "Plate")

    def test_reject_invalid_table(self):
        width = Parameter("width", 80)

        body = Box(width, 30, 5)
        with self.assertRaisesRegex(ValueError, "active configuration"):
            body.configure(
                active="B",
                columns=(width,),
                rows={"A": (60,)},
            )

        body = Box(width, 30, 5)
        with self.assertRaisesRegex(ValueError, "cell count"):
            body.configure(
                active="A",
                columns=(width,),
                rows={"A": ()},
            )

        feature = Hole(d=5).at(0, 0, 5)
        body = Box(80, 30, 5, anchor=Anchor.BOTTOM) - feature
        with self.assertRaisesRegex(TypeError, "suppression cells"):
            body.configure(
                active="A",
                columns=(feature,),
                rows={"A": (1,)},
            )

        body = Box(width, 30, 5)
        with self.assertRaisesRegex(TypeError, "Parameter or authored feature"):
            body.configure(
                active="A",
                columns=("width",),
                rows={"A": (60,)},
            )

    def test_reject_second_configuration(self):
        width = Parameter("width", 80)
        body = Box(width, 30, 5)
        body.configure(
            active="A",
            columns=(width,),
            rows={"A": (80,)},
        )
        with self.assertRaisesRegex(ValueError, "already has a configuration"):
            body.configure(
                active="B",
                columns=(width,),
                rows={"B": (100,)},
            )

    def test_row_replay_identity_is_stable_across_order(self):
        self.assertEqual(_row_variable("Medium"), _row_variable("Medium"))
        self.assertNotEqual(_row_variable("Medium"), _row_variable("Large"))

    def test_configure_can_drive_published_child_parameter_with_parent_size(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.py"
            path.write_text(
                "@component(include=('width',))\n"
                "class FrameBody:\n"
                "    width = 80.0\n"
                "    def build(self):\n"
                "        return Box(self.width, 30, 4, anchor=Anchor.BOTTOM)\n"
                "@component(include=('fit_diameter',))\n"
                "class Clamp:\n"
                "    fit_diameter = 20.0\n"
                "    def build(self):\n"
                "        return Cylinder(d=self.fit_diameter, h=10)\n"
                "class Frame:\n"
                "    frame_width = 80.0\n"
                "    clamp_bore = 20.0\n"
                "    def build(self):\n"
                "        body = FrameBody(width=self.frame_width, name='frame')\n"
                "        left = Clamp(fit_diameter=self.clamp_bore, name='left')\n"
                "        right = left.copy(\n"
                "            name='right', placement=Placement(x=40)\n"
                "        )\n"
                "        model = body + left + right\n"
                "        model.configure(\n"
                "            active='Medium',\n"
                "            columns=(self.frame_width, self.clamp_bore),\n"
                "            rows={\n"
                "                'Small': ('60 mm', '19.8 mm'),\n"
                "                'Medium': ('80 mm', '20.0 mm'),\n"
                "                'Large': ('100 mm', '20.2 mm'),\n"
                "            },\n"
                "        )\n"
                "        return model\n"
                "Frame()\n",
                encoding="utf-8",
            )
            document = run_script(path)

        commands = document["commands"]
        configure = next(
            row for row in commands if row["command"] == "config.configure"
        )
        self.assertEqual(
            configure["params"],
            {"params": ["frame_width", "clamp_bore"]},
        )
        self.assertEqual(
            [
                row["params"]["name"]
                for row in commands
                if row["command"] == "parameters.add"
            ].count("clamp_bore"),
            1,
        )
        clamp = next(
            row
            for row in commands
            if row["command"] == "solid.cylinder"
        )
        self.assertEqual(clamp["params"]["diameter"], "clamp_bore")
        large = next(
            row
            for row in commands
            if row["command"] == "config.row"
            and row["params"].get("name") == "Large"
        )
        self.assertEqual(
            large["params"]["values"],
            {
                "param:frame_width": "100 mm",
                "param:clamp_bore": "20.2 mm",
            },
        )

    def test_parent_configure_suppresses_exported_child_feature_by_definition(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.py"
            path.write_text(
                "@component(include=('width',))\n"
                "class Coupler:\n"
                "    width = 40.0\n"
                "    def build(self):\n"
                "        body = Box(self.width, 20, 10, anchor=Anchor.BOTTOM)\n"
                "        panel_pin = Hole(d=5).at(0, 0, 10).export_feature('panel_pin')\n"
                "        return body - panel_pin\n"
                "class Frame:\n"
                "    coupler_width = 40.0\n"
                "    def build(self):\n"
                "        left = Coupler(width=self.coupler_width, name='left')\n"
                "        right = left.copy(\n"
                "            name='right', placement=Placement(x=60)\n"
                "        )\n"
                "        model = left + right\n"
                "        model.configure(\n"
                "            active='Medium',\n"
                "            columns=(\n"
                "                self.coupler_width,\n"
                "                right.feature('panel_pin'),\n"
                "            ),\n"
                "            rows={\n"
                "                'Small': ('30 mm', True),\n"
                "                'Medium': ('40 mm', True),\n"
                "                'Large': ('50 mm', False),\n"
                "            },\n"
                "        )\n"
                "        return model\n"
                "Frame()\n",
                encoding="utf-8",
            )
            document = run_script(path)

        commands = document["commands"]
        configure = next(
            row for row in commands if row["command"] == "config.configure"
        )
        self.assertEqual(configure["params"]["params"], ["coupler_width"])
        self.assertEqual(configure["params"]["features"], ["$config_name_2"])

        holes = [
            row for row in commands if row["command"] == "solid.hole"
        ]
        self.assertEqual(len(holes), 1)
        self.assertEqual(holes[0]["bind"]["$config_name_2"], "name")

        large = next(
            row
            for row in commands
            if row["command"] == "config.row"
            and row["params"].get("name") == "Large"
        )
        self.assertEqual(
            large["params"]["values"],
            {
                "param:coupler_width": "50 mm",
                "suppress:$config_name_2": "false",
            },
        )

    def test_component_feature_reference_requires_explicit_export(self):
        @component
        class Coupler:
            def build(self):
                return Box(40, 20, 10)

        instance = Coupler()
        with self.assertRaisesRegex(
            ValueError,
            "no exported component feature",
        ):
            instance.feature("panel_pin")

    def test_reusable_component_cannot_own_configuration(self):
        @component
        class BadComponent:
            width = 40.0

            def build(self):
                body = Box(self.width, 20, 10)
                body.configure(
                    active="A",
                    columns=(self.width,),
                    rows={"A": ("40 mm",)},
                )
                return body

        with self.assertRaisesRegex(
            TypeError,
            "cannot own final-model configuration",
        ):
            BadComponent()

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
                "        plate = FrontPlate(\n"
                "            name='front_plate',\n"
                "            placement=Placement(y=self.plate_y, z=self.plate_z),\n"
                "        )\n"
                "        model = screen + plate\n"
                "        model.configure(\n"
                "            active='Front',\n"
                "            columns=(self.plate_y, self.plate_z),\n"
                "            rows={\n"
                "                'Front': ('8 mm', '0 mm'),\n"
                "                'Below': ('0 mm', '-55 mm'),\n"
                "                'Service': ('25 mm', '0 mm'),\n"
                "            },\n"
                "        )\n"
                "        return model\n"
                "Display()\n",
                encoding="utf-8",
            )
            document = run_script(path)

        commands = document["commands"]
        move = next(
            row for row in commands if row["command"] == "occurrence.move"
        )
        self.assertEqual(
            move["params"]["translate"][1:],
            ["plate_y", "plate_z"],
        )
        configure = next(
            row for row in commands if row["command"] == "config.configure"
        )
        self.assertEqual(
            configure["params"],
            {"params": ["plate_y", "plate_z"]},
        )
        self.assertEqual(
            next(
                row
                for row in commands
                if row["command"] == "config.activate"
            )["params"],
            {"row": _row_variable("Front")},
        )


if __name__ == "__main__":
    unittest.main()
