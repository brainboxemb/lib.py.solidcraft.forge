"""CadQuery reference for two short L profiles on each vertical frame corner."""

import cadquery as cq


frame = (
    cq.Workplane("XY")
    .box(120, 80, 60, centered=(True, True, False))
    .edges("|Z")
    .fillet(8)
    .val()
)

horizontal = cq.Solid.makeBox(32, 4, 16, cq.Vector(-4, -4, 0))
vertical = cq.Solid.makeBox(4, 32, 16, cq.Vector(-4, -4, 0))
profile = horizontal.fuse(vertical)

model = cq.Assembly()
model.add(frame, name="frame")
for corner, (x, y, angle) in enumerate([
    (-60, -40, 0),
    (60, -40, 90),
    (60, 40, 180),
    (-60, 40, 270),
]):
    rotation = cq.Location(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), angle)
    for level, z in (("low", 0), ("high", 44)):
        model.add(
            profile,
            name=f"profile_{corner}_{level}",
            loc=cq.Location((x, y, z)) * rotation,
        )
