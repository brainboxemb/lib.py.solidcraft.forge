"""build123d 0.12 geometry reference for the qualified 90-degree sheet fold.

build123d's make_brake_formed helper is not used here because the pinned 0.12
implementation fails to solidify this small R2 / 2 mm fixture. The reference
instead builds the exact folded XZ section independently and extrudes it across
the 40 mm width.
"""

from math import cos, pi, sin

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Cylinder,
    Locations,
    Mode,
    Plane,
    Polygon,
    extrude,
)

R_INNER = 2.0
THICKNESS = 2.0
R_OUTER = R_INNER + THICKNESS
X_TANGENT = 17.64380551
Z_TOP = 21.64380551
CENTER = (X_TANGENT, 4.0)
SEGMENTS = 32


def arc_points(radius, start, end, count=SEGMENTS):
    return [
        (
            CENTER[0] + radius * cos(start + (end - start) * i / count),
            CENTER[1] + radius * sin(start + (end - start) * i / count),
        )
        for i in range(count + 1)
    ]


outer = arc_points(R_OUTER, -pi / 2, 0)
inner = list(reversed(arc_points(R_INNER, -pi / 2, 0)))
profile = [
    (-40.0, 0.0),
    *outer,
    (X_TANGENT + R_OUTER, Z_TOP),
    (X_TANGENT + R_INNER, Z_TOP),
    *inner,
    (-40.0, 2.0),
]

with BuildPart() as model:
    with BuildSketch(Plane.XZ):
        Polygon(*profile)
    extrude(amount=20, both=True)

    with Locations((-20, 0, -1)):
        Cylinder(
            3,
            4,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
