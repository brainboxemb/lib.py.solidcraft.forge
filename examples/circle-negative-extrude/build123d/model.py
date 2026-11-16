"""build123d reference: a diameter-20 cylinder extruded down from Z=0."""
from build123d import Cylinder, Pos

model = Pos(0, 0, -15) * Cylinder(10, 30)
