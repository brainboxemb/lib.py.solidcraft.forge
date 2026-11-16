# Agent reference: PythonSCAD, pyBOSL2 and CadQuery

Purpose: avoid repeated external documentation lookups while writing Forge
qualification comparison models. Read only this file unless the needed
operation is absent.

This file is a **local working cache**, not the source of truth for the
external projects. If behaviour here conflicts with installed/upstream code,
verify upstream and refresh this file.

Snapshot used when this cache was written:

- PythonSCAD: `pythonscad/pythonscad@0d1b8a0ce1a9b98b4b56b45bbfc928376638788b`
- pyBOSL2: `pinkfish/pybosl2@d4279910c12435ed7224b3406616e495db1c96ec`
- CadQuery: PyPI `cadquery==2.8.0`

## Selection rule

Use **PythonSCAD** to show a neutral Python CSG expression of the same visible
model.

Use **pyBOSL2** when anchors, faces, orientation or attachment intent is the
important comparison.

Use **CadQuery** as the third default comparison, especially for object
Location, assembly hierarchy, workplane and constraint-vs-placement semantics.
If a useful CadQuery comparison is technically unavailable, record an explicit
qualification exception with the reason.

Do not translate Forge syntax mechanically. Preserve modelling intent.


## Primitive origins: Forge vs PythonSCAD vs pyBOSL2

This is the local lookup for change 0022. Use it instead of consulting external
repositories for the common primitive defaults and syntax.

| Primitive | Forge intended default | PythonSCAD equivalent | pyBOSL2 equivalent |
| --- | --- | --- | --- |
| rectangular solid | `Box(x, y, z)`: centered XYZ | `cube([x,y,z], center=True)` | `cuboid([x,y,z])` |
| rectangular solid resting on Z=0 | `Box(x,y,z, anchor=BOTTOM)` | `cube([x,y,z], center="00-")` | `cuboid([x,y,z], anchor=Anchor.BOTTOM)` |
| sphere | `Sphere(r)`: centered | `sphere(r=r)` | `sphere(radius=r)` |
| cylindrical solid | `Cylinder(d=d, h=h)`: centered on its axis (planned 0022) | `cylinder(d=d,h=h,center=True)` | `cyl(diameter=d,height=h)` |
| cylinder starting on Z=0 | `Cylinder(d=d,h=h,anchor=BOTTOM)` (planned 0022) | `cylinder(d=d,h=h)` | `cyl(diameter=d,height=h,anchor=Anchor.BOTTOM)` |

**Important:** PythonSCAD's raw cube/cylinder defaults are not the Forge
defaults; pass an explicit `center=` value in comparison examples. pyBOSL2's
`cuboid`/`cyl` centered conventions are the closer user-facing reference.
Forge's contract is defined in its own API; the external libraries are used to
express comparable geometry, not to dictate implementation details.

The 2D dimension-defined primitives `Rectangle2D` and `Circle2D` are also
centered by default. Coordinate-defined `Polygon2D` keeps the coordinates
supplied by the caller, rather than silently centering the polygon.

**Verification:** The box conventions are already reflected in the local
`examples/simple-box` references. The cylinder rows describe the target for
the expanded change 0022 and must not be advertised as implemented until their
native/CSG regression tests pass.


## PythonSCAD: subset used by qualification references

Typical import:

```python
from pythonscad import *
```

Relevant concepts used by Forge comparisons:

```python
cube([x, y, z], center=True)
cube([x, y, z], center="00-")  # centered X/Y, grows from Z=0 in +Z
sphere(r=radius)
cylinder(d=diameter, h=height, center=True)

a | b      # union
a - b      # difference
a & b      # intersection

shape.translate([x, y, z])
shape.rotate([rx, ry, rz])

profile.linear_extrude(height=h)
shape.export("model.stl")
show(shape)
```

PythonSCAD's three-character cube center code is ordered X/Y/Z. Runtime
verification against 1.1.2 shows the sign is a placement-side symbol rather
than an intuitive growth-direction sign: `"-"` places the datum on the
negative/min side so geometry grows toward the positive axis; `"+"` does the
opposite. Therefore `"00-"` represents a **deliberately bottom-anchored** Forge Box (`anchor=BOTTOM`), not the Forge default.

Prefer explicit transforms in references when that makes the geometry obvious.
Do not claim that a PythonSCAD transform is equivalent to a persisted
SolidCraft joint/parameter relationship.

Before adding a PythonSCAD call not listed here, inspect the installed/upstream
API once and then add only the verified minimal syntax to this cache.

