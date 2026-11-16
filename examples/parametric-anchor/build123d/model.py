"""build123d reference: centered block positioned against a right face."""
from build123d import Align, Box, Compound, Pos

base_width, child_width = 40.0, 20.0
bottom = (Align.CENTER, Align.CENTER, Align.MIN)
base = Box(base_width, 30, 10, align=bottom)
block = Box(child_width, 20, 10, align=bottom)
model = Compound(children=[base, Pos(base_width/2 + child_width/2, 0, 0) * block])
