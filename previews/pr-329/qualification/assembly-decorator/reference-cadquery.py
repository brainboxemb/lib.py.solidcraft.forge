"""CadQuery assembly reference for the reusable PostPair geometry."""

import cadquery as cq


post = cq.Solid.makeBox(
    10,
    10,
    20,
    cq.Vector(-5, -5, 0),
)

model = cq.Assembly()
model.add(post, name="left", loc=cq.Location((-15, 0, 0)))
model.add(post, name="right", loc=cq.Location((15, 0, 0)))
