# Change 0022 — Consistent anchors for standard 3D primitives

**Status:** design and implementation  
**SolidCraft target:** 0.42.0

## Problem

Forge did not give its direct 3D primitives one consistent datum rule.

The clearest example was `Box()`:

- feature-history lowering used a bottom-centred corner;
- direct CSG lowering used the geometric centre.

Cylinder also historically treated its constructor/placement point as the
native base, while CENTER alignment elsewhere already needed half-height
offsets.

Because Forge is still in unstable-release development, change 0022 chooses one
simple rule instead of preserving those accidental defaults.

## Rule

Standard dimension-defined 3D primitives are centred on model coordinate
`(0, 0, 0)` by default:

```python
Box(80, 50, 10)
Cylinder(d=8, h=20)
Sphere(12)
```

An optional `anchor=` chooses which world-cardinal datum lies at the origin.

```python
Box(80, 50, 10, anchor=BOTTOM)
Cylinder(d=8, h=20, anchor=BOTTOM)
Cylinder(d=8, h=20, axis=Axis.X, anchor=LEFT)
Sphere(12, anchor=LEFT)
```

The public signatures are:

```python
Box(length, width, thickness, *, anchor=Anchor.CENTER)
Cylinder(*, d, h, axis=Axis.Z, anchor=Anchor.CENTER)
Sphere(radius, *, anchor=Anchor.CENTER)
```

For an oriented Cylinder, anchors refer to its **world X/Y/Z bounds after the
axis is chosen**. Therefore:

- Axis.Z uses BOTTOM/TOP for its axial ends;
- Axis.X uses LEFT/RIGHT for its axial ends;
- Axis.Y uses FRONT/BACK for its axial ends.

Other cardinal directions select tangent points/planes on the transverse
circular bounds.

## Native lowering

Forge lowers the selected datum directly to SolidCraft primitive coordinates.

For Box:

- CENTER uses native `center=[...]`;
- another anchor is converted to native `corner=[...]`.

For Cylinder:

- SolidCraft still receives a native `base=[...]`;
- Forge derives that base from the selected anchor, axis, height and diameter.

For Sphere:

- SolidCraft receives the native `center=[...]`;
- Forge derives that center from the selected tangent/center anchor.

The same calculation is used whether a primitive is a root body, a Boolean CSG
operand, or is translated later. No corrective move is added merely to emulate
the chosen datum.

## `.at()` remains placement

Constructor `anchor=` chooses the unplaced primitive datum.

`.at(x, y, z, anchor=...)` chooses which datum is placed at the requested
world coordinate. With no explicit anchor, CENTER is placed there.

Examples:

```python
Box(80, 50, 10).at(0, 0, 0, anchor=BOTTOM)
Cylinder(d=8, h=20).at(10, 5, 3)
Cylinder(d=8, h=20).at(10, 5, 3, anchor=BOTTOM)
Sphere(12).at(30, 0, 0)
```

`shape.at(other_shape)` remains CENTER-to-CENTER for the supported direct
shapes.

## Box taper

`Box.taper(from_z=..., inset=...)` is anchor-aware.

`from_z` is measured from the Box bottom face regardless of which constructor
anchor lies at model origin. The native section sketches are emitted at the
actual bottom/start/top planes.

## 2D profiles

Rectangle2D, RoundedRectangle2D and Circle2D already use semantic centering
inside a Sketch from change 0018. Polygon2D and Text2D keep their authored
coordinates/insertion point and are not forcibly recentered.

## Qualification

Change 0022 proves:

- ordinary Box uses native CENTER in both feature-history and CSG;
- Box bottom/edge/corner anchors lower to the correct native corner;
- ordinary Cylinder is centred on all principal axes;
- explicit Cylinder axial anchors use the expected native base;
- ordinary Sphere is centred and cardinal anchors move its native center to
  keep the selected tangent datum at the origin;
- primitive CSG and non-CSG paths use the same datum calculation;
- focused compiler regressions prove the new default CENTER and explicit
  anchors; the older simple-box qualification keeps its established
  bottom-based geometry by stating anchor=BOTTOM explicitly;
- Box.taper keeps the same physical taper intent for CENTER and BOTTOM;
- qualification fixtures that require a bottom datum state it explicitly;
- PythonSCAD, pyBOSL2 and CadQuery references for the qualification cases keep
  the same visible modelling intent;
- full Q1-Q6 qualification remains green.

## Exit condition

> Standard direct 3D primitives have a centred default, explicit cardinal
> anchors have one world-space meaning, and native/CSG lowering agree.
