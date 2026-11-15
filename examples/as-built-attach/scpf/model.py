"""Qualification: as-built attachment preserves an existing child pose."""


class Base:
    WIDTH = 40.0
    DEPTH = 30.0
    HEIGHT = 10.0

    def build(self):
        return Box(self.WIDTH, self.DEPTH, self.HEIGHT)


class Marker:
    LENGTH = 30.0
    WIDTH = 10.0
    HEIGHT = 8.0

    def build(self):
        return Box(self.LENGTH, self.WIDTH, self.HEIGHT)


class AsBuiltAttach:
    def build(self):
        base = Base()
        marker = Marker().at(
            Placement(
                position=Position(x=50, y=20, z=15),
                rotation=((0, 0, 1), 90),
            )
        ).attach(base, as_built=True)
        return base + marker


AsBuiltAttach()
