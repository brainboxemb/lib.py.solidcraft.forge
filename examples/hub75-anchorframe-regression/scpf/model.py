"""HUB75-like regression: eight L profiles attached to two placed side boards."""



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
            anchor=Anchor.FRONT + Anchor.BOTTOM,
        )


class LProfile:
    ARM_LENGTH = 28.0
    THICKNESS = 4.0
    PROFILE_DEPTH = 24.0

    def build(self):
        # Neutral local profile: inside corner is the component origin.
        # The horizontal arm extends +X and the vertical arm extends -Z.
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


class Hub75LikeAnchorFrame:
    opening_width = 120.0
    opening_height = 80.0
    wall_thickness = 12.0
    cabinet_depth = 60.0
    bracket_depth = 24.0

    def build(self):
        side_center_x = half(self.opening_width) + half(self.wall_thickness)

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

        # These are the exact A/B child-frame choices from the downstream
        # regression. They belong to this assembly, not to generic LProfile.
        w = LProfile.THICKNESS
        front_mount_a = AnchorFrame(
            origin=down(w),
            z=Anchor.BACK,
            x=Anchor.DOWN,
        )
        front_mount_b = AnchorFrame(
            origin=right(w),
            z=Anchor.BACK,
            x=Anchor.DOWN,
        )
        rear_mount_a = AnchorFrame(
            origin=down(w),
            z=Anchor.FRONT,
            x=Anchor.RIGHT,
        )
        rear_mount_b = AnchorFrame(
            origin=right(w),
            z=Anchor.FRONT,
            x=Anchor.RIGHT,
        )
        gap = -half(self.bracket_depth)

        top_left_front = bracket.copy(name="top_left_front").attach(
            left_board,
            parent=Anchor.FRONT_TOP_LEFT,
            child=front_mount_a,
            gap=gap,
        )
        top_right_front = bracket.copy(name="top_right_front").attach(
            right_board,
            parent=Anchor.FRONT_TOP_RIGHT,
            child=front_mount_b,
            gap=gap,
        )
        bottom_right_front = bracket.copy(name="bottom_right_front").attach(
            right_board,
            parent=Anchor.FRONT_BOTTOM_RIGHT,
            child=front_mount_a,
            gap=gap,
        )
        bottom_left_front = bracket.copy(name="bottom_left_front").attach(
            left_board,
            parent=Anchor.FRONT_BOTTOM_LEFT,
            child=front_mount_b,
            gap=gap,
        )

        top_left_rear = bracket.copy(name="top_left_rear").attach(
            left_board,
            parent=Anchor.BACK_TOP_LEFT,
            child=rear_mount_a,
            gap=gap,
        )
        top_right_rear = bracket.copy(name="top_right_rear").attach(
            right_board,
            parent=Anchor.BACK_TOP_RIGHT,
            child=rear_mount_b,
            gap=gap,
        )
        bottom_right_rear = bracket.copy(name="bottom_right_rear").attach(
            right_board,
            parent=Anchor.BACK_BOTTOM_RIGHT,
            child=rear_mount_a,
            gap=gap,
        )
        bottom_left_rear = bracket.copy(name="bottom_left_rear").attach(
            left_board,
            parent=Anchor.BACK_BOTTOM_LEFT,
            child=rear_mount_b,
            gap=gap,
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


Hub75LikeAnchorFrame()
