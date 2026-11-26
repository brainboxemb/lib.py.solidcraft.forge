"""Native two-distance chamfer qualification."""


class AsymmetricChamfer:
    width = 40.0
    depth = 20.0
    height = 10.0
    primary_distance = 0.18
    secondary_distance = 0.65

    def build(self):
        with Sketch(name="Chamfer profile", plane="XZ") as profile:
            Polygon2D(
                [
                    (-self.width / 2, 0),
                    (self.width / 2, 0),
                    (self.width / 2, self.height),
                    (-self.width / 2, self.height),
                ],
                plane="XZ",
                world=True,
                ids=["bottom", "right", "top", "left"],
            )

        body = profile.extrude(self.depth, sym=True)
        return body.chamfer(
            self.primary_distance,
            distance2=self.secondary_distance,
            flip=True,
            edges=Edges.from_profile("top"),
        )


AsymmetricChamfer()
