"""Minimal #845 contour-flange recess replay regression fixture."""


class SheetContourFlangeRecess:
    length = 250.0

    PROFILE_WIDTH = 27.0
    PROFILE_HEIGHT = 18.0
    THICKNESS = 1.25
    OPENING = 15.0
    BEND_RADIUS = 1.25
    K_FACTOR = 0.40

    HOLE_DIAMETER = 12.5
    HOLE_OFFSET = 37.5

    def build(self):
        thickness = self.THICKNESS
        half_side = (self.PROFILE_WIDTH - thickness) / 2
        lower_z = thickness / 2
        upper_z = self.PROFILE_HEIGHT - thickness / 2
        opening_half = self.OPENING / 2

        with Sketch(name="C profile", plane="XZ") as profile:
            chain = profile.chain(start=(-opening_half, lower_z))
            chain.line_to((-half_side, lower_z))
            chain.line_to((-half_side, upper_z))
            chain.line_to((half_side, upper_z))
            chain.line_to((half_side, lower_z))
            chain.line_to((opening_half, lower_z))
            contour = chain.finish()

        rail = contour.contour_flange(
            distance=self.length,
            thickness=thickness,
            bend_radius=self.BEND_RADIUS,
            k_factor=self.K_FACTOR,
            rule_name="Contour Recess Rule",
        )

        with Sketch(
            name="Broad face recess",
            on=rail,
            parent=Anchor.TOP,
        ) as recess:
            recess.add(
                Circle2D(d=self.HOLE_DIAMETER),
                offset=(0, self.HOLE_OFFSET),
            )

        cut = recess.extrude(Depth.THROUGH_ALL)
        return rail - cut


SheetContourFlangeRecess()
