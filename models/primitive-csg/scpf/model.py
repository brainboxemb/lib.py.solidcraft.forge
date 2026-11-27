"""Core CSG qualification: primitives, transforms and Boolean operations."""


class PrimitiveCsg:
    def build(self):
        body = Sphere(20)
        body = body + Box(30, 30, 20).move(x=18, z=10)

        # Native principal-axis Cylinder, centered by default.
        bore = Cylinder(d=8, h=60, axis=Axis.X)
        body = body - bore

        # Keep the authored final clip as an exact semantic feature so the
        # configuration can reference it without any native feature id.
        clip = Box(50, 50, 30).move(z=15)
        clipped = body & clip

        return clipped.configure(
            active="Clipped",
            columns=(clip,),
            rows={
                "Clipped": (False,),
                "Unclipped": (True,),
            },
        )


PrimitiveCsg()
