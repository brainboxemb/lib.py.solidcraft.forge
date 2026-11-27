"""Contracts for engine-neutral reusable-component and assembly IR."""
import unittest

from scpf import (
    Anchor,
    AnchorFrame,
    Box,
    Parameter,
    Placement,
    assembly,
    component,
)
from scpf.assembly_ir import (
    AnchorFrameIR,
    AssemblyAnchorIR,
    AssemblyIR,
    ComponentDefinitionIR,
    OccurrenceIR,
    OccurrencePlacementIR,
    RelationshipIR,
    normalize_assembly,
)
from scpf.ir import BoxIR, PlacementIR


@component(include=("width",))
class AssemblyIRBlock:
    width = 40.0
    depth = 30.0
    height = 10.0

    def build(self):
        return Box(
            self.width,
            self.depth,
            self.height,
            anchor=Anchor.BOTTOM,
        )

    def anchors(self):
        return {
            "mount": AnchorFrame(
                origin=(self.width / 2, 0, self.height / 2),
                z=(1, 0, 0),
                x=(0, 0, 1),
            )
        }


@assembly
class AssemblyIRPair:
    spacing = 60.0

    def build(self):
        left = AssemblyIRBlock(name="left")
        right = left.copy(
            name="right",
            placement=Placement(x=self.spacing),
        )
        return (left + right).group("Pair")


