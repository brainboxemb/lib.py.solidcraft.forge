"""CadQuery geometry reference for sketch pattern/mirror qualification."""

import cadquery as cq

CUT_HEIGHT = 9
CUT_Z = -2


def circle_cut(x, y, diameter=8):
    return (
        cq.Workplane("XY")
        .center(x, y)
        .circle(diameter / 2)
        .extrude(CUT_HEIGHT)
        .translate((0, 0, CUT_Z))
    )


def straight_slot(cx, cy, overall_length=28, width=8):
    return (
        cq.Workplane("XY")
        .center(cx, cy)
        .slot2D(overall_length, width)
        .extrude(CUT_HEIGHT)
        .translate((0, 0, CUT_Z))
    )


plate = cq.Workplane("XY").box(240, 160, 5, centered=(True, True, False))
cutters = None

for y in (-45, 45):
    for x in (-60, -35, -10, 15):
        shape = circle_cut(x, y)
        cutters = shape if cutters is None else cutters.union(shape)

for y in (-20, 20):
    for x in (-80, -30, 30, 80):
        shape = straight_slot(x, y)
        cutters = shape if cutters is None else cutters.union(shape)

result = plate.cut(cutters)
model = cq.Assembly()
model.add(result, name="sketch_pattern_mirror")
