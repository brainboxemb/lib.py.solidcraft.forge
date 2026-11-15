"""Qualification: group(name) becomes a real nested native component."""


class Panel:
    def build(self):
        return Box(10, 2, 20)


class Frame:
    def build(self):
        # The frame offset is visual fixture geometry, not the grouping API.
        return Box(35, 10, 40).move(y=20, z=20)


class GroupHierarchy:
    def build(self):
        left = Panel()
        panels = (left + left.copy(placement=Placement(x=11))).group("PanelGroup")
        frame = Frame()
        return panels + frame


GroupHierarchy()
