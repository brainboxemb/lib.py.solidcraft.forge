"""build123d reference: a child's dimensions derive from its parent."""
from build123d import Align, Box, Compound, Pos

base_width, base_depth = 120.0, 80.0
bottom_based = (Align.CENTER, Align.CENTER, Align.MIN)
parent = Box(base_width, base_depth, 10, align=bottom_based)
child = Pos(0, 0, 20) * Box(base_width / 2, base_depth / 2, 6, align=bottom_based)
model = Compound(children=[parent, child])
