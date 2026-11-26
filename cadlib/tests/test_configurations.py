"""Configuration-table authoring and replay identity tests."""
import tempfile
import unittest
from pathlib import Path

from scpf import (
    Always, Anchor, Box, ConfigRule, Configure, DriveParameter, Hole, Param,
    Parameter, Suppress, compile_model, component,
)
from scpf.compiler import ModelError
from scpf.replay import resolve_value, validate_replay_document, variables_in
from scpf.configurations import _row_variable
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
        self.assertEqual(
            commands[-2],
            {"command": "config.activate", "params": {"row": _row_variable("Medium")}},
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

    def test_enabled_rule_drives_configured_parameter_after_rows(self):
        size = Parameter("size", 80)
        tube_d = Parameter("tube_d", 20)
        fit_diameter = Parameter("fit_diameter", 20.4)
        shape = Box(size, tube_d, fit_diameter)
        design = Configure(
            shape,
            active="Medium",
            columns=(Param(size), Param(fit_diameter)),
            rows={
                "Small": ("60 mm", "20.4 mm"),
                "Medium": ("80 mm", "20.4 mm"),
                "Large": ("100 mm", "20.4 mm"),
            },
            rules=(
                ConfigRule(
                    "installed",
                    "Installed",
                    enabled=True,
                    condition=Always(),
                    effect=DriveParameter(fit_diameter, tube_d),
                ),
            ),
        )

        commands = compile_model(design, "RulePlate")["commands"]
        rule = next(row for row in commands if row["command"] == "config.rule")
        self.assertEqual(
            rule["params"],
            {
                "rule": {
                    "id": "installed",
                    "name": "Installed",
                    "enabled": True,
                    "condition": {"type": "always"},
                    "effect": {
                        "type": "drive_parameter",
                        "parameter": "fit_diameter",
                        "expression": "tube_d",
                    },
                },
            },
        )
        rule_index = commands.index(rule)
        activate_index = next(
            i for i, row in enumerate(commands)
            if row["command"] == "config.activate"
        )
        self.assertLess(rule_index, activate_index)

    def test_rule_can_be_authored_disabled(self):
        fit = Parameter("fit", 20.4)
        shape = Box(40, 30, fit)
        design = Configure(
            shape,
            active="Medium",
            columns=(Param(fit),),
            rows={"Medium": ("20.4 mm",)},
            rules=(
                ConfigRule(
                    "installed",
                    "Installed",
                    enabled=False,
                    condition=Always(),
                    effect=DriveParameter(fit, 20.0),
                ),
            ),
        )
        command = next(
            row for row in compile_model(design, "Fit")["commands"]
            if row["command"] == "config.rule"
        )
        self.assertFalse(command["params"]["rule"]["enabled"])

    def test_rule_requires_configured_parameter_target(self):
        fit = Parameter("fit", 20.4)
        other = Parameter("other", 20.0)
        shape = Box(40, fit, other)
        with self.assertRaisesRegex(ValueError, "also be a Param"):
            Configure(
                shape,
                active="Medium",
                columns=(Param(fit),),
                rows={"Medium": ("20.4 mm",)},
                rules=(
                    ConfigRule(
                        "installed",
                        "Installed",
                        condition=Always(),
                        effect=DriveParameter(other, 20.0),
                    ),
                ),
            )

    def test_rule_rejects_untyped_condition_and_effect(self):
        with self.assertRaisesRegex(TypeError, "condition must use Always"):
            ConfigRule(
                "installed",
                "Installed",
                condition="always",
                effect=DriveParameter("fit", 20.0),
            )
        with self.assertRaisesRegex(TypeError, "effect must use DriveParameter"):
            ConfigRule(
                "installed",
                "Installed",
                condition=Always(),
                effect="fit",
            )

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
                "        return Configure(\n"
                "            body + left + right, active='Medium',\n"
                "            columns=(Param(self.frame_width), Param(self.clamp_bore)),\n"
                "            rows={\n"
                "                'Small': ('60 mm', '19.8 mm'),\n"
                "                'Medium': ('80 mm', '20.0 mm'),\n"
                "                'Large': ('100 mm', '20.2 mm'),\n"
                "            },\n"
                "        )\n"
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
            row for row in commands
            if row["command"] == "solid.cylinder"
        )
        self.assertEqual(clamp["params"]["diameter"], "clamp_bore")
        large = next(
            row for row in commands
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

    def test_rule_drives_published_child_parameter_with_size_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.py"
            path.write_text(
                "@component(include=('tube_d', 'fit_diameter'))\n"
                "class Clamp:\n"
                "    tube_d = 20.0\n"
                "    fit_diameter = 20.4\n"
                "    def build(self):\n"
                "        return Cylinder(d=self.tube_d + 4, h=10) - Cylinder(d=self.fit_diameter, h=12)\n"
                "class Frame:\n"
                "    frame_width = 80.0\n"
                "    tube_d = 20.0\n"
                "    clamp_bore = 20.4\n"
                "    def build(self):\n"
                "        left = Clamp(\n"
                "            tube_d=self.tube_d, fit_diameter=self.clamp_bore, name='left',\n"
                "            placement=Placement(x=-self.frame_width / 4),\n"
                "        )\n"
                "        right = left.copy(\n"
                "            name='right',\n"
                "            placement=Placement(x=self.frame_width / 4),\n"
                "        )\n"
                "        return Configure(\n"
                "            left + right, active='Medium',\n"
                "            columns=(Param(self.frame_width), Param(self.clamp_bore)),\n"
                "            rows={\n"
                "                'Small': ('60 mm', '20.4 mm'),\n"
                "                'Medium': ('80 mm', '20.4 mm'),\n"
                "                'Large': ('100 mm', '20.4 mm'),\n"
                "            },\n"
                "            rules=(\n"
                "                ConfigRule(\n"
                "                    'installed', 'Installed', enabled=True,\n"
                "                    condition=Always(),\n"
                "                    effect=DriveParameter(self.clamp_bore, self.tube_d),\n"
                "                ),\n"
                "            ),\n"
                "        )\n"
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
        rule = next(row for row in commands if row["command"] == "config.rule")
        self.assertEqual(rule["params"]["rule"]["id"], "installed")
        self.assertTrue(rule["params"]["rule"]["enabled"])
        self.assertEqual(
            rule["params"]["rule"]["effect"],
            {
                "type": "drive_parameter",
                "parameter": "clamp_bore",
                "expression": "tube_d",
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
                "        right = Coupler(\n"
                "            width=self.coupler_width, name='right',\n"
                "            placement=Placement(x=60),\n"
                "        )\n"
                "        return Configure(\n"
                "            left + right, active='Medium',\n"
                "            columns=(\n"
                "                Param(self.coupler_width),\n"
                "                Suppress(right.feature('panel_pin')),\n"
                "            ),\n"
                "            rows={\n"
                "                'Small': ('30 mm', True),\n"
                "                'Medium': ('40 mm', True),\n"
                "                'Large': ('50 mm', False),\n"
                "            },\n"
                "        )\n"
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

        holes = [row for row in commands if row["command"] == "solid.hole"]
        self.assertEqual(len(holes), 1)
        self.assertEqual(holes[0]["bind"]["$config_name_2"], "name")

        large = next(
            row for row in commands
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
        with self.assertRaisesRegex(ValueError, "no exported component feature"):
            instance.feature("panel_pin")

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
            {"row": _row_variable("Front")},
        )


if __name__ == "__main__":
    unittest.main()
