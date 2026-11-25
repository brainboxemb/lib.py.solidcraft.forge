"""Native SolidCraft revolute-joint authoring contracts."""

import unittest

from scpf import Anchor, Box, component
from scpf.assembly import compile_assembly


@component
class JointBlock:
    def build(self):
        return Box(40, 30, 3)


class RevoluteJointTests(unittest.TestCase):
    def test_revolute_attachment_lowers_to_native_joint(self):
        fixed = JointBlock(name="fixed")
        moving = JointBlock(name="moving").attach(
            fixed,
            parent=Anchor.RIGHT,
            child=Anchor.LEFT,
            kind="revolute",
            value=60,
            limits=(0, 180),
            flip=True,
            name="Hinge",
        )

        commands = compile_assembly(fixed + moving, "HingeFixture")["commands"]
        joint = next(
            row for row in commands
            if row["command"] == "joint.create"
        )

        self.assertEqual(joint["params"]["type"], "revolute")
        self.assertEqual(joint["params"]["name"], "Hinge")
        self.assertEqual(joint["params"]["values"], [60.0])
        self.assertEqual(joint["params"]["limits"], [[0.0, 180.0]])
        self.assertTrue(joint["params"]["flip"])
        self.assertEqual(
            joint["params"]["a"]["occurrence"],
            "$fixed",
        )
        self.assertEqual(
            joint["params"]["b"]["occurrence"],
            "$moving",
        )

    def test_existing_default_remains_rigid(self):
        fixed = JointBlock(name="fixed")
        moving = JointBlock(name="moving").attach(
            fixed,
            parent=Anchor.RIGHT,
            child=Anchor.LEFT,
        )
        commands = compile_assembly(fixed + moving, "RigidFixture")["commands"]
        joint = next(
            row for row in commands
            if row["command"] == "joint.create"
        )
        self.assertEqual(joint["params"]["type"], "rigid")
        self.assertNotIn("values", joint["params"])
        self.assertNotIn("limits", joint["params"])

    def test_revolute_validation_rejects_ambiguous_inputs(self):
        fixed = JointBlock(name="fixed")
        moving = JointBlock(name="moving")

        with self.assertRaisesRegex(ValueError, "in-plane offset"):
            moving.attach(
                fixed,
                kind="revolute",
                offset=(1, 0),
            )
        with self.assertRaisesRegex(ValueError, "outside its limits"):
            moving.attach(
                fixed,
                kind="revolute",
                value=200,
                limits=(0, 180),
            )
        with self.assertRaisesRegex(ValueError, "require kind='revolute'"):
            moving.attach(
                fixed,
                value=30,
            )


if __name__ == "__main__":
    unittest.main()
