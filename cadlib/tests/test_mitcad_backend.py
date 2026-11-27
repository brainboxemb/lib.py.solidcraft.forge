"""Feasibility contracts for the experimental Mitcad backend."""

from pathlib import Path
import unittest

from scpf import Anchor, Axis, Box, Cone, Cylinder, Sphere
from scpf.backends.mitcad import compile_ir, compile_model
from scpf.compiler import ModelError
from scpf.ir import normalize_model
from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]
SIMPLE_BOX = ROOT / "models/simple-box/scpf/model.py"
NEGATIVE_CIRCLE = ROOT / "models/circle-negative-extrude/scpf/model.py"
TOPOLOGY_BOX = ROOT / "models/topology-face-boundary-box/scpf/model.py"
NATIVE_REVOLVE = ROOT / "models/native-revolve/scpf/model.py"
CYLINDER_SUBTRACT = ROOT / "models/cylinder-subtract/scpf/model.py"
CONFIGURATION_TABLE = ROOT / "models/configuration-table/scpf/model.py"
SHIFTED_AXIS_REVOLVE = ROOT / "models/shifted-axis-revolve/scpf/model.py"


class MitcadBackendTests(unittest.TestCase):
    def test_simple_box_source_is_unchanged_across_backends(self):
        solidcraft = run_script(SIMPLE_BOX)
        mitcad = run_script(SIMPLE_BOX, backend="mitcad")

        self.assertEqual(
            [row["command"] for row in solidcraft["commands"] if row["command"] != "parameters.add"],
            ["solid.box"],
        )
        self.assertEqual(mitcad["format"], "scpf-mitcad")
        self.assertEqual(mitcad["backend"], "mitcad")
        self.assertEqual(
            [row["cmd"] for row in mitcad["commands"]],
            ["add_parameter", "add_parameter", "add_parameter", "add_feature"],
        )

        feature = mitcad["commands"][-1]
        self.assertEqual(feature["name"], "SimpleBox")
        self.assertEqual(
            feature["def"],
            {
                "type": "box",
                "plane": "xy",
                "corner": ["-(length / 2)", "-(width / 2)"],
                "length": "length",
                "width": "width",
                "height": "height",
                "symmetric": False,
                "operation": "new_body",
                "participants": [],
            },
        )

    def test_negative_circle_extrude_is_native_sketch_plus_extrude(self):
        document = run_script(NEGATIVE_CIRCLE, backend="mitcad")
        self.assertEqual(
            [row["cmd"] for row in document["commands"]],
            [
                "add_parameter",
                "add_parameter",
                "add_feature",
                "add_feature",
            ],
        )
        sketch = document["commands"][-2]
        self.assertEqual(sketch["name"], "Profile")
        self.assertEqual(sketch["def"]["type"], "sketch")
        self.assertEqual(sketch["def"]["plane"], "xy")
        self.assertEqual(sketch["def"]["entities"][1]["type"], "circle")
        self.assertEqual(sketch["def"]["entities"][1]["radius"], 10.0)
        self.assertEqual(
            sketch["def"]["dimensions"],
            [
                {
                    "id": "k1",
                    "type": "diameter",
                    "curve": "c2",
                    "value": "diameter",
                }
            ],
        )

        extrusion = document["commands"][-1]
        self.assertEqual(extrusion["name"], "NegativeCircleExtrude")
        self.assertEqual(extrusion["def"]["type"], "extrude")
        self.assertEqual(
            extrusion["def"]["profiles"],
            [{"sketch": {"ref": "sk.uid"}, "point": [0, 0]}],
        )
        distance = str(extrusion["def"]["extent"]["distance"])
        self.assertTrue(distance.startswith("-("))
        self.assertIn("height", distance)
        self.assertEqual(extrusion["def"]["operation"], "new_body")


    def test_native_revolve_source_lowers_to_native_mitcad_revolve(self):
        document = run_script(NATIVE_REVOLVE, backend="mitcad")
        self.assertEqual(
            [row["cmd"] for row in document["commands"]],
            [
                "add_parameter",
                "add_parameter",
                "add_parameter",
                "add_feature",
                "add_feature",
            ],
        )
        self.assertEqual(
            [(row["name"], row["unit"]) for row in document["commands"][:3]],
            [
                ("radius", "mm"),
                ("length", "mm"),
                ("sweep", "deg"),
            ],
        )
        self.assertNotIn("value", document["commands"][2])
        self.assertEqual(
            document["commands"][2]["expression"],
            "360 deg",
        )
        sketch = document["commands"][-2]["def"]
        revolve = document["commands"][-1]["def"]
        self.assertEqual(sketch["type"], "sketch")
        self.assertEqual(
            [row["type"] for row in sketch["entities"]],
            [
                "point", "point", "point", "point",
                "line", "line", "line", "line",
            ],
        )
        self.assertEqual(
            [row["type"] for row in sketch["constraints"]],
            ["vertical", "horizontal", "vertical", "horizontal"],
        )
        self.assertEqual(
            [row["value"] for row in sketch["dimensions"]],
            ["radius", "length"],
        )
        self.assertEqual(
            [(row["type"], row["line"]) for row in sketch["dimensions"]],
            [("length", "c5"), ("length", "c6")],
        )
        self.assertEqual(revolve["type"], "revolve")
        self.assertEqual(revolve["axis"], "x")
        self.assertEqual(
            revolve["extent"],
            {"type": "angle", "angle": "sweep"},
        )
        self.assertEqual(revolve["operation"], "new_body")

    def test_face_boundary_chamfer_uses_native_filter_and_runtime_body_binding(self):
        document = run_script(TOPOLOGY_BOX, backend="mitcad")
        self.assertEqual([row["cmd"] for row in document["commands"]], ["add_feature"])
        self.assertEqual(len(document["replay"]), 1)
        stage = document["replay"][0]
        self.assertEqual(stage["bind_single_body"], "body")
        definition = stage["commands"][0]["def"]
        self.assertEqual(definition["type"], "chamfer")
        self.assertEqual(definition["body"], {"$mitcad_bind": "body"})
        self.assertEqual(
            stage["bind_face_boundary_edges"],
            {
                "name": "edges",
                "body": "body",
                "face": {
                    "surface": "plane",
                    "normal": [0, 0, 1],
                    "normal_tolerance": 1e-06,
                },
            },
        )
        self.assertEqual(
            definition["edges"],
            {"$mitcad_bind": "edges"},
        )
        self.assertEqual(
            definition["size"],
            {"type": "equal_distance", "distance": 2},
        )

    def test_cylinder_subtract_uses_native_cylinder_cut_without_body_ids(self):
        solidcraft = run_script(CYLINDER_SUBTRACT)
        document = run_script(CYLINDER_SUBTRACT, backend="mitcad")

        self.assertEqual(
            [
                row["command"]
                for row in solidcraft["commands"]
                if row["command"].startswith("solid.")
            ],
            ["solid.box", "solid.cylinder"],
        )
        features = [
            row["def"]
            for row in document["commands"]
            if row["cmd"] == "add_feature"
        ]
        self.assertEqual(
            [feature["type"] for feature in features],
            ["box", "cylinder"],
        )
        self.assertEqual(features[0]["operation"], "new_body")
        self.assertEqual(features[1]["operation"], "cut")
        self.assertEqual(features[1]["participants"], [])
        self.assertEqual(features[1]["center"], ["bore_x", "bore_y"])
        self.assertFalse(any(
            isinstance(value, str) and value.startswith("F")
            for feature in features
            for value in feature.values()
        ))

    def test_centered_box_uses_native_mitcad_symmetric_height(self):
        document = compile_model(
            Box(40, 30, 10, anchor=Anchor.CENTER),
            "CenteredBox",
        )
        feature = document["commands"][-1]["def"]
        self.assertEqual(feature["corner"], [-20.0, -15.0])
        self.assertTrue(feature["symmetric"])

    def test_axial_primitive_offset_fails_closed_until_qualified(self):
        with self.assertRaisesRegex(
            ModelError,
            "axial coordinate on the origin plane",
        ):
            compile_model(
                Cylinder(d=10, h=20).at(8, -5, 3),
                "AxiallyOffsetCylinder",
            )

    def test_cone_boolean_uses_native_csg_operation(self):
        document = compile_model(
            Cone(
                d=10,
                h=20,
                anchor=Anchor.BOTTOM,
            )
            + Box(10, 10, 10, anchor=Anchor.BOTTOM),
            "ConeBooleanTest",
        )
        features = [
            row["def"]
            for row in document["commands"]
            if row["cmd"] == "add_feature"
        ]
        self.assertEqual(
            [feature["type"] for feature in features],
            ["cone", "box"],
        )
        self.assertEqual(features[0]["operation"], "new_body")
        self.assertEqual(features[1]["operation"], "join")

    def test_shifted_axis_configuration_lowers_semantic_feature_identity(self):
        document = run_script(SHIFTED_AXIS_REVOLVE, backend="mitcad")

        self.assertEqual(document["format"], "scpf-mitcad")
        self.assertEqual(len(document["replay"]), 1)
        stage = document["replay"][0]
        self.assertEqual(stage["bind_single_body"], "body")

        commands = stage["commands"]
        revolve = next(
            row
            for row in commands
            if row.get("cmd") == "add_feature"
            and row.get("def", {}).get("type") == "revolve"
        )
        self.assertEqual(revolve["as"], "configured_feature")
        self.assertEqual(revolve["def"]["operation"], "cut")

        sketch = next(
            row
            for row in commands
            if row.get("cmd") == "add_feature"
            and row.get("def", {}).get("type") == "sketch"
        )["def"]
        dimension_values = [
            str(row.get("value"))
            for row in sketch["dimensions"]
        ]
        self.assertTrue(any("axis_x" in value for value in dimension_values))
        self.assertTrue(any("relief_d" in value for value in dimension_values))
        self.assertTrue(any("core_d" in value for value in dimension_values))

        private = next(
            row["name"]
            for row in commands
            if row.get("cmd") == "add_parameter"
            and row.get("name", "").startswith("__forge_suppress_root")
        )
        self.assertNotIn(
            private,
            [row.get("name") for row in document["commands"]],
        )

        table = next(
            row["configurations"]
            for row in commands
            if row.get("cmd") == "set_configurations"
        )
        self.assertEqual(table["default"], "Cut")
        self.assertEqual(
            [row["name"] for row in table["rows"]],
            ["Cut", "Suppressed"],
        )
        self.assertEqual(table["parameters"], [private])

        suppression = next(
            row for row in commands
            if row.get("cmd") == "suppress_feature"
        )
        self.assertEqual(
            suppression["uid"],
            {"ref": "configured_feature.uid"},
        )
        self.assertEqual(
            suppression["expression"],
            f"{private} > 0",
        )
        self.assertEqual(
            commands[-1],
            {"cmd": "apply_configuration", "name": "Cut"},
        )

    def test_nested_boolean_configuration_binds_semantic_feature_result(self):
        sphere = Sphere(20)
        extension = Box(30, 30, 20).move(x=18, z=10)
        joined = sphere + extension
        bore = Cylinder(d=8, h=60, axis=Axis.X)
        cut = joined - bore
        clip = Box(50, 50, 30).move(z=15)
        design = cut & clip

        configured = design.configure(
            active="Clipped",
            columns=(clip,),
            rows={"Clipped": (False,), "Unclipped": (True,)},
        )
        document = compile_ir(
            normalize_model(configured),
            "PrimitiveCsgConfigured",
        )
        features = [
            row for row in document["commands"]
            if row.get("cmd") == "add_feature"
        ]
        self.assertEqual(
            [row["def"]["operation"] for row in features],
            ["new_body", "join", "cut", "intersect"],
        )
        bound = [row for row in features if row.get("as") == "configured_feature"]
        self.assertEqual(len(bound), 1)
        self.assertEqual(bound[0]["def"]["operation"], "intersect")

        suppression = next(
            row for row in document["commands"]
            if row.get("cmd") == "suppress_feature"
        )
        self.assertEqual(
            suppression["uid"],
            {"ref": "configured_feature.uid"},
        )
        self.assertEqual(document["commands"][-1], {
            "cmd": "apply_configuration",
            "name": "Clipped",
        })

        bore_design = type(design)(design.kind, design.data)
        bore_configured = bore_design.configure(
            active="Bored",
            columns=(bore,),
            rows={"Bored": (False,), "Solid": (True,)},
        )
        bore_document = compile_ir(
            normalize_model(bore_configured),
            "PrimitiveCsgBoreConfigured",
        )
        bore_features = [
            row for row in bore_document["commands"]
            if row.get("cmd") == "add_feature"
        ]
        bore_bound = [
            row for row in bore_features
            if row.get("as") == "configured_feature"
        ]
        self.assertEqual(len(bore_bound), 1)
        self.assertEqual(bore_bound[0]["def"]["type"], "cylinder")
        self.assertEqual(bore_bound[0]["def"]["operation"], "cut")

    def test_configuration_table_fails_closed_on_mitcad(self):
        with self.assertRaisesRegex(
            ModelError,
            "does not support Forge configurations",
        ):
            run_script(CONFIGURATION_TABLE, backend="mitcad")

    def test_unknown_runner_backend_is_rejected_before_model_execution(self):
        with self.assertRaisesRegex(ValueError, "unknown SCPF backend"):
            run_script(SIMPLE_BOX, backend="unknown")


if __name__ == "__main__":
    unittest.main()
