"""CadQuery geometry reference for the minimal symmetric L bracket."""

import cadquery as cq


horizontal = cq.Solid.makeBox(40, 24, 12, cq.Vector(0, -12, -12))
vertical = cq.Solid.makeBox(12, 24, 40, cq.Vector(0, -12, -40))
bracket = horizontal.fuse(vertical)

model = cq.Assembly()
model.add(bracket, name="bracket")
