"""build123d reference: two posts built from one part definition."""
from build123d import Align, Box, Compound, Pos

post = Box(10, 10, 20, align=(Align.CENTER, Align.CENTER, Align.MIN))
model = Compound(children=[Pos(-15, 0, 0) * post, Pos(15, 0, 0) * post])
