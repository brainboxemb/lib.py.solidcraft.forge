"""PythonSCAD geometry reference for the qualified 90-degree sheet fold."""

from math import cos, pi, sin
from pythonscad import *

R_INNER = 2.0
THICKNESS = 2.0
R_OUTER = R_INNER + THICKNESS
X_TANGENT = 17.64380551
Z_TOP = 21.64380551
CENTER = (X_TANGENT, 4.0)
SEGMENTS = 32


def arc_points(radius, start, end, count=SEGMENTS):
    return [
        [
            CENTER[0] + radius * cos(start + (end - start) * i / count),
            CENTER[1] + radius * sin(start + (end - start) * i / count),
        ]
        for i in range(count + 1)
    ]


outer = arc_points(R_OUTER, -pi / 2, 0)
inner = list(reversed(arc_points(R_INNER, -pi / 2, 0)))

profile = [
    [-40.0, 0.0],
    *outer,
    [X_TANGENT + R_OUTER, Z_TOP],
    [X_TANGENT + R_INNER, Z_TOP],
    *inner,
    [-40.0, 2.0],
]

sheet = (
    polygon(profile)
    .linear_extrude(height=40)
    .rotate([90, 0, 0])
    .translate([0, 20, 0])
)
hole = cylinder(d=6, h=4).translate([-20, 0, -1])
model = sheet - hole
