"""build123d reference for the original bottom-based SimpleBox intent."""
from build123d import Align, Box

length, width, height = 40.0, 30.0, 10.0
model = Box(
    length,
    width,
    height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
