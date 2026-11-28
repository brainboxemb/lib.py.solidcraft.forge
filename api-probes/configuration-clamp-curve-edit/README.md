# Clamp curve-edit verification probe

## Consumer case

This is the HUB75-style geometry case, reduced only enough to stay generic.

The first sketch is an open clamp ring made from the same four center-point arcs
as the CAD consumer:

- Free bore: 9.6 mm;
- wall: 2.0 mm;
- Free opening: 90 deg.

After extrusion, one `sketch.move_points` call moves all six relevant sketch
references together:

- upper/lower outer endpoints;
- upper/lower inner endpoints;
- upper/lower lip-arc centres.

The target geometry is the 10.0 mm Installed form with the 2.0 mm wall retained.
Using the current neutral-axis approximation gives a 99 deg opening.

## Independent target

A second sketch is drawn directly at the target 10.0 mm geometry and extruded
to `Target10`.

The probe compares:

~~~text
ClampProfile96 -> move six points -> rebuilt Clamp

against

InstalledReference10 -> direct extrusion -> Target10
~~~

`inspect.compare` must report the two final bodies geometrically identical
within the probe tolerance.

## What this proves

- a multi-curve open-ring sketch can be changed by one atomic multi-point edit;
- connected arc endpoints and arc centres move together to the calculated target;
- an already-dependent extrusion rebuilds from that edited sketch;
- the resulting 10.0 mm geometry matches an independently drawn target.

This probe does not claim that `sketch.move_points` is a separate timeline
feature. It verifies the geometry-edit operation itself.