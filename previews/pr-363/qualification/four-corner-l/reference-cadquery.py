"""CadQuery reference for four short L profiles around a rounded frame."""

import cadquery as cq


frame = (
    cq.Workplane("XY")
    .box(120, 80, 60, centered=(True, True, False))
    .edges("|Z")
    .fillet(8)
    .val()
)

horizontal = cq.Solid.makeBox(32, 4, 16, cq.Vector(-4, -4, -8))
vertical = cq.Solid.makeBox(4, 32, 16, cq.Vector(-4, -4, -8))
profile = horizontal.fuse(vertical)

model = cq.Assembly()
model.add(frame, name="frame")
for index, (x, y, angle) in enumerate([
    (-60, -40, 0),
    (60, -40, 90),
    (60, 40, 180),
    (-60, 40, 270),
]):
    loc = (
        cq.Location((x, y, 30))
        * cq.Location(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), angle)
    )
    model.add(profile, name=f"profile_{index}", loc=loc)
