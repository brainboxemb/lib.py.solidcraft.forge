"""build123d reference: a marker shifted relative to a top/front corner."""
from build123d import Align, Box, Compound, Pos

shift = 5.0
base = Box(40, 30, 20, align=(Align.CENTER, Align.CENTER, Align.MIN))
marker = Box(10, 10, 10)
model = Compound(children=[base, Pos(15, -15 - shift, 20) * marker])
