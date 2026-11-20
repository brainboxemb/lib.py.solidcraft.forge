"""Qualification: two repeated parents, each with one attached child."""


class Parent:
    _height = 40.0

    def build(self):
        return Box(20, 20, self._height, anchor=Anchor.BOTTOM)


class Marker:
    def build(self):
        return Box(10, 10, 10, anchor=Anchor.BOTTOM)


class RepeatedParentAttachments:
    parent_height = 40.0

    def build(self):
        left = Parent(_height=self.parent_height)
        right = left.copy(placement=Placement(x=60))

        left_marker = Marker().attach(
            left,
            parent=Anchor.TOP,
            child=Anchor.BOTTOM,
        )
        right_marker = left_marker.copy().attach(
            right,
            parent=Anchor.TOP,
            child=Anchor.BOTTOM,
        )
        return left + right + left_marker + right_marker


RepeatedParentAttachments()
