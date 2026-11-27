"""Parent configuration controls one feature exported by a reusable child."""


@component(include=("width",))
class FeatureCoupler:
    width = 40.0
    DEPTH = 24.0
    HEIGHT = 12.0

    def build(self):
        body = Box(
            self.width,
            self.DEPTH,
            self.HEIGHT,
            anchor=Anchor.BOTTOM,
        )
        panel_pin = (
            Hole(d=5)
            .at(0, 0, self.HEIGHT)
            .export_feature("panel_pin")
        )
        return body - panel_pin


class ConfigurationChildFeature:
    coupler_width = 40.0

    def build(self):
        left = FeatureCoupler(
            width=self.coupler_width,
            name="left",
            placement=Placement(x=-50),
        )
        right = FeatureCoupler(
            width=self.coupler_width,
            name="right",
            placement=Placement(x=50),
        )

        model = left + right
        model.configure(
            active="Medium",
            columns=(
                self.coupler_width,
                right.feature("panel_pin"),
            ),
            rows={
                "Small": ("30 mm", True),
                "Medium": ("40 mm", True),
                "Large": ("40 mm", False),
            },
        )
        return model


ConfigurationChildFeature()
