"""CadQuery geometry reference for the Hole family.

The threaded case is represented by its Ø5 M6 tap-drill envelope; SolidCraft
native qualification separately proves thread metadata and modeled thread.
"""
import cadquery as cq

part = cq.Workplane("XY").box(120, 40, 12, centered=(True, True, False))

part = part.faces(">Z").workplane().pushPoints([(-45, 0)]).hole(6)
part = part.faces(">Z").workplane().pushPoints([(-15, 0)]).cboreHole(6, 12, 4)
part = part.faces(">Z").workplane().pushPoints([(15, 0)]).cskHole(6, 12, 90)
part = part.faces(">Z").workplane().pushPoints([(45, 0)]).hole(5)

model = cq.Assembly()
model.add(part, name="hole_family")
