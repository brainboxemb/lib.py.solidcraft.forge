"""pyBOSL2 geometry reference for the five Slot-family cut shapes."""

import math
from pybosl2 import Path2D, cuboid, cyl

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


def straight_slot(center_x, center_y, center_separation, width=SLOT_WIDTH):
    bar = cuboid([center_separation, width, CUT_HEIGHT]).translate(
        [center_x, center_y, 2.5]
    )
    left = cyl(diameter=width, height=CUT_HEIGHT).translate(
        [center_x - center_separation / 2, center_y, 2.5]
    )
    right = cyl(diameter=width, height=CUT_HEIGHT).translate(
        [center_x + center_separation / 2, center_y, 2.5]
    )
    return bar | left | right

def polygon_solid(points):
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    box_center = ((min_x + max_x) / 2, (min_y + max_y) / 2)
    local = [[p[0] - box_center[0], p[1] - box_center[1]] for p in points]
    return (
        Path2D(local)
        .polygon()
        .linear_extrude(height=CUT_HEIGHT)
        .translate([box_center[0], box_center[1], CUT_Z])
    )

def arc_slot(center, radius, start_deg, sweep_deg, width=SLOT_WIDTH):
    points, start, end = arc_band_points(
        center, radius, start_deg, sweep_deg, width
    )
    band = polygon_solid(points)
    start_cap = cyl(diameter=width, height=CUT_HEIGHT).translate(
        [start[0], start[1], 2.5]
    )
    end_cap = cyl(diameter=width, height=CUT_HEIGHT).translate(
        [end[0], end[1], 2.5]
    )
    return band | start_cap | end_cap

plate = cuboid([160, 120, 5]).up(2.5)
cutters = straight_slot(-50, -35, 20)
cutters = cutters | straight_slot(5, -35, 22)
cutters = cutters | straight_slot(55, -35, 20)

three_center = (-35.0, 22.846153846153847)
three_radius = 15.153846153846153
cutters = cutters | arc_slot(
    three_center,
    three_radius,
    171.82876644005026,
    -163.65753288010052,
)
cutters = cutters | arc_slot((40, 25), 12, 0, 120)

model = plate - cutters
