"""Public Verification model for Cone Boolean feature compilation (#746)."""


class ConeBoolean:
    def build(self):
        body = Box(
            50,
            40,
            20,
            anchor=Anchor.BOTTOM,
        ).fillet(2, edges=Edges.VERTICAL)
        flare = Cone(
            d=18,
            top_d=10,
            h=8,
            anchor=Anchor.BOTTOM,
        ).at(0, 0, 18, anchor=Anchor.BOTTOM)
        return body + flare


ConeBoolean()
