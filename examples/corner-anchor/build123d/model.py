"""build123d reference: marker at the base's front/top/right corner."""
from build123d import Align, Box, Compound, Pos

base = Box(40, 30, 20, align=(Align.CENTER, Align.CENTER, Align.MIN))
marker = Pos(15, -20, 15) * Box(10, 10, 10)
model = Compound(children=[base, marker])
