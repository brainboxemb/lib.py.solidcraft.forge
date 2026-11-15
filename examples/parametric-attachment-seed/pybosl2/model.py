"""pyBOSL2 geometry reference for associative attachment seed placement."""

from pybosl2 import cuboid

left = cuboid([20, 20, 100]).up(50)
right = cuboid([20, 20, 100]).up(50).right(80)
left_marker = cuboid([10, 10, 10]).up(105)
right_marker = cuboid([10, 10, 10]).up(105).right(80)

model = left | right | left_marker | right_marker
