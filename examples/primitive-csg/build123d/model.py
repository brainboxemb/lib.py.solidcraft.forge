"""build123d reference: Builder-mode union, subtraction and intersection."""
from build123d import Box, BuildPart, Cylinder, Locations, Mode, Rot, Sphere

with BuildPart() as model:
    Sphere(20)

    with Locations((18, 0, 10)):
        Box(30, 30, 20)

    with Locations(Rot(0, 90, 0)):
        Cylinder(4, 120, mode=Mode.SUBTRACT)

    with Locations((0, 0, 15)):
        Box(50, 50, 30, mode=Mode.INTERSECT)