## pyBOSL2: subset used by qualification references

Typical imports:

```python
from pybosl2 import Anchor, cuboid, cyl, sphere, rect, circle
```

### 3D primitives

```python
cuboid([x, y, z])
cuboid([x, y, z], anchor=Anchor.BOTTOM)
cyl(diameter=d, height=h)
sphere(radius=r)
```

Boolean operators:

```python
a | b
a - b
a & b
```

Transforms:

```python
shape.translate([x, y, z])
shape.rotate(degrees, [ax, ay, az])

shape.right(x)
shape.left(x)
shape.front(y)
shape.back(y)
shape.up(z)
shape.down(z)
```

### Anchors

Face anchors:

```text
Anchor.CENTER
Anchor.TOP
Anchor.BOTTOM
Anchor.FRONT
Anchor.BACK
Anchor.LEFT
Anchor.RIGHT
```

Edge anchors:

```text
TOP_FRONT TOP_BACK TOP_LEFT TOP_RIGHT
BOTTOM_FRONT BOTTOM_BACK BOTTOM_LEFT BOTTOM_RIGHT
FRONT_LEFT FRONT_RIGHT BACK_LEFT BACK_RIGHT
```

Corner anchors:

```text
TOP_FRONT_LEFT
TOP_FRONT_RIGHT
TOP_BACK_LEFT
TOP_BACK_RIGHT
BOTTOM_FRONT_LEFT
BOTTOM_FRONT_RIGHT
BOTTOM_BACK_LEFT
BOTTOM_BACK_RIGHT
```

### Placement / attachment

Place a child's local origin at a parent anchor without reorienting it:

```python
parent.position(Anchor.TOP_FRONT_LEFT, child)
```

Place a child on a face without changing its axes:

```python
parent.align(Anchor.FRONT, child, align=Anchor.LEFT)
```

Mate child and parent anchors, including orientation:

```python
parent.attach(
    Anchor.TOP,
    child,
    child_anchor=Anchor.BOTTOM,
    overlap=0,
    spin=0,
)
```

Attachments are deferred; use `.realize()` when one combined measurable solid
is required. Any resulting 3D shape can be exported directly with
`shape.export("model.stl")`.

```python
model = parent.attach(Anchor.RIGHT, child, child_anchor=Anchor.LEFT).realize()
```

### 2D profiles

Rounded rectangle:

```python
profile = rect(
    [width, depth],
    rounding=radius,
    anchor=Anchor.CENTER,
)
```

`rect()` defaults to CENTER anchoring. This makes it a useful comparison for
Forge sketch-profile centring.

Circle:

```python
profile = circle(diameter=20)
```

Extrusion:

```python
solid = profile.linear_extrude(height=8)
```


## CadQuery: subset used by qualification references

Pinned comparison version:

```text
cadquery==2.8.0
```

CadQuery is required by default for every qualification case. Use its native
solid/workplane/Assembly/Location vocabulary to express the closest useful
comparison. SolidCraft-specific persistence semantics remain native
qualification evidence rather than something to imitate in CadQuery.

Typical import:

```python
import cadquery as cq
```

Bottom-based block used by the Placement reference:

```python
block = cq.Solid.makeBox(
    20,
    20,
    10,
    cq.Vector(-10, -10, 0),
)
```

Independent assembly locations:

```python
model = cq.Assembly()
model.add(block, name="fixed", loc=cq.Location((0, 0, 0)))
model.add(block, name="placed", loc=cq.Location((40, 0, 0)))
```

The qualification runner exports CadQuery Assembly references to STL and
compares the resulting envelope with the same independent expected bounds.

CadQuery Location is a comparison for visible occurrence pose. It does not
prove SolidCraft saved-design parameter expressions, native occurrence identity
or joint persistence; those remain SolidCraft-native qualification targets.

## Semantic limits of the comparison

The references compare author intent and visible geometry. They do **not**
automatically prove equivalents for:

- SolidCraft native feature history;
- saved-design `parameters.change`;
- persisted topology identity;
- SolidCraft native joint solving;
- Forge component-definition/occurrence browser hierarchy;
- `as_built=True` semantics.

When one of these is the qualification target, state the limit in the reference
source and keep the comparison simple.

## When external lookup is justified

Consult upstream only when:

1. the required operation is not listed here;
2. a reference fails against the installed library;
3. PythonSCAD/pyBOSL2/CadQuery dependency versions are intentionally upgraded;
4. an upstream behavioural change is suspected.

After verifying upstream, update this file with the smallest useful new fact
and update the snapshot commit if the cache has been intentionally refreshed.
