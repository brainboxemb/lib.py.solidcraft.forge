"""build123d 0.12 reference using its brake-formed sheet operation."""

from build123d import (
    Align,
    BuildLine,
    BuildPart,
    Cylinder,
    Line,
    Locations,
    Mode,
    Plane,
    Side,
    fillet,
    make_brake_formed,
)

X_TANGENT = 17.64380551
Z_TOP = 21.64380551

with BuildPart() as model:
    # The path follows the inside sheet surface. A 2 mm radius at the corner
    # plus a 2 mm RIGHT-side offset yields the same R2/R4 bend envelope as the
    # SolidCraft sheet rule.
    with BuildLine(Plane.XZ) as inside:
        Line((-40, 2), (X_TANGENT + 2, 2))
        Line((X_TANGENT + 2, 2), (X_TANGENT + 2, Z_TOP))
        fillet(inside.vertices(), 2)

    make_brake_formed(
        thickness=2,
        station_widths=40,
        side=Side.RIGHT,
    )

    with Locations((-20, 0, -1)):
        Cylinder(
            3,
            4,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
