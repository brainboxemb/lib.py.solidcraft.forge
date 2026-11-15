"""Known-good Placement baseline for the HUB75-like AnchorFrame regression."""


from scpf import BOTTOM, FRONT


class SideBoard:
    width = 12.0
    depth = 60.0
    height = 80.0

    def build(self):
        return Box(
            self.width,
            self.depth,
            self.height,
        ).at(
            0,
            0,
            0,
            anchor=FRONT + BOTTOM,
        )


class LProfile:
    ARM_LENGTH = 28.0
    THICKNESS = 4.0
    PROFILE_DEPTH = 24.0

    def build(self):
        w = self.THICKNESS
        a = self.ARM_LENGTH

        with Sketch(name="Profile", plane="XZ") as sketch:
            Polygon2D(
                [
                    ("inside_corner", (0, 0)),
                    ("horizontal_tip", (a, 0)),
                    ("horizontal_outer", (a, w)),
                    ("outside_corner", (-w, w)),
                    ("vertical_outer", (-w, -a)),
                    ("vertical_tip", (0, -a)),
                ],
                plane="XZ",
                world=True,
            )

        return sketch.extrude(
            self.PROFILE_DEPTH,
            direction=Direction.SYMMETRIC,
        )


class Hub75LikePlacementBaseline:
    opening_width = 120.0
    opening_height = 80.0
    wall_thickness = 12.0
    cabinet_depth = 60.0
    bracket_depth = 24.0

    def build(self):
        outer_x = half(self.opening_width) + self.wall_thickness
        outer_height = self.opening_height + 2 * self.wall_thickness
        side_center_x = half(self.opening_width) + half(self.wall_thickness)
        front_y = half(self.bracket_depth)
        rear_y = self.cabinet_depth - half(self.bracket_depth)

        left_board = SideBoard(
            width=self.wall_thickness,
            depth=self.cabinet_depth,
            height=self.opening_height,
            name="left_board",
            placement=Placement(
                x=-side_center_x,
                z=self.wall_thickness,
            ),
        )
        right_board = left_board.copy(
            name="right_board",
            placement=Placement(
                x=side_center_x,
                z=self.wall_thickness,
            ),
        )

        bracket = LProfile()

        top_left_front = bracket.copy(
            name="top_left_front",
            placement=Placement(x=-outer_x, y=front_y, z=outer_height),
        )
        top_left_rear = bracket.copy(
            name="top_left_rear",
            placement=Placement(x=-outer_x, y=rear_y, z=outer_height),
        )

        top_right_front = bracket.copy(
            name="top_right_front",
            placement=Placement(
                x=outer_x,
                y=front_y,
                z=outer_height,
                rotation=(Y, 90),
            ),
        )
        top_right_rear = bracket.copy(
            name="top_right_rear",
            placement=Placement(
                x=outer_x,
                y=rear_y,
                z=outer_height,
                rotation=(Z, 180),
            ),
        )

        bottom_left_front = bracket.copy(
            name="bottom_left_front",
            placement=Placement(
                x=-outer_x,
                y=front_y,
                z=0,
                rotation=(Y, 270),
            ),
        )
        bottom_left_rear = bracket.copy(
            name="bottom_left_rear",
            placement=Placement(
                x=-outer_x,
                y=rear_y,
                z=0,
                rotation=(X, 180),
            ),
        )

        bottom_right_front = bracket.copy(
            name="bottom_right_front",
            placement=Placement(
                x=outer_x,
                y=front_y,
                z=0,
                rotation=(Y, 180),
            ),
        )
        bottom_right_rear = bracket.copy(
            name="bottom_right_rear",
            placement=Placement(
                x=outer_x,
                y=rear_y,
                z=0,
                rotation=(Y, 180),
            ),
        )

        return (
            left_board
            + right_board
            + top_left_front
            + top_left_rear
            + top_right_front
            + top_right_rear
            + bottom_right_front
            + bottom_right_rear
            + bottom_left_front
            + bottom_left_rear
        )


Hub75LikePlacementBaseline()
