"""build123d reference: XZ-oriented board and two front corner markers."""
from build123d import Align, Box, Compound, Pos

board = Pos(0, 6, 0) * Box(40, 12, 20, align=(Align.CENTER, Align.CENTER, Align.MIN))
marker = Box(10, 10, 10)
model = Compound(children=[
    board,
    Pos(15, -5, 15) * marker,
    Pos(-15, -5, 15) * marker,
])
