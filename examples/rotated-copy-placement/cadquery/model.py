"""CadQuery reference for one translated and X-rotated copied panel."""

import cadquery as cq


panel = cq.Solid.makeBox(
    20,
    10,
    2,
    cq.Vector(-10, -5, 0),
)

model = cq.Assembly()
model.add(panel, name="fixed")
model.add(
    panel,
    name="rotated",
    loc=cq.Location(
        cq.Vector(30, 0, 40),
        cq.Vector(1, 0, 0),
        90,
    ),
)
