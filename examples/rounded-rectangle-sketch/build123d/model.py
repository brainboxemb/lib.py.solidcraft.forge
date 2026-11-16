"""build123d reference: a true rounded pad on a rectangular base."""
from build123d import Align, Axis, Box, Compound, Pos, fillet

base_width, base_depth, base_height = 80.0, 60.0, 5.0
pad_width, pad_depth, radius, pad_height = 40.0, 30.0, 5.0, 8.0
bottom = (Align.CENTER, Align.CENTER, Align.MIN)
base = Box(base_width, base_depth, base_height, align=bottom)
pad = Box(pad_width, pad_depth, pad_height, align=bottom)
pad = fillet(pad.edges().filter_by(Axis.Z), radius=radius)
model = Compound(children=[base, Pos(0, 0, base_height) * pad])
