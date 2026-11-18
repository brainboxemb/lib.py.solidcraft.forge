"""build123d 0.12 reference using its brake-formed sheet operation."""

from build123d import (
    Align,
    Cylinder,
    Plane,
    Polyline,
    Pos,
    Side,
    fillet,
    make_brake_formed,
)

X_TANGENT = 17.64380551
Z_TOP = 21.64380551

# Algebra-mode reference, matching build123d's own make_brake_formed examples.
# The polyline follows the inside sheet surface; the R2 fillet plus 2 mm sheet
# thickness produces the same R2/R4 bend envelope as the SolidCraft sheet rule.
inside = Plane.XZ * Polyline(
    (-40, 2),
    (X_TANGENT + 2, 2),
    (X_TANGENT + 2, Z_TOP),
)
inside = fillet(inside.vertices(), 2)

sheet = make_brake_formed(
    thickness=2,
    station_widths=40,
    line=inside,
    side=Side.LEFT,
)

# make_brake_formed grows the station width to one side of the path plane.
# Centre that independent reference on Y=0 so its 40 mm width matches the
# qualified SolidCraft body bounds.
bbox = sheet.bounding_box()
sheet = Pos(Y=-(bbox.min.Y + bbox.max.Y) / 2) * sheet

hole = Pos(-20, 0, -1) * Cylinder(
    3,
    4,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
model = sheet - hole
