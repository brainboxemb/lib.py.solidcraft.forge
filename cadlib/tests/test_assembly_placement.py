"""Reusable model objects and native SolidCraft assembly command tests."""
from pathlib import Path
import tempfile
import unittest

from scpf.runner import run_script
from scpf.model_objects import Placement

ROOT = Path(__file__).resolve().parents[2]

class AssemblyPlacementTests(unittest.TestCase):
    def test_components_example_uses_placement_without_joint(self):
        commands = run_script(
            ROOT / "examples/components/scpf/model.py"
        )["commands"]

        copies = [
            command["params"]
            for command in commands
            if command["command"] == "occurrence.copy"
        ]
        self.assertEqual(
            copies,
            [{"component": "Block", "translate": [40.0, 0.0, 0.0]}],
        )
        self.assertFalse(any(
            command["command"] == "joint.create"
            for command in commands
        ))
        self.assertFalse(any(
            command["command"] == "occurrence.move"
            for command in commands
        ))

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

    def test_replay_variable_names_do_not_depend_on_process_occurrence_ids(self):
        from scpf import Box, Placement, Z, component
        from scpf.assembly import compile_assembly

        @component
        class Panel:
            def build(self):
                return Box(20, 10, 2)

        def build_commands():
            first = Panel()
            second = first.copy(
                placement=Placement(x=30, rotation=(Z, 90)),
            )
            return compile_assembly(first + second, "Panels")["commands"]

        first_run = build_commands()
        second_run = build_commands()
        self.assertEqual(first_run, second_run)
        self.assertIn(
            {"$panel_occurrence_1": "occurrence"},
            [command.get("bind") for command in first_run],
        )
        self.assertIn(
            {"$panel_occurrence_2": "occurrence"},
            [command.get("bind") for command in first_run],
        )

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

    def test_first_nonidentity_occurrence_uses_replay_variable(self):
        from scpf import Box, Placement, component
        from scpf.assembly import compile_assembly

        @component
        class Panel:
            def build(self):
                return Box(20, 10, 2)

        moved = Panel(placement=Placement(x=30))
        identity = moved.copy(placement=Placement())
        commands = compile_assembly(moved + identity, "Panels")["commands"]

        create = next(
            command
            for command in commands
            if command["command"] == "component.create"
            and command["params"]["name"] == "Panel"
        )
        self.assertEqual(
            create["bind"],
            {"$panel_occurrence_1": "occurrence"},
        )
        copy = next(
            command
            for command in commands
            if command["command"] == "occurrence.copy"
        )
        self.assertNotIn("translate", copy["params"])
        move = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
        )
        self.assertEqual(move["occurrence"], "$panel_occurrence_1")
        self.assertEqual(move["translate"], [30, 0, 0])

    def test_definition_without_identity_occurrence_is_replayable(self):
        from scpf import Box, Placement, component
        from scpf.assembly import compile_assembly

        @component
        class Panel:
            def build(self):
                return Box(20, 10, 2)

        left = Panel(placement=Placement(x=-30))
        right = left.copy(placement=Placement(x=30))
        commands = compile_assembly(left + right, "Panels")["commands"]

        copy = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.copy"
        )
        self.assertEqual(copy["translate"], [30, 0, 0])
        move = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
        )
        self.assertEqual(move["occurrence"], "$panel_occurrence_1")
        self.assertEqual(move["translate"], [-30, 0, 0])

    def test_parametric_root_placement_stays_ungrounded_in_solidcraft_042(self):
        from scpf import Box, Parameter, Placement, component, half
        from scpf.assembly import compile_assembly

        @component
        class Panel:
            def build(self):
                return Box(20, 10, 2)

        height = Parameter("opening_height", 362)
        panel = Panel(
            placement=Placement(z=half(height)),
        ).group("Panels")

        commands = compile_assembly(panel, "Display")["commands"]
        create = next(
            command["params"]
            for command in commands
            if command["command"] == "component.create"
            and command["params"]["name"] == "Panel"
        )
        self.assertFalse(create["grounded"])
        self.assertEqual(create["parent"], "Panels")

        move = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
        )
        self.assertEqual(move["occurrence"], "$panel")
        self.assertIn("opening_height", str(move["translate"][2]))
        self.assertNotIn("move_grounded", move)

    def test_fixed_root_placement_keeps_grounded_behaviour(self):
        from scpf import Box, Placement, component
        from scpf.assembly import compile_assembly

        @component
        class Panel:
            def build(self):
                return Box(20, 10, 2)

        panel = Panel(
            placement=Placement(x=30),
        )
        commands = compile_assembly(panel, "Display")["commands"]

        create = next(
            command["params"]
            for command in commands
            if command["command"] == "component.create"
            and command["params"]["name"] == "Panel"
        )
        self.assertTrue(create["grounded"])

        move = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
        )
        self.assertEqual(move["occurrence"], "$panel")
        self.assertEqual(move["translate"], [30, 0, 0])
        self.assertTrue(move["move_grounded"])

    def test_symbolic_ordinary_copy_placement_uses_replay_variable(self):
        from scpf import Box, Parameter, Placement, component
        from scpf.assembly import compile_assembly

        @component
        class Panel:
            def build(self):
                return Box(20, 10, 2)

        first = Panel()
        second = first.copy(
            placement=Placement(x=Parameter("offset", 30)),
        )
        commands = compile_assembly(first + second, "Panels")["commands"]

        copy = next(
            command
            for command in commands
            if command["command"] == "occurrence.copy"
        )
        self.assertNotIn("translate", copy["params"])
        self.assertEqual(
            copy["bind"],
            {"$panel_occurrence_2": "occurrence"},
        )
        move = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
        )
        self.assertEqual(move["occurrence"], "$panel_occurrence_2")
        self.assertEqual(move["translate"], ["offset", 0, 0])

    def test_rotated_ordinary_copy_placement_uses_replay_variable(self):
        from scpf import Box, Placement, Z, component
        from scpf.assembly import compile_assembly

        @component
        class Panel:
            def build(self):
                return Box(20, 10, 2)

        first = Panel()
        second = first.copy(
            placement=Placement(x=30, rotation=(Z, 180)),
        )
        commands = compile_assembly(first + second, "Panels")["commands"]

        copy = next(
            command
            for command in commands
            if command["command"] == "occurrence.copy"
        )
        self.assertNotIn("translate", copy["params"])
        move = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
        )
        self.assertEqual(move["occurrence"], "$panel_occurrence_2")
        self.assertEqual(move["translate"], [30, 0, 0])
        self.assertEqual(move["axis"], [0.0, 0.0, 1.0])
        self.assertEqual(move["angle"], "180 deg")

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

    def test_rotated_copy_replays_through_bound_occurrence(self):
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
            commands = run_script(script)["commands"]

        move = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
        )
        self.assertTrue(move["occurrence"].startswith("$"))
        self.assertEqual(move["translate"], [40, 0, 0])
        self.assertEqual(move["angle"], "180 deg")

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
        self.assertFalse(created[0]["grounded"])
        self.assertEqual(created[1]["parent"], "HUB75Panels")
        self.assertTrue(created[1]["grounded"])
        self.assertNotIn("parent", created[2])
        copies = [c for c in commands if c["command"] == "occurrence.copy"]
        self.assertEqual(len(copies), 1)
        self.assertEqual(copies[0]["params"]["component"], "Panel")

    def test_named_groups_are_not_grounded_and_physical_root_stays_grounded(self):
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

        created = {
            command["params"]["name"]: command["params"]
            for command in commands
            if command["command"] == "component.create"
        }
        self.assertFalse(created["LeftGroup"]["grounded"])
        self.assertFalse(created["RightGroup"]["grounded"])
        self.assertTrue(created["LeftPart"]["grounded"])
        self.assertFalse(created["RightPart"]["grounded"])

    def test_group_name_conflicts_and_reusable_definition_can_span_groups(self):
        from scpf.core import Box
        from scpf.model_objects import ModelDefinition, ModelInstance, Placement
        from scpf.assembly import compile_assembly
        from scpf.compiler import ModelError

        panel = ModelInstance(ModelDefinition("Panel", (), Box(10, 2, 20)))
        with self.assertRaisesRegex(ValueError, "non-empty"):
            panel.group("")
        with self.assertRaisesRegex(ValueError, "multiple groups"):
            panel.group("One").group("Two")

        assembly = (
            panel.group("A")
            + panel.copy(placement=Placement(x=30)).group("B")
        )
        commands = compile_assembly(assembly, "Display")["commands"]
        panel_creates = [
            command["params"]
            for command in commands
            if command["command"] == "component.create"
            and command["params"]["name"] == "Panel"
        ]
        self.assertEqual(len(panel_creates), 1)
        self.assertEqual(panel_creates[0]["parent"], "A")
        self.assertTrue(panel_creates[0]["grounded"])

        copies = [
            command["params"]
            for command in commands
            if command["command"] == "occurrence.copy"
        ]
        self.assertEqual(len(copies), 1)
        self.assertEqual(copies[0]["component"], "Panel")
        self.assertEqual(copies[0]["parent"], "B")
        self.assertEqual(copies[0]["translate"], [30.0, 0.0, 0.0])

        root_copy = compile_assembly(
            panel.group("A")
            + panel.copy(placement=Placement(x=30)),
            "Display",
        )["commands"]
        root_copy_params = next(
            command["params"]
            for command in root_copy
            if command["command"] == "occurrence.copy"
        )
        self.assertEqual(root_copy_params["parent"], "root")
        self.assertEqual(root_copy_params["translate"], [30.0, 0.0, 0.0])

        grouped_copy = compile_assembly(
            panel
            + panel.copy(placement=Placement(x=30)).group("B"),
            "Display",
        )["commands"]
        grouped_copy_params = next(
            command["params"]
            for command in grouped_copy
            if command["command"] == "occurrence.copy"
        )
        self.assertEqual(grouped_copy_params["parent"], "B")
        self.assertEqual(grouped_copy_params["translate"], [30.0, 0.0, 0.0])

        with self.assertRaisesRegex(ModelError, "conflicts"):
            compile_assembly(panel.group("Panel"), "Display")

    def test_rotation_remains_occurrence_data_and_replays_by_variable(self):
        from scpf.core import Box
        from scpf.model_objects import ModelDefinition, ModelInstance, Placement
        from scpf.assembly import compile_assembly

        first = ModelInstance(ModelDefinition("Panel", (), Box(20, 10, 2)))
        second = first.copy(
            placement=Placement(x=30, rotation=((0, 0, 1), 180))
        )
        self.assertIs(first.definition, second.definition)
        self.assertIsNone(first.placement.rotation)
        self.assertEqual(second.placement.position, (30, 0, 0))
        self.assertEqual(
            second.placement.rotation,
            ((0.0, 0.0, 1.0), 180.0),
        )
        self.assertIsNone(second.attachment)
        self.assertEqual(
            second.copy().placement.rotation,
            second.placement.rotation,
        )

        commands = compile_assembly(first + second, "Display")["commands"]
        move = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
        )
        self.assertEqual(move["occurrence"], "$panel_occurrence_2")
        self.assertEqual(move["angle"], "180 deg")

    def test_placement_accepts_named_axis_rotation(self):
        from scpf.core import X, Y, Z
        from scpf.model_objects import Placement

        self.assertEqual(Placement(rotation=(X, 180)).rotation, ((1.0, 0.0, 0.0), 180.0))
        self.assertEqual(Placement(rotation=(Y, 90)).rotation, ((0.0, 1.0, 0.0), 90.0))
        self.assertEqual(Placement(rotation=(Z, -90)).rotation, ((0.0, 0.0, 1.0), -90.0))
        with self.assertRaisesRegex(ValueError, "X, Y or Z"):
            Placement(rotation=("Q", 90))

    def test_first_grounded_occurrence_rotation_uses_bound_id(self):
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
                "Display()\n",
                encoding="utf-8",
            )
            commands = run_script(path)["commands"]

        move = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
        )
        self.assertEqual(move["occurrence"], "$panel_occurrence_1")
        self.assertEqual(move["translate"], [-50, 0, 0])
        self.assertEqual(move["angle"], "180 deg")
        self.assertTrue(move["move_grounded"])

    def test_rotated_hub75_copies_use_replay_variables(self):
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
            commands = run_script(script)["commands"]

        moves = [
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
        ]
        self.assertEqual(len(moves), 4)
        self.assertTrue(all(
            move["occurrence"].startswith("$panel_occurrence_")
            for move in moves
        ))
        self.assertTrue(all(move["angle"] == "90 deg" for move in moves))

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

    def test_symbolic_ordinary_placement_replays_with_expression_move(self):
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
            commands = run_script(path)["commands"]

        move = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
        )
        self.assertEqual(move["occurrence"], "$panel_occurrence_2")
        self.assertIn("depth", str(move["translate"][1]))

    def test_symbolic_ordinary_copy_placement_keeps_parameter(self):
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
            commands = run_script(path)["commands"]

        parameter = next(
            command["params"]
            for command in commands
            if command["command"] == "parameters.add"
            and command["params"]["name"] == "offset"
        )
        self.assertEqual(parameter["expression"], "30 mm")
        move = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
        )
        self.assertEqual(move["occurrence"], "$panel_occurrence_2")
        self.assertEqual(move["translate"], ["offset", 0, 0])

    def test_symbolic_copy_with_rotation_uses_bound_native_move(self):
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
            commands = run_script(path)["commands"]

        move = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
        )
        self.assertEqual(move["occurrence"], "$strip_occurrence_2")
        self.assertIn("height", str(move["translate"][2]))
        self.assertEqual(move["axis"], [0.0, 1.0, 0.0])
        self.assertEqual(move["angle"], "90 deg")
