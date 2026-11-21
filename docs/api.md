# Forge API

> **Primary cross-object API contract.** This document defines stable
> user-facing Forge/SCPF semantics that span more than one public Python object.
> Exact exported names, signatures, defaults and enum members come from the
> current Python implementation and its public docstrings. The generated API
> reference and agent index are derived from those implementation sources.
>
> When implementation and this cross-object contract disagree, treat that as
> documentation/API drift to be resolved explicitly; do not silently preserve
> obsolete wording from this document.

SCPF exposes CAD objects and relationships, not JSON commands, transports, or
an independent geometry engine. SolidCraft creates and evaluates the actual
geometry.

## Modelling style: object-first assemblies, expression-first geometry

Forge is deliberately **object-first at the component/assembly level** and
**expression-first inside component geometry**.

At assembly level, named Python objects represent meaningful physical
occurrences:

```python
left = Board()
right = left.copy(
    placement=Placement(x=160)
)
bracket = CornerBracket().attach(left, ...)
```

The variables represent parts in the design, so later relationships refer to
the actual Python occurrence object rather than a generated SolidCraft label.

Inside one component, geometry remains a lightweight feature/expression model:

```python
class Board:
    def build(self):
        body = Box(self.width, self.depth, self.height)
        holes = Hole(d=5, depth=Depth.THROUGH_ALL).repeat_linear(...)
        return body - holes
```

Do not turn every primitive or feature into an assembly object. Conversely, do
not flatten physical assembly parts into an anonymous transform expression tree.
This boundary is intentional and is part of the Forge API design.

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
| explicit sketch on a body | `Sketch(on=target, parent=Anchor.TOP)` | Create a named sketch attached to the selected native SolidCraft target face. Profile coordinates are authored in that native sketch frame; Forge does not reconstruct a separate face-centre coordinate system. |
| profile inside a sketch | `sketch.add(profile, anchor=None)` | Use the profile's natural placement default. Dimension-defined Circle2D/Rectangle2D/RoundedRectangle2D resolve the omitted anchor to CENTER; coordinate-defined Text2D/Polygon2D keep their own coordinates. |
| deliberate sketch-local shift | `sketch.add(profile, offset=(u, v))` | Apply an explicit local 2D displacement. For dimension-defined profiles this shifts the centred profile; for Text2D it sets the native insertion-point displacement. |
| occurrence position/pose | `Component(..., placement=Placement(...))`, `copy(placement=...)` | Declare the occurrence pose at creation/copy time in the parent coordinate frame. Placement itself does not create a joint. Forge replay variables bind the real SolidCraft occurrence ids when a later native move is needed. |
| assembly relationship | `child.attach(parent, ...)` | Create an explicit relationship between reusable component occurrences. |

### Native primitive anchor datum

Direct standard 3D primitives use CENTER as their constructor datum:

```python
box = Box(80, 50, 10)
pin = Cylinder(d=8, h=20)
ball = Sphere(12)
```

The public signatures are:

```python
Box(length, width, thickness, *, anchor=Anchor.CENTER)
Cylinder(*, d, h, axis=Axis.Z, anchor=Anchor.CENTER)
Cone(*, d, top_d=0, h, axis=Axis.Z, anchor=Anchor.CENTER)
Sphere(radius, *, anchor=Anchor.CENTER)
```

`anchor` selects which world-cardinal primitive datum lies at model
coordinate `(0, 0, 0)` before later placement.

For Cylinder the anchor is resolved against its world XYZ bounds after the axis
is chosen. Axis.X therefore uses LEFT/RIGHT for the axial ends; Axis.Y uses
FRONT/BACK; Axis.Z uses BOTTOM/TOP. The remaining cardinal directions select
tangent datums on the transverse circular bounds.

Forge lowers each primitive through the native command that SolidCraft already
owns:

- Box CENTER maps to native `center`; another Box anchor maps to the matching
  native `corner`.
- Cylinder always maps to native `base`; Forge derives that base from axis,
  height, diameter and the selected anchor.