class AssemblyIRTests(unittest.TestCase):
    def test_definitions_occurrences_and_placement_are_semantic(self):
        spacing = Parameter("spacing", 60)
        first = AssemblyIRBlock(
            name="first",
            placement=Placement(x=spacing),
        )
        second = first.copy(
            name="second",
            placement=Placement(
                x=120,
                rotation=((0, 0, 1), 90),
            ),
        )

        model = normalize_assembly(first + second)
        self.assertIsInstance(model, AssemblyIR)
        self.assertEqual(len(model.definitions), 1)
        self.assertEqual(len(model.occurrences), 2)

        definition = model.definitions[0]
        self.assertIsInstance(definition, ComponentDefinitionIR)
        self.assertEqual(definition.id, "definition_1")
        self.assertIsInstance(definition.model.root, PlacementIR)
        self.assertIsInstance(definition.model.root.primitive, BoxIR)
        self.assertEqual(definition.exported_features, ())
        self.assertIn("mount", dict(definition.anchors))
        self.assertIsInstance(dict(definition.anchors)["mount"], AnchorFrameIR)
        self.assertEqual(
            definition.bounds,
            ((-20.0, 20.0), (-15.0, 15.0), (0, 10.0)),
        )

        first_ir, second_ir = model.occurrences
        self.assertEqual(first_ir.id, "occurrence_1")
        self.assertEqual(second_ir.id, "occurrence_2")
        self.assertEqual(first_ir.definition, "definition_1")
        self.assertIs(first_ir.placement.position[0], spacing)
        self.assertEqual(
            second_ir.placement,
            OccurrencePlacementIR(
                (120, 0, 0),
                rotation_axis=(0.0, 0.0, 1.0),
                rotation_angle=90.0,
            ),
        )

        # Process-local ModelInstance ids and backend replay variables never
        # become semantic AssemblyIR identity.
        text = repr(model)
        self.assertNotIn(str(first.occurrence_id), text)
        self.assertNotIn(str(second.occurrence_id), text)
        self.assertNotIn("$", text)

    def test_group_and_imported_assembly_preserve_occurrence_meaning(self):
        model = normalize_assembly(AssemblyIRPair())
        self.assertEqual(
            [occurrence.group for occurrence in model.occurrences],
            ["Pair", "Pair"],
        )
        self.assertEqual(
            [occurrence.name for occurrence in model.occurrences],
            ["left", "right"],
        )
        self.assertEqual(
            [occurrence.id for occurrence in model.occurrences],
            ["occurrence_1", "occurrence_2"],
        )

    def test_rigid_planar_revolute_and_as_built_relationships_are_semantic(self):
        parent = AssemblyIRBlock(name="parent")

        rigid = AssemblyIRBlock(name="rigid").attach(
            parent,
            parent=Anchor.RIGHT,
            child=Anchor.LEFT,
            gap=4,
        )
        rigid_ir = normalize_assembly(parent + rigid)
        relationship = rigid_ir.relationships[0]
        self.assertEqual(relationship.kind, "rigid")
        self.assertEqual(relationship.parent, "occurrence_1")
        self.assertEqual(relationship.child, "occurrence_2")
        self.assertEqual(relationship.parent_anchor.value, "right")
        self.assertEqual(relationship.child_anchor.value, "left")
        self.assertEqual(relationship.gap, 4)

        planar = AssemblyIRBlock(name="planar").attach(
            parent,
            parent=Anchor.TOP,
            child=Anchor.BOTTOM,
            offset=(3, 5),
        )
        planar_ir = normalize_assembly(parent + planar).relationships[0]
        self.assertEqual(planar_ir.kind, "planar")
        self.assertEqual(planar_ir.offset, (3, 5))

        revolute = AssemblyIRBlock(name="moving").attach(
            parent,
            parent="mount",
            child="mount",
            kind="revolute",
            value=45,
            limits=(0, 120),
            flip=True,
            name="Hinge",
        )
        revolute_ir = normalize_assembly(parent + revolute).relationships[0]
        self.assertEqual(
            revolute_ir,
            RelationshipIR(
                child="occurrence_2",
                parent="occurrence_1",
                kind="revolute",
                parent_anchor=revolute_ir.parent_anchor,
                child_anchor=revolute_ir.child_anchor,
                value=45.0,
                limits=(0.0, 120.0),
                flip=True,
                name="Hinge",
            ),
        )
        self.assertEqual(revolute_ir.parent_anchor.kind, "named")
        self.assertEqual(revolute_ir.parent_anchor.value, "mount")

        as_built = AssemblyIRBlock(
            name="as_built",
            placement=Placement(x=80),
        ).attach(parent, as_built=True)
        as_built_ir = normalize_assembly(parent + as_built).relationships[0]
        self.assertTrue(as_built_ir.as_built)
        self.assertEqual(as_built_ir.kind, "rigid")
        self.assertIsNone(as_built_ir.parent_anchor)
        self.assertIsNone(as_built_ir.child_anchor)

    def test_assembly_owned_anchor_uses_semantic_occurrence_reference(self):
        base = AssemblyIRBlock(name="base")
        assembly_value = (base + base.copy(
            name="copy",
            placement=Placement(x=60),
        )).with_anchor(
            "front_mount",
            base,
            "mount",
            offset=(2, 3),
        )
        model = normalize_assembly(assembly_value)
        self.assertEqual(
            model.anchors,
            (
                AssemblyAnchorIR(
                    name="front_mount",
                    target="occurrence_1",
                    reference=model.anchors[0].reference,
                    offset=(2, 3),
                ),
            ),
        )
        self.assertEqual(model.anchors[0].reference.kind, "named")
        self.assertEqual(model.anchors[0].reference.value, "mount")

    def test_semantic_ir_validates_missing_relationship_targets(self):
        definition = ComponentDefinitionIR(
            id="definition_1",
            class_name="Block",
            model=normalize_assembly(AssemblyIRBlock()).definitions[0].model,
            parameters=(),
            fixed_inputs=(),
            external_parameters=(),
            input_bindings=(),
            anchors=(),
            exported_features=(),
        )
        occurrence = OccurrenceIR(
            id="occurrence_1",
            definition="definition_1",
            placement=OccurrencePlacementIR((0, 0, 0)),
        )
        with self.assertRaises(ValueError):
            AssemblyIR(
                definitions=(definition,),
                occurrences=(occurrence,),
                relationships=(
                    RelationshipIR(
                        child="occurrence_1",
                        parent="occurrence_2",
                        kind="rigid",
                        parent_anchor=None,
                        child_anchor=None,
                        as_built=True,
                    ),
                ),
            )


if __name__ == "__main__":
    unittest.main()
