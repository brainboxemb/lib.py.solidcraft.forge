# Change 0022 — Consistent origins for standard primitives

**Status:** design and implementation  
**SolidCraft target:** 0.42.0

## Problem

Change 0022 covers **all standard dimension-defined primitives**, not only
Box. The placement rule must be consistent between the direct native route,
CSG booleans, and feature addition/subtraction.

Forge gave one `Box()` two different native meanings.

The feature-history path used a bottom-centred corner:

```text
solid.box(..., corner=[-length / 2, -width / 2, 0])
```

while the direct CSG path used:

```text
solid.box(..., center=[0, 0, 0])
```

for the same unplaced Box.

SolidCraft 0.42 already has the right native distinction: `solid.box` accepts
either `center=[x,y,z]` or `corner=[x,y,z]`.

## Public API

The default for a dimension-defined solid is the geometric center, following
the useful pyBOSL2 modelling convention. PythonSCAD generally needs an explicit
`center=True` for centered cube/cylinder equivalents. Reference syntax and
version pins are cached locally in `docs/agent/reference-libraries.md`; do not
revisit upstream projects for every qualification.

| Shape | Normal origin | Deliberate alternative |
| --- | --- | --- |
| `Box` | XYZ center | `anchor=BOTTOM`, edge/corner anchors |
| `Cylinder` | center of its axis and circular sections | `anchor=BOTTOM` for Z axis, `anchor=LEFT` for X axis |
| `Sphere` | sphere center | a cardinal tangent-point anchor if exposed |
| `Rectangle2D`, `RoundedRectangle2D` | profile center | explicit sketch anchor |
| `Circle2D` | circle center | explicit sketch placement |
| `Polygon2D`, `Text2D` | authored coordinates/insertion point | explicit placement, no forced recentering |

For an oriented cylinder, cardinal anchors refer to world X/Y/Z dimensions
after orientation. This avoids using BOTTOM to mean the axial end of an X-axis
cylinder.

**Rollout:** apply each primitive's new origin consistently, migrate existing
scripts/examples/qualification expectations that relied on the old origin, and
then qualify native and CSG equivalents. No compatibility shim is required in
this unstable release.

`Box` uses the existing anchor vocabulary:

```python
Box(length, width, thickness, *, anchor=Anchor.CENTER)
```

`anchor` means: **which Box anchor is located at model coordinate
`(0, 0, 0)` before later placement**.

The useful default is the geometric centre:

```python
Box(80, 50, 10)                          # fully centred
Box(80, 50, 10, anchor=BOTTOM)           # bottom-face centre at Z=0
Box(80, 50, 10, anchor=FRONT + BOTTOM)   # front/bottom edge centre at origin
Box(80, 50, 10, anchor=FRONT + LEFT + BOTTOM)  # corner at origin
```

Forge is still in unstable-release development. Change 0022 deliberately picks
one clear default instead of preserving the previous accidental bottom-centred
behaviour.

## Other primitive lowering

A default Z-axis cylinder of diameter `d` and height `h` is centered at the
origin, so the native cylinder `base` is at `[0, 0, -h / 2]`. An explicit
`anchor=BOTTOM` sets the base to `[0, 0, 0]`. For a sphere the native
`center=[0,0,0]` is already correct. The same parameter-aware calculation
must be reused for boolean operands.

## Native lowering

For the default `CENTER` anchor Forge emits:

```text
solid.box(..., center=[0, 0, 0])
```

For another supported anchor Forge calculates the corresponding native
`corner=[...]` directly from the Box dimensions and selected datum.

The feature-history and direct-CSG paths use the same rule.

A translated CSG Box adds the translation to the selected native datum; it does
not add a corrective move after construction.

## `.at()` remains placement

Constructor `anchor=` chooses the Box's unplaced datum. `.at(..., anchor=...)`
is later placement.

For example:

```python
Box(80, 50, 10).at(0, 0, 0, anchor=BOTTOM)
```

creates a centred Box constructor, then explicitly places its bottom-face centre
at the requested point. The resulting native Box is emitted from that placement
datum directly.

## `taper()`

`Box.taper(from_z=..., inset=...)` is anchor-aware.

`from_z` is a distance measured from the Box's bottom face, regardless of
which Box anchor is located at model origin. For a centred Box, the front plane
is therefore at `-thickness / 2`; for `anchor=BOTTOM` it is at `Z=0`.

The section sketches and loft use those native offsets directly. No corrective
translation is added.

## Qualification

The box qualification already covers the initial correction. Extend tests
and the migration to Cylinder and Sphere in native/CSG, including all supported
axes, anchors and placements. Check 2D profile defaults explicitly. A native
parameter mutation must keep the declared center/anchor rather than a stale
numeric offset.

Change 0022 proves:

- ordinary `Box()` emits native `center=[0,0,0]`;
- `anchor=BOTTOM` and cardinal edge/corner anchors emit the correct native
  `corner=[...]`;
- direct feature-history and CSG lowering use the same anchor contract;
- a saved default Box remains centred after length/width/height parameter
  changes without rerunning Python;
- `Box.taper()` keeps the same physical geometry for CENTER and BOTTOM anchor
  choices, expressed through the correct native section offsets;
- explicit `.at(..., anchor=...)` overrides constructor datum placement;
- PythonSCAD, pyBOSL2 and CadQuery references describe the same centred default;
- full Q1-Q6 qualification remains green.

## Exit condition

> Every standard primitive has one origin convention in every compiler path, and ordinary
> `Box(...)` and `Cylinder(...)` are centered on the model origin.
