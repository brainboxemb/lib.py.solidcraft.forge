"""CadQuery geometry reference for the five Slot-family cut shapes."""

import math
import cadquery as cq

CUT_HEIGHT = 9
CUT_Z = -2
SLOT_WIDTH = 8.0

def arc_band_points(center, radius, start_deg, sweep_deg, width, steps=96):
    cx, cy = center
    half = width / 2
    angles = [
        math.radians(start_deg + sweep_deg * i / steps)
        for i in range(steps + 1)
    ]
    outer = [
        [cx + (radius + half) * math.cos(a), cy + (radius + half) * math.sin(a)]
        for a in angles
    ]
    inner = [
        [cx + (radius - half) * math.cos(a), cy + (radius - half) * math.sin(a)]
        for a in reversed(angles)
    ]
    start = [
        cx + radius * math.cos(angles[0]),
        cy + radius * math.sin(angles[0]),
    ]
    end = [
        cx + radius * math.cos(angles[-1]),
        cy + radius * math.sin(angles[-1]),
    ]
    return outer + inner, start, end


def straight_slot(center_x, center_y, overall_length, width=SLOT_WIDTH):
    return (
        cq.Workplane("XY")
        .center(center_x, center_y)
        .slot2D(overall_length, width)
        .extrude(CUT_HEIGHT)
        .translate((0, 0, CUT_Z))
    )

def arc_slot(center, radius, start_deg, sweep_deg, width=SLOT_WIDTH):
    points, start, end = arc_band_points(
        center, radius, start_deg, sweep_deg, width
    )
    band = (
        cq.Workplane("XY")
        .polyline(points)
        .close()
        .extrude(CUT_HEIGHT)
        .translate((0, 0, CUT_Z))
    )
    start_cap = (
        cq.Workplane("XY")
        .center(start[0], start[1])
        .circle(width / 2)
        .extrude(CUT_HEIGHT)
        .translate((0, 0, CUT_Z))
    )
    end_cap = (
        cq.Workplane("XY")
        .center(end[0], end[1])
        .circle(width / 2)
        .extrude(CUT_HEIGHT)
        .translate((0, 0, CUT_Z))
    )
    return band.union(start_cap).union(end_cap)

plate = cq.Workplane("XY").box(160, 120, 5, centered=(True, True, False))

# overall lengths: 28, 30 and 28 mm respectively.
cutters = straight_slot(-50, -35, 28)
cutters = cutters.union(straight_slot(5, -35, 30))
cutters = cutters.union(straight_slot(55, -35, 28))

three_center = (-35.0, 22.846153846153847)
three_radius = 15.153846153846153
cutters = cutters.union(
    arc_slot(
        three_center,
        three_radius,
        171.82876644005026,
        -163.65753288010052,
    )
)
cutters = cutters.union(arc_slot((40, 25), 12, 0, 120))

result = plate.cut(cutters)
model = cq.Assembly()
model.add(result, name="slot_family")
