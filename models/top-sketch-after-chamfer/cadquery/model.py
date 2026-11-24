"""CadQuery reference for a chamfered plate with one through hole."""

import cadquery as cq


plate = (
    cq.Workplane("XY")
    .box(100, 70, 10, centered=(True, True, False))
    .edges("|Z")
    .chamfer(8)
    .faces(">Z")
    .workplane()
    .hole(12)
)

model = cq.Assembly()
model.add(plate, name="top_sketch_after_chamfer")
