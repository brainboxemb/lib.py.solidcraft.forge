"""Qualification: native bounded revolute relationship."""

from scpf import AnchorFrame, Box, assembly, component


@component
class Leaf:
    width = 40.0
    depth = 30.0
    thickness = 3.0

    def anchors(self):
        return {
            "hinge_positive": AnchorFrame(
                origin=(0, 15, 1.5),
                z=(1, 0, 0),
                x=(0, 0, 1),
            ),
            "hinge_negative": AnchorFrame(
                origin=(0, -15, 1.5),
                z=(1, 0, 0),
                x=(0, 0, 1),
            ),
        }

    def build(self):
        return Box(self.width, self.depth, self.thickness)


@assembly
class RevoluteFixture:
    def build(self):
        fixed = Leaf(name="fixed")
        moving = Leaf(name="moving").attach(
            fixed,
            parent="hinge_positive",
            child="hinge_negative",
            kind="revolute",
            value=60,
            limits=(0, 180),
            flip=True,
            name="Hinge",
        )
        return fixed + moving


RevoluteFixture()
