"""build123d reference: companion and marker positioned by assembly intent."""
from build123d import Align, Box, Compound, Pos

base = Box(40, 30, 20, align=(Align.CENTER, Align.CENTER, Align.MIN))
small = Box(10, 10, 10)
model = Compound(children=[
    base,
    Pos(70, 0, 5) * small,
    Pos(15, -20, 15) * small,
])
