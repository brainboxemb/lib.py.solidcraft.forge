"""build123d 0.12 geometry reference for the Hole family.

build123d core has native Hole, CounterBoreHole and CounterSinkHole operations.
It has no equivalent native tapped-hole metadata feature, so the fourth
reference cut represents the qualified M6 tap drill envelope (Ø5) only.
"""
from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    CounterBoreHole,
    CounterSinkHole,
    Hole,
    Locations,
)

bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    Box(120, 40, 12, align=bottom)
    top = model.faces().sort_by(Axis.Z)[-1]
    with Locations(top):
        with Locations((-45, 0)):
            Hole(radius=3)
        with Locations((-15, 0)):
            CounterBoreHole(
                radius=3,
                counter_bore_radius=6,
                counter_bore_depth=4,
            )
        with Locations((15, 0)):
            CounterSinkHole(
                radius=3,
                counter_sink_radius=6,
                counter_sink_angle=90,
            )
        with Locations((45, 0)):
            Hole(radius=2.5)
