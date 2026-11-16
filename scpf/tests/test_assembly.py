"""Reusable model objects and native SolidCraft assembly command tests."""
from pathlib import Path
import tempfile
import unittest

from scpf.runner import run_script
from scpf.model_objects import Placement

ROOT = Path(__file__).resolve().parents[2]


class AssemblyTests(unittest.TestCase):
    def test_copied_occurrence_attachment_is_rejected(self):
        from scpf.compiler import ModelError

        with self.assertRaisesRegex(
            ModelError,
            "attachment involving a copied occurrence",
        ):
            run_script(ROOT / "examples/components/scpf/model.py")

    def test_component_placement_is_occurrence_data(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "placement_keyword.py"
            script.write_text(
                "class Panel:\n"
                "    width = 20.0\n"
                "    def build(self):\n"
                "        return Box(self.width, 10, 2)\n"
                "class Display:\n"
                "    def build(self):\n"
                "        left = Panel()\n"
                "        right = left.copy(placement=Placement(x=30))\n"
                "        return left + right\n"
                "Display()\n",
                encoding="utf-8",
            )
            commands = run_script(script)["commands"]

        parameters = [
            command["params"]["name"]
            for command in commands
            if command["command"] == "parameters.add"
        ]
        self.assertEqual(parameters, [])
        copy = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.copy"
        )
        self.assertEqual(copy["translate"], [30.0, 0.0, 0.0])
        self.assertFalse(any(
            command["command"] == "occurrence.move"
            for command in commands
        ))
        self.assertFalse(any("Panel:" in str(command) for command in commands))

    def test_occurrence_placement_is_declared_at_construction(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "position_at.py"
            script.write_text(
                "class Block:\n"
                "    def build(self):\n"
                "        return Box(20, 10, 2)\n"
                "class Pair:\n"
                "    def build(self):\n"
                "        first = Block()\n"
                "        second = first.copy(placement=Placement(x=50))\n"
                "        return first + second\n"
                "Pair()\n",
                encoding="utf-8",
            )
            commands = run_script(script)["commands"]

        copy = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.copy"
        )
        self.assertEqual(copy["translate"], [50.0, 0.0, 0.0])

    def test_copy_accepts_placement_override(self):
        from scpf import Box, Placement, component

        @component
        class Panel:
            def build(self):
                return Box(20, 10, 2)

        original = Panel(placement=Placement(x=10, y=5))
        copied = original.copy(placement=Placement(x=40, y=0, z=3))
        self.assertEqual(original.placement.position, (10, 5, 0))
        self.assertEqual(copied.placement.position, (40, 0, 3))
        self.assertIsNone(copied.attachment)
        self.assertEqual(original.copy().placement, original.placement)
        with self.assertRaisesRegex(TypeError, "Placement"):
            original.copy(placement=(40, 0, 3))

    def test_forge_occurrence_id_survives_group_and_attach_but_not_copy(self):
        from scpf import Box, component

        @component
        class Panel:
            def build(self):
                return Box(20, 10, 2)

        parent = Panel()
        child = Panel()

        grouped = parent.group("Panels")
        attached = child.attach(parent)
        copied = parent.copy()

        self.assertEqual(grouped.occurrence_id, parent.occurrence_id)
        self.assertEqual(attached.occurrence_id, child.occurrence_id)
        self.assertEqual(
            attached.attachment.target.occurrence_id,
            parent.occurrence_id,
        )
        self.assertNotEqual(copied.occurrence_id, parent.occurrence_id)

    def test_same_forge_occurrence_cannot_be_added_twice(self):
        from scpf import Box, component

        @component
        class Panel:
            def build(self):
                return Box(20, 10, 2)

        panel = Panel()
        with self.assertRaisesRegex(ValueError, "same Forge occurrence"):
            panel + panel

    def test_grouped_attachment_resolves_by_forge_occurrence_id(self):
        from scpf import Anchor, Box, component
        from scpf.assembly import compile_assembly

        @component
        class ParentPanel:
            def build(self):
                return Box(20, 10, 2)

        @component
        class ChildPanel:
            def build(self):
                return Box(20, 10, 2)

        parent = ParentPanel()
        child = ChildPanel().attach(
            parent,
            parent=Anchor.RIGHT,
            child=Anchor.LEFT,
        )
        grouped = (parent + child).group("Pair")

        self.assertIsNot(
            grouped.instances[1].attachment.target,
            grouped.instances[0],
        )
        self.assertEqual(
            grouped.instances[1].attachment.target.occurrence_id,
            grouped.instances[0].occurrence_id,
        )

        commands = compile_assembly(grouped, "GroupedPair")["commands"]
        joints = [
            command for command in commands
            if command["command"] == "joint.create"
        ]
        self.assertEqual(len(joints), 1)

    def test_replay_first_ordinary_placement_uses_copy_translate_only(self):
        from scpf import Box, Placement, component
        from scpf.assembly import compile_assembly

        @component
        class Panel:
            def build(self):
                return Box(20, 10, 2)

        first = Panel()
        second = first.copy(placement=Placement(x=30))
        commands = compile_assembly(first + second, "Panels")["commands"]

        copies = [
            command["params"]
            for command in commands
            if command["command"] == "occurrence.copy"
        ]
        self.assertEqual(copies, [{"component": "Panel", "translate": [30, 0, 0]}])
        self.assertFalse(any(
            command["command"] == "occurrence.move"
            for command in commands
        ))
        self.assertFalse(any(
            "Panel:" in str(command["params"])
            for command in commands
        ))

    def test_replay_first_can_bind_later_identity_occurrence_as_native_first(self):
        from scpf import Box, Placement, component
        from scpf.assembly import compile_assembly

        @component
        class Panel:
            def build(self):
                return Box(20, 10, 2)

        moved = Panel(placement=Placement(x=30))
        identity = moved.copy(placement=Placement())
        commands = compile_assembly(moved + identity, "Panels")["commands"]

        copy = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.copy"
        )
        self.assertEqual(copy["translate"], [30, 0, 0])
        self.assertFalse(any(
            command["command"] == "occurrence.move"
            for command in commands
        ))

    def test_replay_first_rejects_definition_without_identity_occurrence(self):
        from scpf import Box, Placement, component
        from scpf.assembly import compile_assembly
        from scpf.compiler import ModelError

        @component
        class Panel:
            def build(self):
                return Box(20, 10, 2)

        left = Panel(placement=Placement(x=-30))
        right = left.copy(placement=Placement(x=30))
        with self.assertRaisesRegex(
            ModelError,
            "requires one occurrence at identity",
        ):
            compile_assembly(left + right, "Panels")

    def test_replay_first_rejects_symbolic_ordinary_copy_placement(self):
        from scpf import Box, Parameter, Placement, component
        from scpf.assembly import compile_assembly
        from scpf.compiler import ModelError

        @component
        class Panel:
            def build(self):
                return Box(20, 10, 2)

        first = Panel()
        second = first.copy(
            placement=Placement(x=Parameter("offset", 30)),
        )
        with self.assertRaisesRegex(
            ModelError,
            "symbolic copied Placement is not replay-safe",
        ):
            compile_assembly(first + second, "Panels")

    def test_replay_first_rejects_rotated_ordinary_copy_placement(self):
        from scpf import Box, Placement, Z, component
        from scpf.assembly import compile_assembly
        from scpf.compiler import ModelError

        @component
        class Panel:
            def build(self):
                return Box(20, 10, 2)

        first = Panel()
        second = first.copy(
            placement=Placement(x=30, rotation=(Z, 180)),
        )
        with self.assertRaisesRegex(
            ModelError,
            "rotated copied Placement is not replay-safe",
        ):
            compile_assembly(first + second, "Panels")

    def test_copies_use_declared_native_placements(self):
        """Concrete unrotated copies carry their final Placement in copy."""
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "sidewalls.py"
            script.write_text(
                "class SideWall:\n"
                "    def build(self):\n"
                "        return Box(15, 100, 362)\n"
                "class Cabinet:\n"
                "    def build(self):\n"
                "        left = SideWall()\n"
                "        right = left.copy(placement=Placement(x=429.5, y=25))\n"
                "        return (left + right).group('WoodBoxFrame')\n"
                "Cabinet()\n",
                encoding="utf-8",
            )
            commands = run_script(script)["commands"]
        copy = next(c["params"] for c in commands
                    if c["command"] == "occurrence.copy")
        self.assertEqual(copy["component"], "SideWall")
        self.assertEqual(copy["translate"], [429.5, 25.0, 0.0])
        self.assertFalse(any(
            c["command"] == "occurrence.move"
            for c in commands
        ))

    def test_rotated_copy_is_rejected_without_replay_safe_selector(self):
        from scpf.compiler import ModelError

        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "rotated_source.py"
            script.write_text(
                "class Panel:\n"
                "    def build(self):\n"
                "        return Box(20, 10, 2)\n"
                "class Cabinet:\n"
                "    def build(self):\n"
                "        first = Panel()\n"
                "        right = first.copy(placement=Placement(x=40, rotation=(Z, 180)))\n"
                "        return first + right\n"
                "Cabinet()\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ModelError,
                "rotated copied Placement is not replay-safe",
            ):
                run_script(script)

    def test_named_group_creates_real_nested_native_component(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "group.py"
            path.write_text(
                "class Panel:\n"
                "    def build(self):\n"
                "        return Box(10, 2, 20)\n"
                "class Frame:\n"
                "    def build(self):\n"
                "        return Box(35, 10, 40)\n"
                "class Display:\n"
                "    def build(self):\n"
                "        left = Panel()\n"
                "        group = (left + left.copy(placement=Placement(x=11))).group('HUB75Panels')\n"
                "        return group + Frame()\n"
                "Display()\n",
                encoding="utf-8",
            )
            commands = run_script(path)["commands"]
        created = [c["params"] for c in commands
                   if c["command"] == "component.create"]
        self.assertEqual([c["name"] for c in created],
                         ["HUB75Panels", "Panel", "Frame"])
        self.assertEqual(created[0]["activate"], False)
        self.assertTrue(created[0]["grounded"])
        self.assertEqual(created[1]["parent"], "HUB75Panels")
        self.assertFalse(created[1]["grounded"])
        self.assertNotIn("parent", created[2])
        copies = [c for c in commands if c["command"] == "occurrence.copy"]
        self.assertEqual(len(copies), 1)
        self.assertEqual(copies[0]["params"]["component"], "Panel")

    def test_each_named_group_is_grounded_as_a_fixed_parent_frame(self):
        from scpf import Box, component
        from scpf.assembly import compile_assembly

        @component
        class LeftPart:
            def build(self):
                return Box(10, 10, 10)

        @component
        class RightPart:
            def build(self):
                return Box(12, 10, 10)

        left = LeftPart().group("LeftGroup")
        right = RightPart().group("RightGroup")
        commands = compile_assembly(left + right, "Grouped")["commands"]

        groups = [
            command["params"]
            for command in commands
            if command["command"] == "component.create"
            and command["params"]["name"] in {"LeftGroup", "RightGroup"}
        ]
        self.assertEqual(
            [(group["name"], group["grounded"]) for group in groups],
            [("LeftGroup", True), ("RightGroup", True)],
        )

    def test_group_name_conflicts_and_multi_parent_definitions_rejected(self):
        from scpf.core import Box
        from scpf.model_objects import ModelDefinition, ModelInstance
        from scpf.assembly import compile_assembly
        from scpf.compiler import ModelError
        panel = ModelInstance(ModelDefinition("Panel", (), Box(10, 2, 20)))
        with self.assertRaisesRegex(ValueError, "non-empty"):
            panel.group("")
        with self.assertRaisesRegex(ValueError, "multiple groups"):
            panel.group("One").group("Two")
        with self.assertRaisesRegex(ModelError, "multiple assembly parents"):
            compile_assembly(panel.group("A") + panel.copy(), "Display")
        with self.assertRaisesRegex(ModelError, "conflicts"):
            compile_assembly(panel.group("Panel"), "Display")

    def test_rotation_remains_occurrence_data_but_is_not_replay_safe_yet(self):
        from scpf.core import Box
        from scpf.model_objects import ModelDefinition, ModelInstance, Placement
        from scpf.assembly import compile_assembly
        from scpf.compiler import ModelError

        first = ModelInstance(ModelDefinition("Panel", (), Box(20, 10, 2)))
        second = first.copy(placement=Placement(x=30, rotation=((0, 0, 1), 180)))
        self.assertIs(first.definition, second.definition)
        self.assertIsNone(first.placement.rotation)
        self.assertEqual(second.placement.position, (30, 0, 0))
        self.assertEqual(second.placement.rotation, ((0.0, 0.0, 1.0), 180.0))
        self.assertIsNone(second.attachment)
        self.assertEqual(second.copy().placement.rotation, second.placement.rotation)

        with self.assertRaisesRegex(
            ModelError,
            "rotated copied Placement is not replay-safe",
        ):
            compile_assembly(first + second, "Display")

    def test_placement_accepts_named_axis_rotation(self):
        from scpf.core import X, Y, Z
        from scpf.model_objects import Placement

        self.assertEqual(Placement(rotation=(X, 180)).rotation, ((1.0, 0.0, 0.0), 180.0))
        self.assertEqual(Placement(rotation=(Y, 90)).rotation, ((0.0, 1.0, 0.0), 90.0))
        self.assertEqual(Placement(rotation=(Z, -90)).rotation, ((0.0, 0.0, 1.0), -90.0))
        with self.assertRaisesRegex(ValueError, "X, Y or Z"):
            Placement(rotation=("Q", 90))

    def test_first_grounded_occurrence_rotation_is_rejected_replay_first(self):
        from scpf.compiler import ModelError

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "root_rotation.py"
            path.write_text(
                "class Panel:\n"
                "    def build(self):\n"
                "        return Box(20, 10, 2)\n"
                "class Display:\n"
                "    def build(self):\n"
                "        first = Panel(placement=Placement(x=-50, rotation=(Z, 180)))\n"
                "        return first + first.copy(placement=Placement())\n"
                "Display()\n", encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ModelError,
                "rotated copied Placement is not replay-safe",
            ):
                run_script(path)

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

    def test_rotated_hub75_copies_require_replay_safe_selector(self):
        from scpf.compiler import ModelError

        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "five.py"
            script.write_text(
                "class Panel:\n"
                "    def build(self):\n"
                "        return Box(159.7, 319.71, 14.5)\n"
                "class Screen:\n"
                "    def build(self):\n"
                "        first = Panel()\n"
                "        return (first + first.copy(placement=Placement(x=-320, z=160, rotation=((1,0,0), 90))) +\n"
                "                first.copy(placement=Placement(x=-160, z=160, rotation=((1,0,0), 90))) +\n"
                "                first.copy(placement=Placement(x=160, z=160, rotation=((1,0,0), 90))) +\n"
                "                first.copy(placement=Placement(x=320, z=160, rotation=((1,0,0), 90))))\n"
                "Screen()\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ModelError,
                "rotated copied Placement is not replay-safe",
            ):
                run_script(script)

    def test_rotation_rejects_undefined_and_nonfinite_axis_angle(self):
        from scpf.model_objects import Placement

        for kwargs in (
            {"axis": (0, 0, 0), "degrees": 90},
            {"axis": (0, 1), "degrees": 90},
            {"axis": (0, float("nan"), 1), "degrees": 90},
            {"axis": (0, 0, 1), "degrees": float("inf")},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Placement(rotation=(kwargs["axis"], kwargs["degrees"]))

    def test_component_attach_lowers_in_plane_offset_as_planar_joint(self):
        from scpf.assembly import compile_assembly
        from scpf.core import Anchor, Box
        from scpf.model_objects import ModelDefinition, ModelInstance

        left_definition = ModelDefinition(
            "LeftBlock",
            (("length", 40.0), ("width", 30.0), ("height", 10.0)),
            Box(40, 30, 10),
        )
        right_definition = ModelDefinition(
            "RightBlock",
            (("length", 40.0), ("width", 30.0), ("height", 10.0)),
            Box(40, 30, 10),
        )
        left = ModelInstance(left_definition)
        right = ModelInstance(right_definition).attach(
            left,
            parent=Anchor.RIGHT,
            child=Anchor.LEFT,
            offset=(5, 7),
            gap=3,
            angle=15,
        )

        commands = compile_assembly(left + right, "OffsetAttach")["commands"]
        joint = next(
            command["params"]
            for command in commands
            if command["command"] == "joint.create"
        )
        self.assertEqual(joint["type"], "planar")
        self.assertEqual(joint["values"], [5, 7, 15])
        self.assertEqual(joint["offset"], 3)
        self.assertNotIn("angle", joint)

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
        self.assertEqual(selected_names, ["Bracket_radius"])

        All = component(Bracket, include="*")
        all_commands = compile_assembly(All(), "All")["commands"]
        all_names = [
            command["params"]["name"]
            for command in all_commands
            if command["command"] == "parameters.add"
        ]
        self.assertEqual(
            all_names,
            ["Bracket_width", "Bracket_radius", "Bracket_chamfer"],
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
        self.assertEqual(names, ["Bracket_radius"])

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
        from scpf.core import Direction, Parameter, Polygon2D
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
                return sketch.extrude(10, direction=Direction.POSITIVE)

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


    def test_symbolic_ordinary_placement_does_not_fall_back_to_expression_move(self):
        from scpf.compiler import ModelError

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "parametric_move.py"
            path.write_text(
                "class Panel:\n"
                "    def build(self):\n"
                "        return Box(40, 12, 20)\n"
                "class Display:\n"
                "    depth = 12.0\n"
                "    def build(self):\n"
                "        first = Panel()\n"
                "        return first + first.copy(placement=Placement(y=half(self.depth)))\n"
                "Display()\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ModelError,
                "symbolic copied Placement is not replay-safe",
            ):
                run_script(path)

    def test_symbolic_ordinary_copy_placement_is_rejected_before_lowering(self):
        from scpf.compiler import ModelError

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "placement_only.py"
            path.write_text(
                "class Panel:\n"
                "    def build(self):\n"
                "        return Box(40, 12, 20)\n"
                "class Display:\n"
                "    offset = 30.0\n"
                "    def build(self):\n"
                "        first = Panel()\n"
                "        return first + first.copy(placement=Placement(x=self.offset))\n"
                "Display()\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ModelError,
                "symbolic copied Placement is not replay-safe",
            ):
                run_script(path)

    def test_symbolic_copy_with_rotation_does_not_use_native_move_fallback(self):
        from scpf.compiler import ModelError

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rotated_parametric_move.py"
            path.write_text(
                "class Strip:\n"
                "    def build(self):\n"
                "        return Box(40, 12, 4)\n"
                "class Frame:\n"
                "    height = 100.0\n"
                "    def build(self):\n"
                "        first = Strip()\n"
                "        return first + first.copy(placement=Placement(z=half(self.height), rotation=(Y, 90)))\n"
                "Frame()\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ModelError,
                "symbolic copied Placement is not replay-safe",
            ):
                run_script(path)

    def test_symbolic_relationship_target_placement_is_rejected_replay_first(self):
        from scpf.assembly import compile_assembly
        from scpf.compiler import ModelError
        from scpf.core import Anchor, Box, Parameter
        from scpf.model_objects import Placement
        from scpf.runner import component

        class Panel:
            def build(self):
                return Box(40, 12, 20)

        PanelObject = component(Panel)
        station = Parameter("station", 100.0)
        parent = PanelObject(placement=Placement(x=station))
        child = PanelObject().attach(
            parent,
            parent=Anchor.RIGHT,
            child=Anchor.LEFT,
        )

        with self.assertRaisesRegex(
            ModelError,
            "symbolic Placement of a relationship target",
        ):
            compile_assembly(parent + child, "Pair")

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


    def test_xz_repeated_marker_attachment_is_rejected_without_copy_reference(self):
        from scpf.compiler import ModelError

        with self.assertRaisesRegex(
            ModelError,
            "attachment involving a copied occurrence",
        ):
            run_script(ROOT / "examples/xz-anchor/scpf/model.py")

    def test_anchor_frame_accepts_named_axis_directions(self):
        from scpf import Anchor, AnchorFrame

        frame = AnchorFrame(
            origin=(10, 25, 0),
            z=Anchor.RIGHT,
            x=Anchor.UP,
        )

        self.assertEqual(frame.origin, (10.0, 25.0, 0.0))
        self.assertEqual(frame.z, (1.0, 0.0, 0.0))
        self.assertEqual(frame.x, (0.0, 0.0, 1.0))

    def test_unrotated_custom_anchors_are_inlined_per_occurrence(self):
        from scpf.assembly import compile_assembly
        from scpf.core import AnchorFrame, Box
        from scpf.runner import component

        class Base:
            def anchors(self):
                return {
                    "front_mount": AnchorFrame(origin=(0, 0, 0)),
                    "rear_mount": AnchorFrame(origin=(0, 0, 0), z=(0, 0, -1)),
                }

            def build(self):
                return Box(20, 20, 10)

        class Bracket:
            def anchors(self):
                return {
                    "front_mount": AnchorFrame(origin=(0, 0, 0)),
                    "rear_mount": AnchorFrame(origin=(0, 0, 0), z=(0, 0, -1)),
                }

            def build(self):
                return Box(10, 10, 10)

        class FrontBracket(Bracket):
            pass

        class RearBracket(Bracket):
            pass

        BaseObject = component(Base)
        FrontBracketObject = component(FrontBracket)
        RearBracketObject = component(RearBracket)

        base = BaseObject()
        front = FrontBracketObject().attach(
            base,
            parent="front_mount",
            child="front_mount",
        )
        rear = RearBracketObject().attach(
            base,
            parent="rear_mount",
            child="rear_mount",
        )

        commands = compile_assembly(base + front + rear, "SelectiveAnchors")["commands"]
        self.assertFalse(
            any(command["command"] == "joint.origin" for command in commands)
        )

        joints = [
            command["params"]
            for command in commands
            if command["command"] == "joint.create"
        ]
        self.assertEqual(len(joints), 2)
        self.assertEqual(
            joints[0]["a"],
            {
                "occurrence": "Base",
                "point": [0.0, 0.0, 0.0],
                "z": [0.0, 0.0, 1.0],
                "x": [1.0, 0.0, 0.0],
            },
        )
        self.assertEqual(
            joints[0]["b"],
            {
                "occurrence": "FrontBracket",
                "point": [0.0, 0.0, 0.0],
                "z": [0.0, 0.0, 1.0],
                "x": [1.0, 0.0, 0.0],
            },
        )
        self.assertEqual(joints[1]["a"]["z"], [0.0, 0.0, -1.0])
        self.assertEqual(joints[1]["b"]["z"], [0.0, 0.0, -1.0])
        self.assertEqual(joints[1]["b"]["occurrence"], "RearBracket")
        self.assertFalse(any(
            ":" in selector
            for command in commands
            for selector in (
                str(command["params"].get("occurrence", "")),
                str(command["params"].get("a", {}).get("occurrence", ""))
                if isinstance(command["params"].get("a"), dict) else "",
                str(command["params"].get("b", {}).get("occurrence", ""))
                if isinstance(command["params"].get("b"), dict) else "",
            )
            if selector
        ))

    def test_assembly_can_own_named_attachment_anchor(self):
        from scpf.assembly import compile_assembly
        from scpf.core import Anchor, AnchorTopology, Box
        from scpf.runner import component

        @component
        class Block:
            def build(self):
                return Box(20, 20, 10)

        left = Block(name="left")
        right = Block(name="right", placement=Placement(x=40))
        topology = AnchorTopology(
            edge=(-10, 0, 5),
            on=(0, 0, 5),
            corner=(-10, 0, 10),
            z=(0, 0, -1),
            x=(1, 0, 0),
        )
        frame = (left + right).with_anchor(
            "top_left",
            left,
            topology,
            offset=(5, 0),
        )

        anchor = frame.anchor("top_left")
        self.assertIs(anchor.target, left)
        self.assertIs(anchor.reference, topology)
        self.assertEqual(anchor.offset, (5, 0))

        @component
        class Marker:
            def build(self):
                return Box(20, 20, 10)

        marker = Marker().attach(
            anchor.target,
            parent=anchor.reference,
            child=Anchor.LEFT,
        )
        commands = compile_assembly(frame + marker, "AssemblyAnchor")["commands"]
        joint = next(
            command["params"]
            for command in commands
            if command["command"] == "joint.create"
        )
        self.assertEqual(joint["a"]["occurrence"], "Block")
        self.assertEqual(joint["a"]["edge"], [-10.0, 0.0, 5.0])
        self.assertEqual(joint["a"]["corner"], [-10.0, 0.0, 10.0])

    def test_group_preserves_assembly_anchor_target(self):
        from scpf.core import AnchorTopology, Box
        from scpf.runner import component

        @component
        class Block:
            def build(self):
                return Box(20, 20, 10)

        left = Block(name="left")
        frame = (left + Block(name="right")).with_anchor(
            "left_edge",
            left,
            AnchorTopology(edge=(-10, 0, 5), on=(0, 0, 5)),
        )
        grouped = frame.group("Frame")
        anchor = grouped.anchor("left_edge")

        self.assertEqual(anchor.target.name, "left")
        self.assertEqual(anchor.target.group_name, "Frame")
        self.assertIs(anchor.target, grouped.left)

    def test_named_topology_anchor_is_inlined_as_edge_reference(self):
        from scpf.assembly import compile_assembly
        from scpf.core import AnchorFrame, AnchorTopology, Box
        from scpf.runner import component

        @component
        class Board:
            def anchors(self):
                return {
                    "front_tangent": AnchorTopology(
                        edge=(-20, 0, 5),
                        on=(-20, 10, 10),
                        corner=(-20, 0, 5),
                        z=(0, 1, 0),
                        x=(0, 0, 1),
                    )
                }

            def build(self):
                return Box(40, 20, 20)

        @component
        class Marker:
            def build(self):
                return Box(10, 10, 10)

        board = Board()
        marker = Marker().attach(
            board,
            parent="front_tangent",
            child=AnchorFrame(),
        )

        commands = compile_assembly(board + marker, "TopologyAnchor")["commands"]
        self.assertFalse(
            any(command["command"] == "joint.origin" for command in commands)
        )
        joint = next(
            command["params"]
            for command in commands
            if command["command"] == "joint.create"
        )
        self.assertEqual(
            joint["a"],
            {
                "occurrence": "Board",
                "edge": [-20.0, 0.0, 5.0],
                "on": [-20.0, 10.0, 10.0],
                "corner": [-20.0, 0.0, 5.0],
                "z": [0.0, 1.0, 0.0],
                "x": [0.0, 0.0, 1.0],
            },
        )

    def test_direct_topology_anchor_is_inlined(self):
        from scpf.assembly import compile_assembly
        from scpf.core import AnchorFrame, AnchorTopology, Box
        from scpf.runner import component

        @component
        class BaseBlock:
            def build(self):
                return Box(20, 20, 10)

        @component
        class ChildBlock:
            def build(self):
                return Box(20, 20, 10)

        base = BaseBlock()
        child = ChildBlock().attach(
            base,
            parent=AnchorTopology(
                edge=(10, 0, 5),
                on=(0, 0, 5),
                corner=(10, 0, 0),
                z=(0, 0, -1),
                x=(-1, 0, 0),
            ),
            child=AnchorFrame(),
        )
        joint = next(
            command["params"]
            for command in compile_assembly(base + child, "DirectTopology")["commands"]
            if command["command"] == "joint.create"
        )
        self.assertEqual(joint["a"]["edge"], [10.0, 0.0, 5.0])
        self.assertEqual(joint["a"]["corner"], [10.0, 0.0, 0.0])
        self.assertEqual(joint["a"]["z"], [0.0, 0.0, -1.0])

    def test_named_topology_anchor_rejects_rotated_occurrence(self):
        from scpf.assembly import compile_assembly
        from scpf.compiler import ModelError
        from scpf.core import Anchor, AnchorTopology, Axis, Box
        from scpf.runner import component

        @component
        class Board:
            def anchors(self):
                return {
                    "edge_mount": AnchorTopology(
                        edge=(10, 0, 5),
                        on=(0, 0, 5),
                    )
                }

            def build(self):
                return Box(20, 20, 10)

        board = Board(placement=Placement(rotation=(Axis.Z, 90)))
        child = Board().attach(board, parent="edge_mount", child=Anchor.LEFT)

        with self.assertRaisesRegex(
            ModelError, "rotated relationship Placement is not replay-safe"
        ):
            compile_assembly(board + child, "RotatedTopologyAnchor")


    def test_direct_anchor_frame_rigid_attach_fixes_mating_angle(self):
        from scpf.assembly import compile_assembly
        from scpf.core import Anchor, AnchorFrame, Box
        from scpf.runner import component

        @component
        class Base:
            def build(self):
                return Box(40, 30, 20)

        @component
        class Bracket:
            def build(self):
                return Box(10, 4, 10)

        base = Base()
        child_frame = AnchorFrame(
            origin=(0, 0, 0),
            z=Anchor.FRONT,
            x=Anchor.RIGHT,
        )
        bracket = Bracket().attach(
            base,
            parent=Anchor.FRONT_TOP_LEFT,
            child=child_frame,
        )

        commands = compile_assembly(base + bracket, "RigidFrame")["commands"]
        joint = next(
            row["params"]
            for row in commands
            if row["command"] == "joint.create"
        )
        self.assertEqual(joint["type"], "rigid")
        self.assertEqual(joint["angle"], 0.0)

    def test_direct_anchor_frame_planar_attach_fixes_mating_angle(self):
        from scpf.assembly import compile_assembly
        from scpf.core import AnchorFrame, Box
        from scpf.runner import component

        @component
        class Base:
            def build(self):
                return Box(40, 30, 20)

        @component
        class Marker:
            def build(self):
                return Box(10, 10, 10)

        parent = AnchorFrame(
            origin=(0, 0, 0),
            z=(0, 0, -1),
            x=(0, -1, 0),
        )
        child = AnchorFrame(
            origin=(0, 0, 0),
            z=(0, 0, 1),
            x=(0, 1, 0),
        )
        base = Base()
        marker = Marker().attach(
            base,
            parent=parent,
            child=child,
            offset=(10, 20),
        )

        commands = compile_assembly(base + marker, "PlanarFrames")["commands"]
        joint = next(
            row["params"]
            for row in commands
            if row["command"] == "joint.create"
        )
        self.assertEqual(joint["type"], "planar")
        self.assertEqual(joint["values"], [10.0, 20.0, 0.0])
        self.assertEqual(joint["angle"], 0.0)

    def test_direct_anchor_frame_attachment_is_inlined(self):
        from scpf.assembly import compile_assembly
        from scpf.core import Anchor, AnchorFrame, Box
        from scpf.runner import component

        @component
        class Base:
            def build(self):
                return Box(40, 40, 40)

        @component
        class Bracket:
            def build(self):
                return Box(10, 10, 10)

        base = Base()
        mount = AnchorFrame(
            origin=(0, 0, -5),
            z=(0, 1, 0),
            x=(0, 0, -1),
        )
        bracket = Bracket().attach(
            base,
            parent=Anchor.FRONT_TOP_RIGHT,
            child=mount,
        )

        commands = compile_assembly(base + bracket, "DirectFrame")["commands"]
        self.assertFalse(
            any(command["command"] == "joint.origin" for command in commands)
        )
        joint = next(
            command["params"]
            for command in commands
            if command["command"] == "joint.create"
        )
        self.assertEqual(
            joint["b"],
            {
                "occurrence": "Bracket",
                "point": [0.0, 0.0, -5.0],
                "z": [0.0, 1.0, 0.0],
                "x": [0.0, 0.0, -1.0],
            },
        )

    def test_direct_anchor_frame_rejects_rotated_occurrence(self):
        from scpf.assembly import compile_assembly
        from scpf.compiler import ModelError
        from scpf.core import Anchor, AnchorFrame, Axis, Box
        from scpf.runner import component

        @component
        class Block:
            def build(self):
                return Box(20, 20, 20)

        base = Block()
        child = Block(placement=Placement(rotation=(Axis.Z, 90))).attach(
            base,
            parent=Anchor.RIGHT,
            child=AnchorFrame(),
        )

        with self.assertRaisesRegex(
            ModelError, "rotated relationship Placement is not replay-safe"
        ):
            compile_assembly(base + child, "RotatedDirectFrame")

    def test_generated_joint_glyphs_are_hidden_after_assembly_compile(self):
        from scpf.assembly import compile_assembly
        from scpf.core import Anchor, Box
        from scpf.runner import component

        class BaseBlock:
            def build(self):
                return Box(20, 20, 10)

        class ChildBlock:
            def build(self):
                return Box(20, 20, 10)

        BaseBlockObject = component(BaseBlock)
        ChildBlockObject = component(ChildBlock)
        base = BaseBlockObject()
        child = ChildBlockObject().attach(
            base,
            parent=Anchor.RIGHT,
            child=Anchor.LEFT,
        )

        commands = compile_assembly(base + child, "HiddenJointGlyphs")["commands"]
        self.assertEqual(
            commands[-1],
            {
                "command": "browser.visibility",
                "params": {"folder": "joints", "visible": False},
            },
        )
        self.assertTrue(
            any(command["command"] == "joint.create" for command in commands[:-1])
        )

        no_joint_commands = compile_assembly(BaseBlockObject(), "NoJoints")["commands"]
        self.assertFalse(
            any(command["command"] == "browser.visibility"
                for command in no_joint_commands)
        )

    def test_rotated_custom_anchor_is_rejected_without_occurrence_move_fallback(self):
        from scpf import Anchor, AnchorFrame, Axis, Box, component
        from scpf.assembly import compile_assembly
        from scpf.compiler import ModelError

        @component
        class Arm:
            def anchors(self):
                return {
                    "tip": AnchorFrame(
                        origin=(20, 0, 5),
                        z=Anchor.RIGHT,
                        x=Anchor.UP,
                    ),
                }

            def build(self):
                return Box(40, 10, 10)

        @component
        class Marker:
            def anchors(self):
                return {
                    "mount": AnchorFrame(
                        origin=(0, 0, 5),
                        z=Anchor.LEFT,
                        x=Anchor.UP,
                    ),
                }

            def build(self):
                return Box(10, 10, 10)

        arm = Arm(placement=Placement(rotation=(Axis.Z, 90)))
        marker = Marker().attach(arm, parent="tip", child="mount")

        with self.assertRaisesRegex(
            ModelError,
            "rotated relationship Placement is not replay-safe",
        ):
            compile_assembly(arm + marker, "RotatedCustomAnchor")

    def test_composed_directions_are_valid_assembly_anchors(self):
        from scpf import Anchor, BOTTOM, FRONT, LEFT, TOP, Box
        from scpf.assembly import compile_assembly
        from scpf.runner import component

        @component
        class BaseBlock:
            def build(self):
                return Box(40, 30, 10)

        @component
        class ChildBlock:
            def build(self):
                return Box(40, 30, 10)

        base = BaseBlock(name="base")
        child = ChildBlock(name="child")
        child = child.attach(
            base,
            parent=FRONT + TOP + LEFT,
            child=FRONT + BOTTOM + LEFT,
        )

        self.assertIs(child.attachment.parent, Anchor.FRONT_TOP_LEFT)
        self.assertIs(child.attachment.child, Anchor.FRONT_BOTTOM_LEFT)

        commands = compile_assembly(base + child, "DirectionalAttach")["commands"]
        joint = next(
            command["params"]
            for command in commands
            if command["command"] == "joint.create"
        )
        self.assertEqual(joint["type"], "rigid")
        self.assertIn("corner", joint["a"])
        self.assertEqual(joint["b"]["point"], [-20.0, -16.0, 10.0])
        self.assertEqual(joint["b"]["z"], [0.0, -1.0, 0.0])
        self.assertEqual(joint["b"]["occurrence"], "ChildBlock")

    def test_corner_anchor_compiles_to_native_edge_and_corner_origins(self):
        commands = run_script(
            ROOT / "examples/corner-anchor/scpf/model.py"
        )["commands"]

        joint = next(
            command["params"]
            for command in commands
            if command["command"] == "joint.create"
        )
        self.assertEqual(joint["type"], "rigid")
        self.assertEqual(
            joint["a"],
            {
                "occurrence": "Base",
                "edge": [20.0, -15.0, 10.0],
                "on": [0.0, -15.0, 10.0],
                "corner": [20.0, -15.0, 20.0],
            },
        )
        self.assertEqual(
            joint["b"],
            {
                "occurrence": "Marker",
                "point": [5.0, 5.0, 10.0],
                "z": [0.0, 1.0, 0.0],
                "x": [-1.0, 0.0, 0.0],
            },
        )

    def test_as_built_copy_is_rejected_without_copy_selector(self):
        from scpf.assembly import compile_assembly
        from scpf.compiler import ModelError
        from scpf.core import Box
        from scpf.runner import component

        class Block:
            def build(self):
                return Box(20, 20, 10)

        BlockObject = component(Block)
        base = BlockObject()
        child = BlockObject(placement=Placement(x=40)).attach(
            base,
            as_built=True,
        )

        with self.assertRaisesRegex(
            ModelError,
            "attachment involving a copied occurrence",
        ):
            compile_assembly(base + child, "AsBuiltAttach")

    def test_attach_angle_is_emitted_as_native_joint_turn(self):
        from scpf.assembly import compile_assembly
        from scpf.core import Anchor, Box
        from scpf.runner import component

        class BaseBlock:
            def build(self):
                return Box(20, 20, 10)

        class ZeroBlock:
            def build(self):
                return Box(20, 20, 10)

        class QuarterBlock:
            def build(self):
                return Box(20, 20, 10)

        BaseBlockObject = component(BaseBlock)
        ZeroBlockObject = component(ZeroBlock)
        QuarterBlockObject = component(QuarterBlock)
        base = BaseBlockObject()
        zero = ZeroBlockObject().attach(
            base,
            parent=Anchor.RIGHT,
            child=Anchor.LEFT,
            angle=0,
        )
        quarter = QuarterBlockObject().attach(
            base,
            parent=Anchor.TOP,
            child=Anchor.BOTTOM,
            angle=90,
        )

        commands = compile_assembly(
            base + zero + quarter,
            "AngleAttach",
        )["commands"]
        joints = [
            command["params"]
            for command in commands
            if command["command"] == "joint.create"
        ]
        self.assertEqual([joint["type"] for joint in joints], ["rigid", "rigid"])
        self.assertEqual([joint["angle"] for joint in joints], [0, 90])

    def test_attach_seed_includes_current_offset_and_gap_values(self):
        from scpf.core import Anchor, Box, Parameter
        from scpf.model_objects import ModelDefinition, ModelInstance

        definition = ModelDefinition("Block", (), Box(40, 30, 10))
        base = ModelInstance(definition)
        gap = Parameter("gap", 5)

        child = ModelInstance(definition).attach(
            base,
            parent=Anchor.TOP,
            child=Anchor.BOTTOM,
            offset=(10, -2),
            gap=gap,
        )

        self.assertEqual(child.placement.position, (10.0, -2.0, 15.0))
        self.assertIs(child.attachment.gap, gap)
        self.assertEqual(child.attachment.offset, (10, -2))

    def test_parametric_attach_keeps_in_plane_offset_expression(self):
        from scpf.assembly import compile_assembly
        from scpf.core import Anchor, Box, Parameter
        from scpf.model_objects import ModelDefinition, ModelInstance

        left_definition = ModelDefinition("LeftBlock", (), Box(40, 30, 10))
        right_definition = ModelDefinition("RightBlock", (), Box(40, 30, 10))
        left = ModelInstance(left_definition)
        wood = Parameter("wood_thickness", 18)
        right = ModelInstance(right_definition).attach(
            left,
            parent=Anchor.RIGHT,
            child=Anchor.LEFT,
            offset=(0, -wood + 12),
        )
        self.assertEqual(right.placement.position, (40.0, 0.0, -6.0))

        commands = compile_assembly(left + right, "ParametricOffset")["commands"]
        parameter = next(
            command["params"]
            for command in commands
            if command["command"] == "parameters.add"
            and command["params"]["name"] == "wood_thickness"
        )
        self.assertEqual(parameter["expression"], "18 mm")

        joint = next(
            command["params"]
            for command in commands
            if command["command"] == "joint.create"
        )
        self.assertEqual(joint["type"], "planar")
        self.assertEqual(
            joint["values"],
            [0, "-(wood_thickness) + 12 mm", 0.0],
        )


    def test_parametric_attach_keeps_gap_as_native_joint_expression(self):
        commands = run_script(
            ROOT / "examples/parametric-attach/scpf/model.py"
        )["commands"]

        gap = next(
            command["params"]
            for command in commands
            if command["command"] == "parameters.add"
            and command["params"]["name"] == "gap"
        )
        self.assertEqual(gap["expression"], "10 mm")

        joint = next(
            command["params"]
            for command in commands
            if command["command"] == "joint.create"
        )
        self.assertEqual(joint["type"], "rigid")
        self.assertEqual(joint["offset"], "gap")



if __name__ == "__main__":
    unittest.main()
