"""One native editable configuration table with two independent optional holes."""
from scpf import Anchor, Box, Configure, Hole, Param, Suppress


class ConfigurationPlate:
    width = 80
    depth = 40
    thickness = 5
    diameter = 5

    def build(self):
        plate = Box(self.width, self.depth, self.thickness, anchor=Anchor.BOTTOM)
        left = Hole(d=self.diameter).at(-12, 0, self.thickness)
        right = Hole(d=self.diameter).at(12, 0, self.thickness)
        return Configure(
            plate - left - right,
            active="Medium",
            columns=(Param("width"), Param("depth"), Param("thickness"),
                     Param("diameter"), Suppress(left), Suppress(right)),
            rows={
                "Small": ("60 mm", "30 mm", "4 mm", "4 mm", True, True),
                "Medium": ("80 mm", "40 mm", "5 mm", "5 mm", True, True),
                "Large": ("100 mm", "50 mm", "6 mm", "6 mm", False, False),
            },
        )


ConfigurationPlate()
