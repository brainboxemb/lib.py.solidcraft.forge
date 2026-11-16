"""build123d reference: a diameter-20 sketch extruded down from Z=0."""
from build123d import BuildPart, BuildSketch, Circle, extrude

with BuildPart() as model:
    with BuildSketch():
        Circle(10)
    extrude(amount=-30)
