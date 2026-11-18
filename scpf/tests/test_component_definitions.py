"""Reusable model objects and native SolidCraft assembly command tests."""
from pathlib import Path
import tempfile
import unittest

from scpf.runner import run_script
from scpf.model_objects import Placement

ROOT = Path(__file__).resolve().parents[2]

class ComponentDefinitionTests(unittest.TestCase):
    def test_explicit_imported_component_factory(self):
        # The library's scpf/ source folder is a namespace root when the
        # test runner executes from the repository root. Import the module
        # directly here; the external-package public import is checked in CI.
        from scpf.runner import component
        from scpf.model_objects import ModelInstance

        class LibraryPanel:
            width = 20

            def build(self):
                from scpf.core import Box
                return Box(self.width, 10, 2)

        Panel = component(LibraryPanel)
        first = Panel()
        second = Panel(placement=Placement(x=20))
        self.assertIsInstance(first, ModelInstance)
        self.assertIsInstance(second, ModelInstance)
        self.assertEqual(first.definition.key, second.definition.key)
        self.assertEqual(second.placement.position, (20, 0, 0))
        with self.assertRaisesRegex(TypeError, "model class"):
            component(42)

    def test_different_model_parameters_create_independent_component_definitions(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "model.py"
            file.write_text(
                "class Block:\n"
                "    length = 40.0\n"
                "    width = 30.0\n"
                "    height = 10.0\n"
                "    def build(self):\n"
                "        Box(self.length, self.width, self.height)\n"
                "class Pair:\n"
                "    def build(self):\n"
                "        left = Block(width=30.0)\n"
                "        right = Block(width=50.0)\n"
                "        left + right\n"
                "Pair()\n"
            )
            commands = run_script(file)["commands"]

        self.assertEqual(
            [c["params"]["name"] for c in commands
             if c["command"] == "component.create"],
            ["Block", "Block 2"],
        )
        self.assertFalse(any(c["command"] == "occurrence.copy" for c in commands))
        parameter_names = [
            c["params"]["name"] for c in commands
            if c["command"] == "parameters.add"
        ]
        self.assertEqual(parameter_names, [])

    def test_conflicting_inherited_defaults_do_not_share_one_definition(self):
        from scpf import Box, Parameter
        from scpf.assembly import compile_assembly
        from scpf.compiler import ModelError
        from scpf.runner import component

        class Panel:
            width = 100.0

            def build(self):
                return Box(self.width, 10, 2)

        PanelObject = component(Panel)
        first = PanelObject(width=Parameter("opening_width", 800))
        second = PanelObject(width=Parameter("opening_width", 900))

        self.assertNotEqual(
            first.definition.key,
            second.definition.key,
        )
        with self.assertRaisesRegex(
            ModelError,
            "conflicting inherited parameter opening_width",
        ):
            compile_assembly(first + second, "Display")

    def test_dataclass_fixed_variants_are_part_of_definition_identity(self):
        from dataclasses import dataclass

        from scpf import Axis, Box
        from scpf.runner import component

        @dataclass
        class VariantPart:
            enabled: object = True
            label: str = "wide"
            axis: Axis = Axis.X
            optional: object = None
            options: tuple = ("outer", True, None, (1, "mm"))

            def build(self):
                length = 20 if self.enabled is True else 10
                width = 30 if self.label == "wide" else 15
                height = 8 if self.axis is Axis.X else 12
                return Box(length, width, height)

        Part = component(VariantPart)
        variants = [
            Part(),
            Part(enabled=False),
            Part(enabled=1),
            Part(label="narrow"),
            Part(axis=Axis.Y),
            Part(optional="present"),
            Part(options=("inner", False, None, (2, "mm"))),
        ]

        keys = {part.definition.key for part in variants}
        self.assertEqual(len(keys), len(variants))

        fixed = dict(variants[0].definition.fixed_inputs)
        self.assertEqual(fixed["enabled"], ("bool", True))
        self.assertEqual(fixed["label"], ("str", "wide"))
        self.assertEqual(fixed["optional"], ("none",))
        self.assertEqual(fixed["axis"][-1], "X")
        self.assertEqual(fixed["options"][0], "tuple")

    def test_forge_selector_values_are_safe_definition_identity_inputs(self):
        from scpf import BOTTOM, LEFT, RIGHT, TOP, Edges, X, Box
        from scpf.runner import component

        class SelectorPart:
            selector = None

            def build(self):
                return Box(20, 10, 5)

        Part = component(SelectorPart)

        lower_left = Part(selector=BOTTOM + LEFT)
        lower_left_again = Part(selector=BOTTOM + LEFT)
        lower_right = Part(selector=BOTTOM + RIGHT)
        upper_left = Part(selector=TOP + LEFT)

        self.assertEqual(
            lower_left.definition.key,
            lower_left_again.definition.key,
        )
        self.assertNotEqual(
            lower_left.definition.key,
            lower_right.definition.key,
        )
        self.assertNotEqual(
            lower_left.definition.key,
            upper_left.definition.key,
        )
        self.assertEqual(
            dict(lower_left.definition.fixed_inputs)["selector"],
            ("direction_selector", (-1, 0, -1)),
        )

        profile_a = Part(selector=Edges.from_profile("a"))
        profile_b = Part(selector=Edges.from_profile("b"))
        self.assertNotEqual(profile_a.definition.key, profile_b.definition.key)
        self.assertEqual(
            dict(profile_a.definition.fixed_inputs)["selector"][:2],
            ("profile_edge_selection", ("a",)),
        )

        axis_token = Part(selector=X)
        text_token = Part(selector="X")
        self.assertNotEqual(axis_token.definition.key, text_token.definition.key)

        near_left = Part(selector=X.MIN + 10)
        far_left = Part(selector=X.MIN + 20)
        self.assertNotEqual(near_left.definition.key, far_left.definition.key)
        self.assertEqual(
            dict(near_left.definition.fixed_inputs)["selector"],
            ("bound_offset", "X", "min", ("number", 10.0)),
        )

    def test_board_style_selector_tuple_is_reusable_definition_input(self):
        from scpf import BOTTOM, LEFT, RIGHT, TOP, Box
        from scpf.assembly import compile_assembly
        from scpf.runner import component

        class Board:
            fillet = None

            def build(self):
                body = Box(40, 20, 5)
                if self.fillet:
                    body = body.fillet(2, edges=self.fillet)
                return body

        BoardPart = component(Board)
        bottom = BoardPart(
            fillet=(BOTTOM + LEFT, BOTTOM + RIGHT),
        )
        same_bottom = BoardPart(
            fillet=(BOTTOM + LEFT, BOTTOM + RIGHT),
        )
        top = BoardPart(
            fillet=(TOP + LEFT, TOP + RIGHT),
        )

        self.assertEqual(bottom.definition.key, same_bottom.definition.key)
        self.assertNotEqual(bottom.definition.key, top.definition.key)

        commands = compile_assembly(bottom + same_bottom, "Boards")["commands"]
        self.assertEqual(
            sum(row["command"] == "component.create" for row in commands),
            1,
        )
        self.assertEqual(
            sum(row["command"] == "occurrence.copy" for row in commands),
            1,
        )

    def test_reusable_dataclass_rejects_unstable_fixed_input(self):
        from dataclasses import dataclass, field

        from scpf import Box
        from scpf.runner import component

        @dataclass
        class VariantPart:
            profile: list = field(default_factory=lambda: [20, 10])

            def build(self):
                return Box(self.profile[0], self.profile[1], 5)

        Part = component(VariantPart)
        with self.assertRaisesRegex(
            TypeError,
            "profile.*list.*definition identity",
        ):
            Part(profile=[30, 10])

    def test_plain_none_input_uses_fixed_identity_when_reused(self):
        from scpf import Box
        from scpf.runner import component

        class Variant:
            profile = None

            def build(self):
                return Box(20 if self.profile == "wide" else 10, 10, 5)

        Part = component(Variant)
        wide = Part(profile="wide")
        narrow = Part(profile="narrow")

        self.assertNotEqual(wide.definition.key, narrow.definition.key)
        self.assertEqual(
            dict(wide.definition.fixed_inputs)["profile"],
            ("str", "wide"),
        )

    def test_plain_reusable_component_rejects_arbitrary_object_input(self):
        from scpf import Box
        from scpf.runner import component

        class Variant:
            profile = None

            def build(self):
                return Box(10, 10, 5)

        Part = component(Variant)
        with self.assertRaisesRegex(
            TypeError,
            "profile.*object.*definition identity",
        ):
            Part(profile=object())

    def test_definition_number_prevents_parameter_namespace_slug_collision(self):
        from scpf import Box
        from scpf.assembly import compile_assembly
        from scpf.runner import component

        class Foo:
            width = 10.0

            def build(self):
                return Box(self.width, 10, 2)

        class Foo_2:
            width = 30.0

            def build(self):
                return Box(self.width, 10, 2)

        FooObject = component(Foo, include=("width",))
        Foo2Object = component(Foo_2, include=("width",))

        commands = compile_assembly(
            FooObject(width=10)
            + FooObject(width=20)
            + Foo2Object(width=30),
            "Display",
        )["commands"]

        parameter_names = [
            command["params"]["name"]
            for command in commands
            if command["command"] == "parameters.add"
        ]
        self.assertEqual(
            parameter_names,
            [
                "d1_Foo_width",
                "d2_Foo_2_width",
                "d3_Foo_2_width",
            ],
        )
        self.assertEqual(len(parameter_names), len(set(parameter_names)))

    def test_parameter_namespacing_does_not_rewrite_plain_strings(self):
        from scpf.assembly import _namespace_commands
        from scpf.core import _native_dependencies, _native_expression

        commands = [
            {
                "command": "parameters.add",
                "params": {
                    "name": "width",
                    "expression": "40",
                    "unit": "mm",
                },
            },
            {
                "command": "sketch.text",
                "params": {
                    "text": "width",
                    "font": "width",
                    "name": "width label",
                    "height": _native_expression("width / 4", ("width",)),
                },
            },
            {
                "command": "material.create",
                "params": {
                    "name": "width",
                    "density_g_cm3": 1.0,
                },
            },
            {
                "command": "solid.box",
                "params": {
                    "length": _native_expression("width", ("width",)),
                    "body_name": "width",
                },
            },
        ]

        namespaced = _namespace_commands(
            commands,
            "Label",
            definition_number=1,
        )

        self.assertEqual(
            namespaced[0]["params"]["name"],
            "d1_Label_width",
        )
        self.assertEqual(
            namespaced[1]["params"]["height"],
            "d1_Label_width / 4",
        )
        self.assertEqual(
            namespaced[1]["params"]["text"],
            "width",
        )
        self.assertEqual(
            namespaced[1]["params"]["font"],
            "width",
        )
        self.assertEqual(
            namespaced[1]["params"]["name"],
            "width label",
        )
        self.assertEqual(
            namespaced[2]["params"]["name"],
            "width",
        )
        self.assertEqual(
            namespaced[3]["params"]["length"],
            "d1_Label_width",
        )
        self.assertEqual(
            _native_dependencies(namespaced),
            frozenset({"d1_Label_width"}),
        )
        self.assertEqual(
            namespaced[3]["params"]["body_name"],
            "width",
        )

    def test_component_namespacing_preserves_and_rewrites_replay_bindings(self):
        from scpf.assembly import _namespace_commands

        commands = [
            {
                "command": "model.faces",
                "params": {"body": "Panel"},
                "bind": {
                    "$face_point_1": {
                        "field": "faces",
                        "where": {"plane_normal": [0, 0, 1]},
                        "max": "area",
                        "select": "point",
                    },
                    "$face_index_1": {
                        "field": "faces",
                        "where": {"plane_normal": [0, 0, 1]},
                        "max": "area",
                        "select": "index",
                    },
                },
            },
            {
                "command": "sketch.create",
                "params": {
                    "plane": {
                        "face": "$face_point_1",
                        "body": "Panel",
                        "index": "$face_index_1",
                    },
                    "name": "Top sketch",
                },
            },
        ]

        namespaced = _namespace_commands(
            commands,
            "Panel",
            definition_number=1,
        )

        self.assertEqual(
            set(namespaced[0]["bind"]),
            {
                "$d1_Panel_face_point_1",
                "$d1_Panel_face_index_1",
            },
        )
        self.assertEqual(
            namespaced[1]["params"]["plane"]["face"],
            "$d1_Panel_face_point_1",
        )
        self.assertEqual(
            namespaced[1]["params"]["plane"]["index"],
            "$d1_Panel_face_index_1",
        )

    def test_component_namespacing_rewrites_replay_binding_prepend(self):
        from scpf.assembly import _namespace_commands

        commands = [
            {
                "command": "sketch.circle.center",
                "params": {"center": [0, 0], "diameter": 8},
                "bind": {"$sketch_1_profile_1": "curves"},
            },
            {
                "command": "sketch.pattern.rectangular",
                "params": {
                    "entities": "$sketch_1_profile_1",
                    "count": 2,
                    "spacing": 20,
                    "dir": [1, 0],
                },
                "bind": {
                    "$sketch_1_operation_1": {
                        "field": "curves",
                        "prepend": "$sketch_1_profile_1",
                    },
                },
            },
        ]

        namespaced = _namespace_commands(
            commands,
            "PatternPart",
            definition_number=2,
        )

        self.assertEqual(
            namespaced[0]["bind"],
            {"$d2_PatternPart_sketch_1_profile_1": "curves"},
        )
        self.assertEqual(
            namespaced[1]["params"]["entities"],
            "$d2_PatternPart_sketch_1_profile_1",
        )
        self.assertEqual(
            namespaced[1]["bind"],
            {
                "$d2_PatternPart_sketch_1_operation_1": {
                    "field": "curves",
                    "prepend": "$d2_PatternPart_sketch_1_profile_1",
                },
            },
        )

    def test_component_replay_namespaces_are_distinct_per_definition(self):
        from scpf.assembly import _namespace_commands

        commands = [
            {
                "command": "model.faces",
                "params": {"body": "Part"},
                "bind": {"$face_point_1": "faces"},
            },
        ]

        first = _namespace_commands(
            commands,
            "Part",
            definition_number=1,
        )
        second = _namespace_commands(
            commands,
            "Part",
            definition_number=2,
        )

        self.assertEqual(
            first[0]["bind"],
            {"$d1_Part_face_point_1": "faces"},
        )
        self.assertEqual(
            second[0]["bind"],
            {"$d2_Part_face_point_1": "faces"},
        )

    def test_attached_sketch_component_assembly_is_valid_replay(self):
        from scpf import Anchor, Box, Circle2D, Depth, Sketch, component
        from scpf.assembly import compile_assembly
        from scpf.replay import validate_replay_document

        @component
        class FaceCut:
            def build(self):
                body = Box(40, 30, 4)
                with Sketch(
                    name="Top cut",
                    on=body,
                    parent=Anchor.TOP,
                ) as sketch:
                    Circle2D(d=8)
                return body - sketch.extrude(Depth.THROUGH_ALL)

        document = compile_assembly(FaceCut(), "FaceCutAssembly")
        validate_replay_document(document)

        faces = next(
            command
            for command in document["commands"]
            if command["command"] == "model.faces"
        )
        self.assertEqual(
            set(faces["bind"]),
            {
                "$d1_FaceCut_face_point_1",
                "$d1_FaceCut_face_index_1",
            },
        )
        sketch = next(
            command
            for command in document["commands"]
            if command["command"] == "sketch.create"
            and command["params"].get("name") == "Top cut"
        )
        self.assertEqual(
            sketch["params"]["plane"]["face"],
            "$d1_FaceCut_face_point_1",
        )
        self.assertEqual(
            sketch["params"]["plane"]["index"],
            "$d1_FaceCut_face_index_1",
        )

    def test_reusable_text_component_keeps_literal_strings_opaque(self):
        from scpf import Anchor, Box, Sketch
        from scpf.core import Text2D
        from scpf.assembly import compile_assembly
        from scpf.runner import component

        class Label:
            height = 8.0

            def build(self):
                body = Box(40, 20, 2)
                with Sketch(
                    name="height",
                    on=body,
                    parent=Anchor.TOP,
                ) as sketch:
                    Text2D(
                        "height",
                        height=self.height / 2,
                        font="height",
                    )
                return body + sketch.extrude(2)

        Part = component(Label, include=("height",))
        document = compile_assembly(Part(), "Display")
        commands = document["commands"]

        parameter = next(
            row["params"]
            for row in commands
            if row["command"] == "parameters.add"
        )
        sketch = next(
            row["params"]
            for row in commands
            if row["command"] == "sketch.create"
        )
        text = next(
            row["params"]
            for row in commands
            if row["command"] == "sketch.text"
        )
        extrude = next(
            row["params"]
            for row in commands
            if row["command"] == "solid.extrude"
        )

        self.assertEqual(parameter["name"], "d1_Label_height")
        self.assertEqual(text["height"], "d1_Label_height / 2")
        self.assertEqual(text["text"], "height")
        self.assertEqual(text["font"], "height")
        self.assertEqual(sketch["name"], "height")
        self.assertEqual(extrude["name"], "height")

        def assert_plain_json_strings(value):
            if isinstance(value, str):
                self.assertIs(type(value), str)
            elif isinstance(value, dict):
                for key, item in value.items():
                    self.assertIs(type(key), str)
                    assert_plain_json_strings(item)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    assert_plain_json_strings(item)

        assert_plain_json_strings(document)

    def test_reusable_component_keeps_material_name_equal_to_parameter_name(self):
        from scpf.assembly import compile_assembly
        from scpf.core import Box
        from scpf.runner import component

        class MaterialBlock:
            width = 40.0

            def build(self):
                return Box(
                    self.width,
                    20,
                    10,
                ).with_material(
                    "width",
                    density_g_cm3=1.2,
                )

        Part = component(MaterialBlock, include=("width",))
        commands = compile_assembly(
            Part(),
            "Display",
        )["commands"]

        parameter = next(
            row["params"]
            for row in commands
            if row["command"] == "parameters.add"
        )
        box = next(
            row["params"]
            for row in commands
            if row["command"] == "solid.box"
        )
        material = next(
            row["params"]
            for row in commands
            if row["command"] == "material.create"
        )
        assignment = next(
            row["params"]
            for row in commands
            if row["command"] == "material.assign"
        )

        self.assertEqual(parameter["name"], "d1_MaterialBlock_width")
        self.assertEqual(box["length"], "d1_MaterialBlock_width")
        self.assertEqual(material["name"], "width")
        self.assertEqual(assignment["material"], "width")

    def test_identical_material_is_created_once_across_components(self):
        from scpf.assembly import compile_assembly
        from scpf.core import Box
        from scpf.runner import component

        class Left:
            def build(self):
                return Box(10, 20, 30).with_material(
                    "WOOD", density_g_cm3=0.55, color="#CBA36B"
                )

        class Right:
            def build(self):
                return Box(10, 20, 30).with_material(
                    "WOOD", density_g_cm3=0.55, color="#CBA36B"
                )

        LeftPart = component(Left)
        RightPart = component(Right)
        commands = compile_assembly(
            LeftPart() + RightPart(),
            "Frame",
        )["commands"]

        creates = [
            c["params"] for c in commands
            if c["command"] == "material.create"
        ]
        assigns = [
            c["params"] for c in commands
            if c["command"] == "material.assign"
        ]
        self.assertEqual(len(creates), 1)
        self.assertEqual(creates[0]["name"], "WOOD")
        self.assertEqual(len(assigns), 2)
        self.assertTrue(all(a["material"] == "WOOD" for a in assigns))

    def test_conflicting_shared_material_definition_is_rejected(self):
        from scpf.assembly import compile_assembly
        from scpf.compiler import ModelError
        from scpf.core import Box
        from scpf.runner import component

        class Left:
            def build(self):
                return Box(10, 20, 30).with_material(
                    "WOOD", density_g_cm3=0.55, color="#CBA36B"
                )

        class Right:
            def build(self):
                return Box(10, 20, 30).with_material(
                    "WOOD", density_g_cm3=0.55, color="#FFFFFF"
                )

        with self.assertRaisesRegex(ModelError, "defined differently"):
            compile_assembly(
                component(Left)() + component(Right)(),
                "Frame",
            )

    def test_component_defaults_are_fixed_unless_included(self):
        from scpf.assembly import compile_assembly
        from scpf.core import Box
        from scpf.runner import component

        class Bracket:
            width = 24.0
            radius = 4.0
            chamfer = 2.0

            def build(self):
                return Box(
                    self.width,
                    self.radius + 20,
                    self.chamfer + 10,
                )

        Hidden = component(Bracket)
        hidden = compile_assembly(Hidden(), "Hidden")["commands"]
        hidden_names = [
            command["params"]["name"]
            for command in hidden
            if command["command"] == "parameters.add"
        ]
        self.assertEqual(hidden_names, [])

        Selected = component(Bracket, include=("radius",))
        selected = compile_assembly(Selected(), "Selected")["commands"]
        selected_names = [
            command["params"]["name"]
            for command in selected
            if command["command"] == "parameters.add"
        ]
        self.assertEqual(selected_names, ["d1_Bracket_radius"])

        All = component(Bracket, include="*")
        all_commands = compile_assembly(All(), "All")["commands"]
        all_names = [
            command["params"]["name"]
            for command in all_commands
            if command["command"] == "parameters.add"
        ]
        self.assertEqual(
            all_names,
            ["d1_Bracket_width", "d1_Bracket_radius", "d1_Bracket_chamfer"],
        )

        with self.assertRaisesRegex(ValueError, "unknown component parameter"):
            component(Bracket, include=("missing",))

    def test_component_decorator_accepts_selected_include(self):
        from scpf.assembly import compile_assembly
        from scpf.core import Box
        from scpf.runner import component

        @component(include=("radius",))
        class Bracket:
            width = 24.0
            radius = 4.0

            def build(self):
                return Box(self.width, self.radius + 20, 10)

        commands = compile_assembly(Bracket(), "BracketAssembly")["commands"]
        names = [
            command["params"]["name"]
            for command in commands
            if command["command"] == "parameters.add"
        ]
        self.assertEqual(names, ["d1_Bracket_radius"])

    def test_component_include_mapping_publishes_shared_name(self):
        from scpf.assembly import compile_assembly
        from scpf.core import Box, Edges
        from scpf.runner import component

        class Bracket:
            width = 24.0
            radius = 4.0

            def build(self):
                return Box(self.width, 40, 40).fillet(
                    self.radius,
                    edges=Edges.VERTICAL,
                )

        BracketObject = component(
            Bracket,
            include={"radius": "corner_radius"},
        )
        commands = compile_assembly(BracketObject(), "Display")["commands"]
        names = [
            command["params"]["name"]
            for command in commands
            if command["command"] == "parameters.add"
        ]
        self.assertEqual(names, ["corner_radius"])
        self.assertNotIn("Bracket_radius", names)

    def test_decorated_component_file_runs_as_standalone_root(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "component.py"
            script.write_text(
                "from scpf import component\n"
                "@component\n"
                "class Block:\n"
                "    width = 40.0\n"
                "    depth = 20.0\n"
                "    height = 10.0\n"
                "    def build(self):\n"
                "        return Box(self.width, self.depth, self.height)\n",
                encoding="utf-8",
            )
            commands = run_script(script)["commands"]

        self.assertFalse(
            any(command["command"] == "component.create" for command in commands)
        )
        self.assertEqual(
            [
                command["params"]["name"]
                for command in commands
                if command["command"] == "parameters.add"
            ],
            ["width", "depth", "height"],
        )
        self.assertTrue(
            any(command["command"] == "solid.box" for command in commands)
        )

    def test_decorated_component_is_reused_without_second_wrapper(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "assembly.py"
            script.write_text(
                "from scpf import component\n"
                "@component\n"
                "class Block:\n"
                "    width = 40.0\n"
                "    def build(self):\n"
                "        return Box(self.width, 20, 10)\n"
                "class Pair:\n"
                "    def build(self):\n"
                "        first = Block()\n"
                "        return first + first.copy(placement=Placement(x=50))\n"
                "Pair()\n",
                encoding="utf-8",
            )
            commands = run_script(script)["commands"]

        self.assertEqual(
            [
                command["params"]["name"]
                for command in commands
                if command["command"] == "component.create"
            ],
            ["Block"],
        )
        self.assertEqual(
            len([
                command for command in commands
                if command["command"] == "occurrence.copy"
                and command["params"]["component"] == "Block"
            ]),
            1,
        )

    def test_private_component_build_input_can_bind_parent_parameter(self):
        from scpf.assembly import compile_assembly
        from scpf import Sketch
        from scpf.core import Parameter, Polygon2D
        from scpf.runner import component

        class Bracket:
            width = 24.0
            _x_position = 0.0

            def build(self):
                x0 = self._x_position
                with Sketch(plane="XZ") as sketch:
                    Polygon2D([
                        (x0, 0),
                        (x0 + self.width, 0),
                        (x0 + self.width, 10),
                        (x0, 10),
                    ], plane="XZ", world=True)
                return sketch.extrude(10)

        BracketObject = component(Bracket)
        opening_width = Parameter("opening_width", 844.0)
        bracket = BracketObject(_x_position=opening_width / 2)

        self.assertNotIn(
            "_x_position",
            dict(bracket.definition.parameters),
        )
        self.assertEqual(
            dict(bracket.definition.external_parameters)["opening_width"],
            844.0,
        )
        self.assertIn(
            "opening_width",
            str(bracket.definition.shape.data),
        )

        commands = compile_assembly(bracket, "Display")["commands"]
        names = [
            command["params"]["name"]
            for command in commands
            if command["command"] == "parameters.add"
        ]
        self.assertEqual(names, ["opening_width"])
        self.assertNotIn("Bracket__x_position", names)

    def test_component_preserves_parent_parameter_dependency(self):
        from scpf.assembly import compile_assembly
        from scpf.core import Box, Parameter
        from scpf.runner import component

        class Panel:
            width = 100.0
            height = 20.0
            thickness = 2.0

            def build(self):
                return Box(self.width, self.thickness, self.height)

        PanelObject = component(Panel)
        parent_width = Parameter("opening_width", 844.0)
        instance = PanelObject(width=parent_width)

        self.assertNotIn("width", dict(instance.definition.parameters))
        self.assertEqual(
            dict(instance.definition.external_parameters)["opening_width"],
            844.0,
        )
        self.assertEqual(
            dict(instance.definition.input_bindings)["width"],
            "opening_width",
        )
        self.assertEqual(
            instance.definition.shape.data[0].name,
            "opening_width",
        )

        commands = compile_assembly(instance, "Display")["commands"]
        parameter_names = [
            command["params"]["name"]
            for command in commands
            if command["command"] == "parameters.add"
        ]
        self.assertIn("opening_width", parameter_names)
        self.assertNotIn("Panel_width", parameter_names)

    def test_shared_parent_parameter_is_added_once_for_multiple_components(self):
        from scpf.assembly import compile_assembly
        from scpf.core import Box, Parameter
        from scpf.runner import component

        class Strip:
            length = 100.0
            width = 12.0

            def build(self):
                return Box(self.length, self.width, 4)

        StripObject = component(Strip)
        opening_width = Parameter("opening_width", 844.0)

        horizontal = StripObject(length=opening_width, width=12.0)
        second = StripObject(length=opening_width, width=15.0)

        commands = compile_assembly(horizontal + second, "Frame")["commands"]
        parameter_names = [
            command["params"]["name"]
            for command in commands
            if command["command"] == "parameters.add"
        ]

        self.assertEqual(parameter_names.count("opening_width"), 1)
        self.assertNotIn("Strip_length", parameter_names)
        self.assertNotIn("Strip_2_length", parameter_names)
        self.assertNotIn("Strip_width", parameter_names)
        self.assertNotIn("Strip_2_width", parameter_names)

    def test_parent_expression_remains_an_expression_in_child_geometry(self):
        from scpf.assembly import compile_assembly
        from scpf.core import Box, Parameter
        from scpf.runner import component

        class Board:
            width = 100.0
            thickness = 12.0

            def build(self):
                return Box(self.width, 50, self.thickness)

        BoardObject = component(Board)
        opening_width = Parameter("opening_width", 844.0)
        frame_wood_thickness = Parameter("frame_wood_thickness", 12.0)
        outer_width = opening_width + 2 * frame_wood_thickness

        board = BoardObject(width=outer_width)
        commands = compile_assembly(board, "Frame")["commands"]

        parameter_names = [
            command["params"]["name"]
            for command in commands
            if command["command"] == "parameters.add"
        ]
        self.assertEqual(parameter_names.count("opening_width"), 1)
        self.assertEqual(parameter_names.count("frame_wood_thickness"), 1)
        self.assertNotIn("Board_width", parameter_names)

        box = next(
            command for command in commands
            if command["command"] == "solid.box"
        )
        self.assertIn("opening_width", str(box["params"]))
        self.assertIn("frame_wood_thickness", str(box["params"]))

    def test_named_component_objects_resolve_directly_from_assembly(self):
        from scpf.core import Box
        from scpf.runner import component

        class Board:
            width = 100.0

            def build(self):
                return Box(self.width, 20, 10)

        BoardObject = component(Board)
        roof = BoardObject(name="roof", width=120)
        bottom = BoardObject(name="bottom", width=100)
        frame = roof + bottom

        self.assertIs(frame.roof, roof)
        self.assertIs(frame.bottom, bottom)
        self.assertIs(frame.resolve("roof"), roof)

        copy = roof.copy()
        self.assertIsNone(copy.name)

        with self.assertRaisesRegex(ValueError, "object names must be unique"):
            _ = roof + BoardObject(name="roof")

    def test_plain_assembly_accepts_non_parametric_object_reference_input(self):
        from scpf.core import Box, Parameter
        from scpf.runner import assembly, component
        from scpf.model_objects import Assembly

        class FramePart:
            def build(self):
                return Box(40, 20, 10)

        FrameObject = component(FramePart)
        frame = FrameObject()

        @assembly
        class Brackets:
            wood_frame = None
            spacing = 30.0

            def build(self):
                self.assert_reference = self.wood_frame
                marker = FrameObject(placement=Placement(x=self.spacing))
                return self.wood_frame + marker

        brackets = Brackets(
            wood_frame=frame,
            spacing=Parameter("spacing", 50.0),
        )

        self.assertIsInstance(brackets, Assembly)
        self.assertEqual(len(brackets.instances), 2)
        self.assertIs(brackets.instances[0], frame)
        self.assertEqual(brackets.instances[1].placement.position[0].name, "spacing")
        self.assertEqual(brackets.instances[1].placement.position[1:], (0, 0))

    def test_imported_assembly_class_uses_object_syntax(self):
        from scpf.core import Box, Parameter
        from scpf.runner import assembly, component
        from scpf.model_objects import Assembly

        class Panel:
            width = 100.0
            height = 20.0
            thickness = 2.0

            def build(self):
                return Box(self.width, self.thickness, self.height)

        PanelObject = component(Panel)

        class PanelRow:
            width = 100.0
            pitch = 110.0

            def build(self):
                left = PanelObject(width=self.width)
                right = left.copy(placement=Placement(x=self.pitch))
                return (left + right).group("Panels")

        PanelRowObject = assembly(PanelRow)
        row = PanelRowObject(
            width=Parameter("panel_width", 160.0),
            pitch=Parameter("panel_pitch", 170.0),
        )

        self.assertIsInstance(row, Assembly)
        self.assertEqual(len(row.instances), 2)
        self.assertEqual(row.instances[1].placement.position[0].name, "panel_pitch")
        self.assertEqual(row.instances[1].placement.position[1:], (0, 0))
        self.assertNotIn(
            "width",
            dict(row.instances[0].definition.parameters),
        )
        self.assertEqual(
            dict(row.instances[0].definition.external_parameters)["panel_width"],
            160.0,
        )

    def test_parent_parameter_binding_reuses_existing_name_without_child_duplicate(self):
        from scpf.assembly import compile_assembly
        from scpf.core import Box, Edges, Parameter
        from scpf.runner import component

        class Bracket:
            bracket_width = 24.0
            inside_corner_radius = 4.0

            def build(self):
                return Box(self.bracket_width, 40, 40).fillet(
                    self.inside_corner_radius,
                    edges=Edges.VERTICAL,
                )

        BracketObject = component(Bracket)
        shared = Parameter("corner_radius", 5.0)
        commands = compile_assembly(
            BracketObject(inside_corner_radius=shared),
            "Display",
        )["commands"]

        parameter_names = [
            command["params"]["name"]
            for command in commands
            if command["command"] == "parameters.add"
        ]
        self.assertEqual(parameter_names, ["corner_radius"])
        self.assertNotIn("Bracket_inside_corner_radius", parameter_names)

        fillet = next(
            command["params"]
            for command in commands
            if command["command"] == "solid.fillet"
        )
        self.assertEqual(fillet["radius"], "corner_radius")

    def test_xz_rectangular_component_uses_standard_corner_anchor(self):
        commands = run_script(
            ROOT / "examples/xz-anchor/scpf/model.py"
        )["commands"]

        joints = [
            command["params"]
            for command in commands
            if command["command"] == "joint.create"
        ]
        self.assertEqual(len(joints), 2)
        self.assertEqual(joints[0]["a"]["occurrence"], "$board")
        self.assertEqual(joints[0]["a"]["corner"], [20.0, 0.0, 20.0])
        self.assertEqual(joints[1]["a"]["occurrence"], "$board")
        self.assertEqual(joints[1]["a"]["corner"], [-20.0, 0.0, 20.0])
        self.assertEqual(
            [joint["b"]["occurrence"] for joint in joints],
            ["$rightmarker", "$leftmarker"],
        )
        self.assertFalse(any(
            "Board:" in str(command["params"])
            or "RightMarker:" in str(command["params"])
            or "LeftMarker:" in str(command["params"])
            for command in commands
        ))

    def test_copy_creates_a_second_occurrence_of_one_definition(self):
        from scpf.core import Box
        from scpf.model_objects import ModelDefinition, ModelInstance, Placement

        original = ModelInstance(ModelDefinition("Panel", (), Box(20, 10, 2)))
        duplicate = original.copy(placement=Placement(x=24))
        self.assertIsNot(original, duplicate)
        self.assertIs(original.definition, duplicate.definition)
        self.assertEqual(original.placement.position, (0, 0, 0))
        self.assertEqual(duplicate.placement.position, (24, 0, 0))
        self.assertIsNone(duplicate.attachment)