- Cone maps to native `solid.cone` with `diameter`, `top_diameter`, `height`,
  `axis` and a derived native `base`. Because a cone/frustum has unequal end
  radii, Forge supports CENTER and the two axial end anchors only.
- Sphere maps to native `center`; Forge derives the center from the selected
  tangent/center anchor.

The same calculation is used in direct and Boolean CSG paths. Do not add a
corrective move merely to preserve an old constructor convention.

Dimension-defined sketch profiles Rectangle2D, Circle2D and RoundedRectangle2D
are already centered by default from change 0018. Polygon2D and Text2D keep
authored coordinates/insertion points.

`Box.taper(from_z=..., inset=...)` is anchor-aware: `from_z` is measured
from the actual Box bottom face regardless of the constructor anchor.

This is intentionally a breaking cleanup while Forge remains unstable. Models
that require an old base/bottom datum must state it explicitly with `anchor=`.

See [change 0022](background/changes/0022-native-box-origin.md).

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
holes = Hole(d=8, depth=Depth.THROUGH_ALL).repeat_linear(
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

- Forge asks SolidCraft for the current body faces and selects the unique largest planar +Z face;
- Forge passes SolidCraft's returned face pick and face index to native `sketch.create`;
- SolidCraft owns the persistent face attachment and the sketch's local coordinate frame;
- Forge passes authored profile coordinates directly in that native sketch frame instead of adding a reconstructed face-centre offset;
- `project_edges=False` is explicit so the result does not depend on a session setting;
- `anchor=None` means use the profile type's defined default;
- for Circle2D, Rectangle2D and RoundedRectangle2D that default is CENTER;
- explicit `anchor=CENTER` centres a dimension-defined profile on the sketch origin;
- a numeric `offset=(u, v)` is reserved for a real design displacement.

Therefore code such as `offset=(-width/2, -depth/2)` used only to emulate
centering is a smell. Circle2D, Rectangle2D and RoundedRectangle2D use CENTER
when anchor is omitted; `offset=(u, v)` is applied afterwards as a real local
design displacement.

Polygon2D is different because its vertex coordinates already define its
sketch-local placement. Text2D likewise uses SolidCraft's text insertion point.
For these coordinate-defined profiles an omitted anchor remains `None`, so
Forge does not invent a profile centre. Text2D may still use
`Sketch.add(..., offset=(u, v))` to set its native insertion-point
displacement. Explicit `anchor=CENTER` is not supported for Polygon2D or
Text2D yet. Polygon2D keeps its existing offset/lowering limits.

Semantic profile centering was introduced by
[change 0018](background/changes/0018-sketch-profile-centering.md). The profile-specific
omitted-anchor rule that preserves coordinate-defined Text2D placement is
recorded in
[change 0020](background/changes/0020-coordinate-profile-default-anchor.md).

Selective Sketch extrusion uses SolidCraft's own profile selection. Pass fixed
sketch-local points with `Sketch.extrude(..., profiles=[(x, y), ...])`.
Forge sends those points as native `solid.extrude profiles` selections; it
does not expose profile indices or generated curve ids. SolidCraft 0.42 stores
successful point selections by their surrounding curves where possible, so the
selected profile can be found again when the saved design recomputes.
`exact_regions=True` requests the exact region containing each point.

Profile pick points are fixed numeric authoring picks, not editable Forge
Parameters. SolidCraft 0.42's point-selection command field accepts numeric
Sketch coordinates rather than parameter expressions.

A direct 3D primitive such as `Box` remains a native primitive; Forge must not
synthesize an unnecessary Sketch merely to construct it.

#### Native Sketch pattern and mirror operations

A profile already authored in the active Sketch can seed an associative native
rectangular pattern:

```python
seed = sketch.add(Circle2D(d=20), offset=(-304, 0))
row = sketch.rectangular_pattern(
    seed,
    count=9,
    spacing=76,
    direction=Axis.X,
)
sketch.mirror(row, axis=Axis.Y)
```

The source may also be a supported Slot profile or a result returned by an
earlier supported Sketch pattern/mirror operation. Pattern and mirror return
Sketch operation handles; they do not expose SolidCraft curve ids.

Current limits include attached Sketch qualification, rectangular patterns,
fixed 2D directions or `Axis.X`/`Axis.Y`, and mirror over the Sketch X/Y
origin axes. A SolidCraft mirror keeps the entity set selected when the mirror
was authored; increasing an upstream pattern count later does not
automatically add the new entities to that existing mirror.

See [change 0033](background/changes/0033-associative-sketch-pattern-mirror.md).

#### Signed and symmetric Sketch extrusion

The current public signature is:

```python
Sketch.extrude(
    distance,
    *,
    sym=False,
    profiles=None,
    exact_regions=False,
)
```

A positive finite `distance` follows the sketch-plane normal. A negative
finite distance reverses that normal. `sym=True` requires a positive finite
distance and splits the extrusion equally across both sides of the sketch
plane. `Depth.THROUGH_ALL` is available only for an attached Sketch and cannot
be combined with `sym=True`.

Forge does not expose a second `direction=` argument for current Sketch
extrusion. Direction is expressed by the sign of `distance` or by
`sym=True`.

See [change 0024](background/changes/0024-signed-sketch-extrude.md).

#### Native Slot profiles

Explicit Sketches support the five native SolidCraft Slot constructors:

```python
SlotCenterToCenter2D(p0, p1, width)
SlotOverall2D(p0, p1, width)
SlotCenterPoint2D(center, end, width)
SlotArcThreePoint2D(start, through, end, width)
SlotArcCenter2D(center, start, width, *, end=None, sweep=None)
```

Slot authoring points are currently fixed sketch-local numeric coordinates.
`width` may be a fixed positive number, `Parameter` or `Expression`; the
symbolic value is lowered directly to SolidCraft's native Slot width field and
remains a driving native dimension. Parametric Slot length/position remains a
separate qualification item rather than being emulated in Forge.

Slots can participate in the supported native sketch
`rectangular_pattern()` and `mirror()` operations.

See [change 0027](background/changes/0027-native-sketch-slot-family.md).

### Occurrence `Placement`

`Placement` is reserved occurrence metadata, separate from component model
parameters:

```python
left = Board(
    width=frame_wood_thickness,
)

right = left.copy(
    name="right",
    placement=Placement(
        x=160,
    ),
)
```

`Placement(x=0, y=0, z=0, rotation=None)` stores the absolute pose in the
parent coordinate frame. Position values may contain Parameters or Expressions.

The component factory consumes `placement=` before building the reusable
component definition, so placement never becomes a model parameter. There is no
separate public `Position` object and no occurrence `.at()`, `.move()` or
`.rotate()` for initial placement.

SolidCraft 0.42 can apply a numeric translation directly in
`occurrence.copy(..., translate=...)`. Forge uses that direct form whenever it
is sufficient.

Some Placements need a second native command. Examples are a rotated copy, a
symbolic position, or the first occurrence created by `component.create`.
SolidCraft returns the real occurrence id from `component.create` and
`occurrence.copy`. Forge therefore gives that returned id a named replay
variable such as `$board_2`.

The replay document stores the variable name, not the temporary SolidCraft id.
Every live run and every later replay binds the variable again from the command
result before a command uses it. Forge never predicts SolidCraft browser names
such as `Board:2`.

This keeps `copy(placement=...)` as one Forge operation even when SolidCraft
needs more than one native command to realise the pose. The second native
`occurrence.move` is a backend detail; it does not add a second Forge movement
operation.

Placement must not create a `joint.create` as an implementation workaround.
Attachments remain explicit relationships and Placement expressions reuse
existing parameters instead of publishing helper parameters.

The replay-variable correction is recorded in
[change 0013](background/changes/0013-correct-0010-placement-cases.md).

SolidCraft 0.42 has one grounding limitation: an expression-based
`occurrence.move` on a grounded occurrence does not follow later parameter
changes. Therefore Forge leaves a physical root occurrence ungrounded when its
Placement position contains Parameters or Expressions. A fixed root occurrence
still uses the normal grounded behaviour. This is a backend compatibility rule,
not a change to the public meaning of Placement. See
[change 0014](background/changes/0014-parametric-root-grounding.md).

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

Forge generates replayable SolidCraft 0.42 commands and never makes up
occurrence names such as `Block:2`. Every physical occurrence has a stable
Forge-side id and a deterministic replay variable. During live execution or
later replay, `component.create` and `occurrence.copy` bind those variables
to the actual SolidCraft occurrence ids before a joint command uses them.

Copied occurrences can therefore be valid attachment endpoints without
predicting browser numbering. The replay document still contains only the
variable name; concrete runtime ids remain in the separate replay log.

A normal attachment currently requires both parent and child Placement
rotations to be `None`. Forge does not yet transform every Anchor,
AnchorFrame and AnchorTopology point/axis through occurrence rotation, so a
rotated parent or child is rejected before command lowering rather than using a
translation-only approximation. Ordinary rotated Placement remains supported
outside normal attachments. `as_built=True` also remains compatible with
rotated Placement because it relates already-positioned occurrences and does
not lower anchor frames.

Chained normal attachments remain unsupported until their SolidCraft solve and
replay order has been qualified. See
[change 0010](background/changes/0010-replay-safe-attachments.md),
[change 0013](background/changes/0013-correct-0010-placement-cases.md) and
[change 0017](background/changes/0017-transform-safe-attachments.md).

### `group()`

`group(name)` changes only the SolidCraft browser hierarchy.

Forge represents the group with an empty SolidCraft component and explicitly
sets that group to `grounded=false`. Grouping must not add a joint, Placement
or solver constraint.

If the physical root occurrence is inside a group, grouping itself does not
change its grounding decision. The empty group does not become the fixed part.
For SolidCraft 0.42, a root occurrence with parameter-driven Placement remains
ungrounded so its occurrence move can follow later parameter changes.

One reusable definition may have occurrences in different groups. Forge uses
SolidCraft 0.42 `occurrence.copy(parent=...)` when a later copy belongs under a
different group or back at the design root. The component definition remains
shared.

See [change 0011](background/changes/0011-grouping-is-hierarchy-only.md).

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

Reusable child-component defaults are fixed unless explicitly published with
`component(..., include=...)`. For example:

```python
Bracket = component(
    CornerBracket,
    include=("inside_corner_radius",),
)
```

`include="*"` explicitly publishes all public child defaults. A mapping may
publish one selected child default under a chosen shared model name.

When several parts must share one parent parameter, pass the parent Parameter
or Expression directly:

```python
bottom = BottomBoard(corner_radius=self.corner_radius)
roof = RoofBoard(corner_radius=self.corner_radius)
bracket = Bracket(inside_corner_radius=self.corner_radius)
```

Forge must preserve that existing dependency instead of creating unrelated or
duplicated child parameters. This contract is recorded in
[change 0003](background/changes/0003-explicit-component-parameter-publication.md).

Reusable component definition identity also includes fixed build-only inputs.
Forge rejects arbitrary mutable/opaque Python objects, but its own immutable
selector values are valid build inputs when they reduce to deterministic
primitive data. This includes public expressions such as `BOTTOM + LEFT`,
`Edges.from_profile(...)`, axis tokens such as `X`, and fixed bound offsets
such as `X.MIN + 10`. Two different selector inputs must not share one native
component definition. See
[change 0021](background/changes/0021-selector-definition-identity.md).

Parameter namespacing applies only to native CAD expressions. Ordinary strings
are opaque user data. A text value, material name, sketch name, feature name or
font name must never be rewritten merely because one word matches a parameter
name.

For example, publishing a child parameter named `width` may rename the native
parameter reference to `d1_Label_width`, but `Text2D("width")` must still
produce the literal text `"width"`. This compiler rule is recorded in
[change 0015](background/changes/0015-typed-native-expressions.md).

Parameter publication by itself is not proof that a saved design remains
associative. Forge tracks dependencies carried by emitted native expressions.
A public parameter with no emitted dependency triggers
`ModelParameterWarning`. If user model code calls `pv()` on a parameter that
also remains native elsewhere, Forge warns that only part of the model may
follow later SolidCraft edits. Internal Forge numeric checks and authoring-time
pick coordinates do not count as user `pv()` calls.

Root model classes and root `@assembly` classes use the same diagnostic rule.
See [change 0016](background/changes/0016-parameter-dependency-diagnostics.md).

## Features and operations

- `+` joins/adds the described CAD feature to the model; Hole intent lowers
  to a cut.
- `-` expresses subtraction/cut where supported.
- `&` expresses intersection where supported.
- `shell()`, `fillet()` and `chamfer()` are modifiers of supported feature trees.
- `rectangular_pattern()` and `circular_pattern()` repeat already-applied native history features. Both keep one native SolidCraft pattern feature instead of expanding independent Python copies. Circular patterns support principal or fixed XYZ axes plus an optional fixed axis origin; native construction/edge/face axis selectors are separate future extensions.
- `fillet(..., edges=...)` and `chamfer(..., edges=...)` use the same edge-selection vocabulary where SolidCraft accepts the same edge picks: `Edges.VERTICAL`, supported two-direction Box edge selectors, `Edges.from_profile(...)`, `Edges.from_vertices(...)` and explicit XYZ edge picks.
- `Lip`, `SnapFit`, `Boss` and `Rest` are object-level feature intents;
  the compiler chooses the appropriate native SolidCraft representation.
- `Anchor.INNER_BOTTOM` refers to the inner floor of a shelled body.
- `X.MIN/CENTER/MAX` and `Y.MIN/CENTER/MAX` express placement relative to
  parent bounds rather than copied world coordinates.

### Native Hole family

Forge exposes explicit native hole intent rather than requiring a caller to
construct every recess or thread from Boolean primitives:

```python
Hole(*, d, depth=Depth.THROUGH_ALL, direction=None)

CounterboreHole(
    *,
    d,
    counterbore_d,
    counterbore_depth,
    depth=Depth.THROUGH_ALL,
    direction=None,
)

CountersinkHole(
    *,
    d,
    countersink_d,
    countersink_angle=90,
    depth=Depth.THROUGH_ALL,
    direction=None,
)

ThreadedHole(
    *,
    thread,
    depth=Depth.THROUGH_ALL,
    d=None,
    direction=None,
    hand="right",
    thread_depth=None,
    modeled=False,
    ease_out=None,
)
```

The simple `Hole` remains compatible with the existing face-relative repeated
hole path. The explicit native Hole-family constructors are positioned with
`at()` and keep their recess/thread intent in one native feature.

See [change 0037](background/changes/0037-explicit-native-hole-family.md).

### Native history patterns

`rectangular_pattern()` and `circular_pattern()` operate on already-applied
native history features rather than expanding independent Python copies.
Circular patterns support the currently documented principal/fixed XYZ axis and
optional fixed axis origin forms.

See [change 0036](background/changes/0036-native-circular-feature-patterns.md).

## Reference implementations

Qualification pages compare Forge with PythonSCAD, pyBOSL2 and CadQuery by
default. Those references answer "how is the same modelling intent expressed
elsewhere?" They are not allowed to redefine Forge behaviour.

PythonSCAD is useful as a neutral Python CSG comparison; pyBOSL2 is especially
useful for anchor/attachment vocabulary; CadQuery provides a distinct
object/workplane/assembly/Location comparison. If a technically meaningful
reference cannot be implemented, the case must carry an explicit documented
exception. A missing reference or a convenience-only exception is not
qualified evidence.

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
