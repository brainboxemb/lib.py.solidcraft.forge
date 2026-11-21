"""CadQuery reference for two independently placed rotated panel occurrences."""

import cadquery as cq

# The Forge definition is 20 x 10 x 4 and each occurrence is rotated Z+90,
# giving a centred 10 x 20 x 4 world envelope.
panel = cq.Solid.makeBox(
    20,
    10,
    4,
    cq.Vector(-10, -5, -2),
)
rotation = cq.Location(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 90)

model = cq.Assembly()
model.add(panel, name="left", loc=cq.Location((-40, 0, 0)) * rotation)
model.add(panel, name="right", loc=cq.Location((40, 0, 0)) * rotation)
