"""build123d reference: an L section across the Y symmetry plane."""
from build123d import Box, Pos

horizontal = Pos(20, 0, -6) * Box(40, 24, 12)
vertical = Pos(6, 0, -20) * Box(12, 24, 40)
model = horizontal + vertical
