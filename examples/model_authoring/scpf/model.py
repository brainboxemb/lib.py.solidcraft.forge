"""Q1/Q2 authoring fixture: separate parts, materials and parameter roles."""


@component(include=("length",))
class Plate:
    length = 60.0
    WIDTH = 30.0
    THICKNESS = 5.0

    def build(self):
        return Box(
            self.length,
            self.WIDTH,
            self.THICKNESS,
            anchor=Anchor.BOTTOM,
        ).with_material(
            "Birch",
            density_g_cm3=0.68,
            color="#D8B47A",
        )


@component
class Block:
    SIZE = 10.0

    def build(self):
        return Box(
            self.SIZE,
            self.SIZE,
            self.SIZE,
            anchor=Anchor.BOTTOM,
        ).with_material(
            "Steel",
            density_g_cm3=7.85,
            color="#777777",
        )


@assembly
class MultiPartMaterials:
    _plate_y = -25.0

    def build(self):
        plate = Plate(
            name="plate",
            placement=Placement(y=self._plate_y),
        )
        left = Block(name="left")
        right = left.copy(
            name="right",
            placement=Placement(x=20),
        )

        # These are three physical occurrences. + creates an Assembly here.
        return plate + left + right


MultiPartMaterials()
