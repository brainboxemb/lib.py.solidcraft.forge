"""PythonSCAD geometry reference for the five Slot-family cut shapes."""

import math
from pythonscad import *

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
    bar = cube([center_separation, width, CUT_HEIGHT], center=True).translate(
        [center_x, center_y, 2.5]
    )
    left = cylinder(d=width, h=CUT_HEIGHT).translate(
        [center_x - center_separation / 2, center_y, CUT_Z]
    )
    right = cylinder(d=width, h=CUT_HEIGHT).translate(
        [center_x + center_separation / 2, center_y, CUT_Z]
    )
    return bar | left | right

def arc_slot(center, radius, start_deg, sweep_deg, width=SLOT_WIDTH):
    points, start, end = arc_band_points(
        center, radius, start_deg, sweep_deg, width
    )
    band = polygon(points).linear_extrude(height=CUT_HEIGHT).translate(
        [0, 0, CUT_Z]
    )
    start_cap = cylinder(d=width, h=CUT_HEIGHT).translate(
        [start[0], start[1], CUT_Z]
    )
    end_cap = cylinder(d=width, h=CUT_HEIGHT).translate(
        [end[0], end[1], CUT_Z]
    )
    return band | start_cap | end_cap

plate = cube([160, 120, 5], center=True).up(2.5)

# Center-to-center: end-circle centres are (-60,-35) and (-40,-35).
cutters = straight_slot(-50, -35, 20)

# Overall endpoints are (-10,-35) and (20,-35), so the end-circle centres
# are 4 mm inward from those endpoints: -6 and 16.
cutters = cutters | straight_slot(5, -35, 22)

# Center-point: slot centre is (55,-35), one end-circle centre is (65,-35).
cutters = cutters | straight_slot(55, -35, 20)

# Three-point arc through (-50,25), (-35,38), (-20,25).
three_center = (-35.0, 22.846153846153847)
three_radius = 15.153846153846153
cutters = cutters | arc_slot(
    three_center,
    three_radius,
    171.82876644005026,
    -163.65753288010052,
)

# Center arc: centre (40,25), start (52,25), radius 12, sweep +120 deg.
cutters = cutters | arc_slot((40, 25), 12, 0, 120)

model = plate - cutters
