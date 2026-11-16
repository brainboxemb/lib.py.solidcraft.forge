"""build123d reference: two panels in one group and a separate frame.

Compound captures the visible hierarchy; native BOM persistence is verified
through SolidCraft rather than inferred from STL.
"""
from build123d import Align, Box, Compound, Pos

bottom = (Align.CENTER, Align.CENTER, Align.MIN)
panel = Box(10, 2, 20, align=bottom)
panels = Compound(children=[panel, Pos(11, 0, 0) * panel])
frame = Pos(0, 20, 0) * Box(35, 10, 40, align=bottom)
model = Compound(children=[panels, frame])
