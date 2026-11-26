"""Feasibility contracts for the experimental Mitcad backend."""

from pathlib import Path
import unittest

from scpf import Anchor, Box
from scpf.backends.mitcad import compile_model
from scpf.compiler import ModelError
from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]
SIMPLE_BOX = ROOT / "models/simple-box/scpf/model.py"
NEGATIVE_CIRCLE = ROOT / "models/circle-negative-extrude/scpf/model.py"
TOPOLOGY_BOX = ROOT / "models/topology-face-boundary-box/scpf/model.py"


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
            definition["faces"],
            {
                "surface": "plane",
                "normal": [0, 0, 1],
                "normal_tolerance": 1e-06,
            },
        )
        self.assertEqual(
            definition["size"],
            {"type": "equal_distance", "distance": 2},
        )

    def test_centered_box_uses_native_mitcad_symmetric_height(self):
        document = compile_model(
            Box(40, 30, 10, anchor=Anchor.CENTER),
            "CenteredBox",
        )
        feature = document["commands"][-1]["def"]
        self.assertEqual(feature["corner"], [-20.0, -15.0])
        self.assertTrue(feature["symmetric"])

    def test_unsupported_shape_fails_explicitly(self):
        with self.assertRaisesRegex(
            ModelError,
            "does not yet support Forge shape kind 'cylinder'",
        ):
            from scpf import Cylinder
            compile_model(Cylinder(d=10, h=20), "CylinderTest")

    def test_unknown_runner_backend_is_rejected_before_model_execution(self):
        with self.assertRaisesRegex(ValueError, "unknown SCPF backend"):
            run_script(SIMPLE_BOX, backend="unknown")


if __name__ == "__main__":
    unittest.main()
