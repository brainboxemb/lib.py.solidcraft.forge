"""build123d reference: a top-mounted arm clocked 90 degrees in XY."""
from build123d import Align, Box, Compound, Pos, Rot

bottom = (Align.CENTER, Align.CENTER, Align.MIN)
base = Box(60, 60, 10, align=bottom)
arm = Box(30, 10, 6, align=bottom)
model = Compound(children=[base, Pos(0, 0, 10) * Rot(0, 0, 90) * arm])
