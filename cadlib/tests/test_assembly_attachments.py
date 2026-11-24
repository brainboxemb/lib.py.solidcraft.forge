"""Reusable model objects and native SolidCraft assembly command tests."""
from pathlib import Path
import tempfile
import unittest

from scpf.runner import run_script
from scpf.model_objects import Placement

ROOT = Path(__file__).resolve().parents[2]

class AssemblyAttachmentTests(unittest.TestCase):
    def test_repeated_parent_attachments_keep_distinct_targets(self):
        from scpf import Anchor, Box, Placement, component

        @component
        class Parent:
            def build(self):
                return Box(20, 20, 40, anchor=Anchor.BOTTOM)

        @component
        class Marker:
            def build(self):
                return Box(10, 10, 10, anchor=Anchor.BOTTOM)

        left = Parent()
        right = left.copy(placement=Placement(x=60))
        first = Marker().attach(
            left,
            parent=Anchor.TOP,
            child=Anchor.BOTTOM,
        )
        second = first.copy().attach(
            right,
            parent=Anchor.TOP,
            child=Anchor.BOTTOM,
        )

        self.assertNotEqual(left.occurrence_id, right.occurrence_id)
        self.assertNotEqual(first.occurrence_id, second.occurrence_id)
        self.assertEqual(first.definition.key, second.definition.key)
        self.assertEqual(
            first.attachment.target.occurrence_id,
            left.occurrence_id,
        )
        self.assertEqual(
            second.attachment.target.occurrence_id,
            right.occurrence_id,
        )

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

        self.assertIs(
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

    def test_symbolic_relationship_target_placement_uses_bound_id(self):
        from scpf.assembly import compile_assembly
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

        commands = compile_assembly(parent + child, "Pair")["commands"]
        move = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
        )
        self.assertEqual(move["occurrence"], "$panel_occurrence_1")
        self.assertEqual(move["translate"], ["station", 0, 0])
        joint = next(
            command["params"]
            for command in commands
            if command["command"] == "joint.create"
        )
        self.assertEqual(
            joint["a"]["occurrence"],
            "$panel_occurrence_1",
        )
        self.assertEqual(
            joint["b"]["occurrence"],
            "$panel_occurrence_2",
        )

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
                "occurrence": "$base",
                "point": [0.0, 0.0, 0.0],
                "z": [0.0, 0.0, 1.0],
                "x": [1.0, 0.0, 0.0],
            },
        )
        self.assertEqual(
            joints[0]["b"],
            {
                "occurrence": "$frontbracket",
                "point": [0.0, 0.0, 0.0],
                "z": [0.0, 0.0, 1.0],
                "x": [1.0, 0.0, 0.0],
            },
        )
        self.assertEqual(joints[1]["a"]["z"], [0.0, 0.0, -1.0])
        self.assertEqual(joints[1]["b"]["z"], [0.0, 0.0, -1.0])
        self.assertEqual(joints[1]["b"]["occurrence"], "$rearbracket")
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
        self.assertEqual(joint["a"]["occurrence"], "$left")
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
                "occurrence": "$board",
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

    def test_rotated_normal_attachment_rejects_every_reference_type(self):
        from scpf import (
            Anchor,
            AnchorFrame,
            AnchorTopology,
            Axis,
            Box,
            Placement,
            component,
        )
        from scpf.assembly import compile_assembly
        from scpf.compiler import ModelError

        @component
        class Block:
            def build(self):
                return Box(20, 20, 10)

        # This matrix must fail before any Anchor/Frame/Topology lowering.
        references = {
            "anchor": (
                Anchor.RIGHT,
                Anchor.LEFT,
            ),
            "frame": (
                AnchorFrame(origin=(10, 0, 5)),
                AnchorFrame(origin=(-10, 0, 5)),
            ),
            "topology": (
                AnchorTopology(
                    edge=(10, 0, 5),
                    on=(10, 0, 5),
                ),
                AnchorTopology(
                    edge=(-10, 0, 5),
                    on=(-10, 0, 5),
                ),
            ),
        }

        for reference_name, (parent_ref, child_ref) in references.items():
            for rotated_side in ("parent", "child"):
                with self.subTest(
                    reference=reference_name,
                    rotated=rotated_side,
                ):
                    parent = Block(
                        placement=(
                            Placement(rotation=(Axis.Z, 90))
                            if rotated_side == "parent"
                            else Placement()
                        )
                    )
                    child = Block(
                        placement=(
                            Placement(rotation=(Axis.Z, 90))
                            if rotated_side == "child"
                            else Placement()
                        )
                    ).attach(
                        parent,
                        parent=parent_ref,
                        child=child_ref,
                    )

                    with self.assertRaisesRegex(
                        ModelError,
                        "rotated Placement in a normal attachment is not supported yet",
                    ):
                        compile_assembly(
                            parent + child,
                            f"Rotated{reference_name}{rotated_side}",
                        )

    def test_rotated_as_built_attachment_keeps_declared_occurrence_pose(self):
        from scpf import Axis, Box, Placement, component
        from scpf.assembly import compile_assembly

        @component
        class Block:
            def build(self):
                return Box(20, 20, 10)

        parent = Block()
        child = Block(
            placement=Placement(
                x=40,
                rotation=(Axis.Z, 90),
            )
        ).attach(
            parent,
            as_built=True,
        )

        commands = compile_assembly(
            parent + child,
            "RotatedAsBuilt",
        )["commands"]

        move = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
        )
        self.assertEqual(move["occurrence"], "$block_occurrence_2")
        self.assertEqual(move["translate"], [40, 0, 0])
        self.assertEqual(move["axis"], [0.0, 0.0, 1.0])
        self.assertEqual(move["angle"], "90 deg")

        joint = next(
            command["params"]
            for command in commands
            if command["command"] == "joint.as_built"
        )
        self.assertEqual(joint["a"], "$block_occurrence_1")
        self.assertEqual(joint["b"], "$block_occurrence_2")

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
            ModelError, "rotated Placement in a normal attachment is not supported yet"
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
                "occurrence": "$bracket",
                "point": [20.0, -20.0, 20.0],
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
            ModelError, "rotated Placement in a normal attachment is not supported yet"
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
            "rotated Placement in a normal attachment is not supported yet",
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
        # The child has already received its seed Placement. joint.create
        # therefore selects the mating datum at its current world position.
        self.assertEqual(joint["b"]["point"], [-20.0, -15.0, 5.0])
        self.assertEqual(joint["b"]["z"], [0.0, -1.0, 0.0])
        self.assertEqual(joint["b"]["occurrence"], "$child")

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
                "occurrence": "$base",
                "edge": [20.0, -15.0, 10.0],
                "on": [0.0, -15.0, 10.0],
                "corner": [20.0, -15.0, 20.0],
            },
        )
        self.assertEqual(
            joint["b"],
            {
                "occurrence": "$marker",
                "point": [20.0, -15.0, 20.0],
                "z": [0.0, 1.0, 0.0],
                "x": [-1.0, 0.0, 0.0],
            },
        )

    def test_as_built_copy_uses_bound_copy_selector(self):
        from scpf.assembly import compile_assembly
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

        commands = compile_assembly(base + child, "AsBuiltAttach")["commands"]
        copy = next(
            command
            for command in commands
            if command["command"] == "occurrence.copy"
        )
        self.assertEqual(copy["params"]["translate"], [40, 0, 0])
        joint = next(
            command["params"]
            for command in commands
            if command["command"] == "joint.as_built"
        )
        self.assertEqual(joint["a"], "$block_occurrence_1")
        self.assertEqual(joint["b"], "$block_occurrence_2")

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
        from scpf.core import Anchor, Box, Parameter, parameters_in, pv
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

        self.assertEqual(child.placement.position[:2], (10.0, -2.0))
        self.assertEqual(pv(child.placement.position[2]), 15.0)
        self.assertEqual(
            [parameter.name for parameter in parameters_in(
                child.placement.position[2]
            )],
            ["gap"],
        )
        self.assertIs(child.attachment.gap, gap)
        self.assertEqual(child.attachment.offset, (10, -2))

    def test_parametric_attach_keeps_in_plane_offset_expression(self):
        from scpf.assembly import compile_assembly
        from scpf.core import Anchor, Box, Parameter, parameters_in, pv
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
        self.assertEqual(right.placement.position[:2], (40.0, 0))
        self.assertEqual(pv(right.placement.position[2]), -6.0)
        self.assertEqual(
            [parameter.name for parameter in parameters_in(
                right.placement.position[2]
            )],
            ["wood_thickness"],
        )

        commands = compile_assembly(left + right, "ParametricOffset")["commands"]
        seed = next(
            command["params"]
            for command in commands
            if command["command"] == "occurrence.move"
            and command["params"]["occurrence"] == "$rightblock"
        )
        self.assertEqual(seed["translate"][:2], [40.0, 0])
        self.assertEqual(
            seed["translate"][2],
            "-(wood_thickness) + 12 mm",
        )
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
