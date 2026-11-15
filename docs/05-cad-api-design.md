# Python CAD API design

> **Normative public API contract.** This document is the single source of
> truth for user-facing Forge/SCPF semantics. Compiler code, qualification
> fixtures, README examples and the website must follow this contract; they do
> not redefine it.

SCPF exposes CAD objects and relationships, not JSON commands, transports, or
an independent geometry engine. SolidCraft creates and evaluates the actual
geometry.

## User-facing model

A model does not need `@dataclass`. Numeric class fields are model parameters:

```python
class Enclosure:
    length = 80.0
    width = 50.0
    height = 30.0
    wall = 2.0
```

A model should express relationships semantically. Do not copy coordinates from
one part into another merely to make a render line up.

## Placement vocabulary

Forge separates **position**, **surface support**, **sketch-local placement**
and **assembly attachment**. These operations are deliberately not synonyms.

| Intent | Public API | Meaning |
| --- | --- | --- |
| absolute placement | `shape.at(x, y, z)` | Place a supported shape at an absolute model coordinate. |
| shape-relative alignment | `shape.at(target)` | Align the supported child CENTER to the target CENTER. Explicit anchor forms may extend this contract where documented. It does not select a support face. |
| feature on a surface | `feature.on(target, face=Faces.TOP)` | Put a within-component feature on a selected target surface. |
| explicit sketch on a body | `Sketch(on=target, parent=Anchor.TOP)` | Create a named sketch supported by the selected target face. The local 2D sketch origin is the centre of that target face. |
| profile inside a sketch | `sketch.add(profile, anchor=CENTER)` | Place the profile's selected 2D anchor on the sketch origin. CENTER is the default semantic centring operation; numeric offset is not a centring substitute. |
| deliberate sketch-local shift | `sketch.add(profile, offset=(u, v))` | Apply an explicit local 2D displacement. Use only when the design actually calls for an offset. |
| occurrence position/pose | `occurrence.at(Position(...))`, `occurrence.at(Placement(...))` | Declare an absolute XYZ position or complete occurrence pose in the parent coordinate frame. Values may be numeric or parametric and do not create a joint. |
| assembly relationship | `child.attach(parent, ...)` | Create an explicit relationship between reusable component occurrences. |

### `at()`

`at()` is geometric placement/alignment.

```python
pin = Cylinder(d=8, h=20, axis=Axis.X).at(10, 0, 5)
centered = Cylinder(d=8, h=30, axis=Axis.X).at(body)
```

`shape.at(target)` means CENTER-to-CENTER for supported direct shapes. It does
not mean "put this on a face". Use `on()` or `Sketch(on=...)` for that intent.

### `on()`

`on()` selects a target surface for a within-component feature.

```python
holes = Hole(d=8, depth=Depth.THROUGH_ALL).pattern(
    count=2,
    spacing=self.width - 24,
    axis=Axis.X,
).on(plate, face=Faces.TOP)

boss = Cylinder(d=24, h=14).on(plate, face=Faces.TOP)
```

For a Hole, `face=Faces.TOP` means drilling starts at the current top surface
and proceeds inward. `Faces` is surface-selection vocabulary; it is not an
assembly attachment vocabulary.

### Explicit `Sketch`

An explicit Sketch is user-authored 2D design intent. It is not an
implementation detail of a 3D primitive.

```python
with Sketch(name="Rounded pad", on=body, parent=Anchor.TOP) as pad:
    pad.add(
        RoundedRectangle2D(40, 30, 5),
        anchor=CENTER,
    )

body = body + pad.extrude(8)
```

For `Sketch(on=target, parent=Anchor.TOP)`:

- the target and face choose the support plane;
- the sketch's local `(0, 0)` is at the centre of that target face;
- profile placement is relative to that local sketch coordinate system;
- `anchor=CENTER` means centre the profile on the sketch origin;
- a numeric `offset=(u, v)` is reserved for a real design displacement.

Therefore code such as `offset=(-width/2, -depth/2)` used only to emulate
centering is a smell. Forge should expose the intended anchor relationship
instead.

A direct 3D primitive such as `Box` remains a native primitive; Forge must not
synthesize an unnecessary Sketch merely to construct it.

### `Position`, `Placement` and occurrence `at()`

`Position` is the absolute XYZ coordinate of an occurrence in its parent
coordinate frame. Coordinates may contain numbers, Parameters or Expressions.

```python
left = Block().at(Position(x=-50))
right = left.copy().at(Position(x=50))
```

`Placement` is the complete pose: Position plus one absolute axis-angle
orientation.

```python
panel = Panel().at(
    Placement(
        position=Position(z=160),
        rotation=(X, 90),
    )
)
```

