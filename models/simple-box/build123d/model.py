"""40 x 30 x 10 mm box centered in XY and based at Z=0."""
from build123d import Align, Box

model = Box(40, 30, 10, align=(Align.CENTER, Align.CENTER, Align.MIN))
