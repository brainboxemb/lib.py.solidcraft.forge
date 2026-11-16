"""build123d reference: two L protectors per vertical frame corner."""
from build123d import Align, Axis, Box, Compound, Pos, Rot, fillet

frame = Box(120, 80, 60, align=(Align.CENTER, Align.CENTER, Align.MIN))
frame = fillet(frame.edges().filter_by(Axis.Z), radius=8)
# Local L has footprint X/Y -4..28 and height 0..16.
horizontal = Pos(12, -2, 8) * Box(32, 4, 16)
vertical = Pos(-2, 12, 8) * Box(4, 32, 16)
profile = horizontal + vertical
parts = [frame]
for x, y, angle in [(-60,-40,0), (60,-40,90), (60,40,180), (-60,40,270)]:
    for z in (0, 44):
        parts.append(Pos(x, y, z) * Rot(0, 0, angle) * profile)
model = Compound(children=parts)