Occurrence `at()` is declarative. `at(Position(...))` replaces XYZ while
preserving orientation; `at(Placement(...))` replaces the complete pose.
There is no occurrence `move()` or `rotate()`.

The backend command name does not define Forge semantics. A parametric Position
may lower to native SolidCraft `occurrence.move.translate`; SolidCraft 0.42
stores that expression associatively and PR #158 qualified saved-model
parameter mutation. A concrete copied Position may lower directly through
`occurrence.copy(..., translate=[...])`.

Placement must not create a `joint.create` as an implementation workaround.
Attachments remain explicit relationships and Position expressions reuse
existing parameters instead of publishing helper parameters.


### `attach()`

`attach()` is reserved for explicit relationships between reusable component
occurrences in an assembly. It is the public Forge relationship; SolidCraft
`joint.create` is an internal lowering detail.

```python
right = Block().attach(
    left,
    parent=Anchor.RIGHT,
    child=Anchor.LEFT,
)
```

A local planar `offset=(u, v)` on an attachment is measured in the attachment
frame, not in world XY.

## Direction, face and anchor vocabulary

Cardinal direction names are shared where their geometric meaning is shared:
`TOP`, `BOTTOM`, `LEFT`, `RIGHT`, `FRONT`, `BACK`.

- `Faces` selects a surface for within-component feature placement.
- `Anchor` describes an attachment/alignment reference.
- Direction selectors may be composed, for example `BOTTOM + LEFT`.
- Component anchors may identify a face or a rectangular corner such as
  `FRONT_TOP_RIGHT`.
- `AnchorFrame` is an oriented local attachment coordinate frame: `origin`
  locates the datum, `z` gives its facing direction and `x` fixes clocking.

```python
AnchorFrame(
    origin=(10, 25, 0),
    z=RIGHT,
    x=UP,
)
```

Put an anchor on a reusable component only when the datum is intrinsic to that
physical component. If the datum exists only because of one assembly, the
assembly owns the `AnchorFrame`.

## Parameter intent

Numeric names are part of the public API contract:

| Python name | Meaning | Native SolidCraft parameter |
| --- | --- | --- |
| `WIDTH = 100.0` | fixed constant | no |
| `_pitch = 160.0` | Forge/build-time input | no |
| `width = 100.0` | editable model parameter | yes |

A public model parameter that disappears before native compilation is
suspicious. Forge emits `ModelParameterWarning` instead of silently pretending
the design is still associative. Use `pv()` only where Python genuinely needs
a concrete number.

Reusable component parameters follow the same naming rule. When several parts
must share one model parameter, pass the parent parameter or expression
directly:

```python
bottom = BottomBoard(corner_radius=self.corner_radius)
roof = RoofBoard(corner_radius=self.corner_radius)
bracket = Bracket(inside_corner_radius=self.corner_radius)
```

Forge must preserve that dependency instead of creating unrelated child values.

## Features and operations

- `+` joins/adds the described CAD feature to the model; Hole intent lowers
  to a cut.
- `-` expresses subtraction/cut where supported.
- `&` expresses intersection where supported.
- `shell()` and `fillet()` are modifiers of supported feature trees.
- `Lip`, `SnapFit`, `Boss` and `Rest` are object-level feature intents;
  the compiler chooses the appropriate native SolidCraft representation.
- `Anchor.INNER_BOTTOM` refers to the inner floor of a shelled body.
- `X.MIN/CENTER/MAX` and `Y.MIN/CENTER/MAX` express placement relative to
  parent bounds rather than copied world coordinates.

## Reference implementations

Qualification pages compare Forge with PythonSCAD and pyBOSL2. Those references
answer "how is the same modelling intent expressed elsewhere?" They are not
allowed to redefine Forge behaviour.

pyBOSL2 is especially useful for reviewing anchor/attachment vocabulary;
PythonSCAD is useful as a neutral Python CSG comparison. When either library
lacks a native associative relationship equivalent, the reference must state
that limitation explicitly.

## Responsibility boundaries

```text
Python objects (SCPF)
  -> semantic compiler
  -> SolidCraft commands
  -> SolidCraft BRep, parameters and editable feature history
```

Forge may perform small dimension arithmetic needed to describe design intent.
It must not implement a competing CAD kernel, transform solver or mating
engine.

Never silently treat numeric coordinates as robust long-lived face references.
Native save/reopen and parameter-edit tests determine which relationships are
truly associative.

## Qualification rule

A public API behaviour is not considered complete merely because one example
renders correctly. It needs the appropriate Q1-Q6 evidence. A qualification
fixture is evidence for this document; the fixture itself is never the API
definition.
