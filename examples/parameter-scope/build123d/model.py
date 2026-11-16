"""build123d geometry reference: explicit fixed/shared/derived panel widths.

Persisted native SolidCraft parameter changes are qualified separately.
"""
from build123d import Align, Box, Compound, Pos

shared_width = 80.0

def panel(width):
    return Box(width, 20, 10, align=(Align.CENTER, Align.CENTER, Align.MIN))

model = Compound(children=[
    Pos(0, 0, 0) * panel(40),
    Pos(100, 0, 0) * panel(60),
    Pos(220, 0, 0) * panel(shared_width),
    Pos(340, 0, 0) * panel(shared_width),
    Pos(460, 0, 0) * panel(shared_width / 2),
])
