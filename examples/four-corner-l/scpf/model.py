"""Four vertical L-profiles centred on the four rounded side corners."""


class FrameBlock:
    _width = 120.0
    _depth = 80.0
    _height = 60.0

    def build(self):
        return Box(
            self._width,
            self._depth,
            self._height,
            anchor=Anchor.BOTTOM,
        ).fillet(8, edges=Edges.VERTICAL)


class LProfile:
    ARM_LENGTH = 28.0
    THICKNESS = 4.0
    PROFILE_HEIGHT = 16.0

    def build(self):
        with Sketch(name="Profile", plane="XY") as sketch:
            Polygon2D(
                [
                    (0, 0),
                    (self.ARM_LENGTH, 0),
                    (self.ARM_LENGTH, -self.THICKNESS),
                    (-self.THICKNESS, -self.THICKNESS),
                    (-self.THICKNESS, self.ARM_LENGTH),
                    (0, self.ARM_LENGTH),
                ],
                plane="XY",
            )
        return sketch.extrude(
            self.PROFILE_HEIGHT,
            direction=Direction.POSITIVE,
        )


class FourCornerL:
    frame_width = 120.0
    frame_depth = 80.0
    frame_height = 60.0

    def build(self):
        frame = FrameBlock(
            _width=self.frame_width,
            _depth=self.frame_depth,
            _height=self.frame_height,
        )
        profile = LProfile()

        half_width = half(self.frame_width)
        half_depth = half(self.frame_depth)
        centre_height = half(
            self.frame_height - LProfile.PROFILE_HEIGHT
        )

        front_left = profile.copy(
            placement=Placement(
                x=-half_width,
                y=-half_depth,
                z=centre_height,
            ),
        )
        front_right = profile.copy(
            placement=Placement(
                x=half_width,
                y=-half_depth,
                z=centre_height,
                rotation=(Z, 90),
            ),
        )
        rear_right = profile.copy(
            placement=Placement(
                x=half_width,
                y=half_depth,
                z=centre_height,
                rotation=(Z, 180),
            ),
        )
        rear_left = profile.copy(
            placement=Placement(
                x=-half_width,
                y=half_depth,
                z=centre_height,
                rotation=(Z, 270),
            ),
        )

        return frame + front_left + front_right + rear_right + rear_left


FourCornerL()
