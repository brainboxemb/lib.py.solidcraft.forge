"""build123d reference: two positions of one reusable block shape."""
from build123d import Align, Box, Compound, Pos

block = Box(40, 30, 10, align=(Align.CENTER, Align.CENTER, Align.MIN))
model = Compound(children=[block, Pos(40, 0, 0) * block])
