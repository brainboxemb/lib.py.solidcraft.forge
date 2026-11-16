"""Native Box whose declared datum is its geometric centre."""


class CenteredBox:
    length = 40.0
    width = 30.0
    height = 10.0

    def build(self):
        return Box(
            self.length,
            self.width,
            self.height,
            origin=CENTER,
        )


CenteredBox()
