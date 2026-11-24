"""40 x 30 x 10 mm box, centered in XY and based at Z=0."""
import cadquery as cq

model = cq.Workplane("XY").box(40, 30, 10, centered=(True, True, False))
