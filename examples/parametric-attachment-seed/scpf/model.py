"""Qualification: attached children keep associative seed placement."""


class Post:
    height = 100.0

    def build(self):
        return Box(20, 20, self.height)


class Marker:
    def build(self):
        return Box(10, 10, 10)


class ParametricAttachmentSeed:
    def build(self):
        left = Post()
        right = Post().move(x=80)

        left_marker = Marker().attach(
            left,
            parent=Anchor.TOP,
            child=Anchor.BOTTOM,
        )
        right_marker = Marker().attach(
            right,
            parent=Anchor.TOP,
            child=Anchor.BOTTOM,
        )

        return left + right + left_marker + right_marker


ParametricAttachmentSeed()
