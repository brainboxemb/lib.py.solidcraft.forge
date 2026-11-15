# 0001 — Position API design

Status: **active design for SCPF 0.3.0**  
SolidCraft target: **0.42.0**  
Supersedes the scattered Position/Placement discussion in `docs/design/` for
this change.

## 1. Goal

Forge needs one clear placement model for two different levels:

1. **shape geometry inside one component**;
2. **component occurrences inside an assembly**.

Those levels must not be mixed.

The public assembly API becomes:

```python
left = Board().at(Position(x=-400))
right = left.copy().at(Position(x=400))
```

There is no public occurrence `.move()` or occurrence `.rotate()`.

Shape-level geometry transforms such as:

```python
bottom = Box(20, 20, 4).move(x=10, y=10, z=-2)
```

remain valid because they are compiled into primitive coordinates rather than
a later occurrence move.

---

## 2. Forge concepts

### Position

```python
Position(x=0, y=0, z=0)
```

Meaning:

- absolute XYZ coordinate in the occurrence's parent coordinate frame;
- values may be numeric, Parameter or Expression;
- Position is data, not a relative movement.

### Placement

```python
Placement(
    position=Position(x=100, z=160),
    rotation=(Y, 90),
)
```

Meaning:

- complete occurrence pose;
- Position plus one absolute axis-angle orientation.

### Attachment

Attachment is a relationship between occurrences and is separate from
Position/Placement. Position must never be implemented as a hidden joint.

---

## 3. Shape creation: `solid.box`

Forge's ordinary `Box` creates native SolidCraft box geometry directly.

### SolidCraft 0.42 complete input contract

```json
{
  "command": "solid.box",
  "params": {
    "length": "length expression",
    "width": "length expression",
    "height": "length expression",

    "corner": ["x", "y", "z"],
    "center": ["x", "y", "z"],

    "operation": "new | join | cut | intersect",
    "targets": ["BodyName"],
    "touching": "separate | one_body",
    "participants": ["BodyName"],

    "name": "timeline feature name",
    "body_name": "single new body name",
    "body_names": ["body 1", "body 2"]
  }
}
```

### Parameter meaning

| Parameter | SolidCraft 0.42 | Forge Box uses | Notes |
| --- | --- | --- | --- |
| `length` | required | yes | X size; number or length expression |
| `width` | required | yes | Y size; number or length expression |
| `height` | required | yes | Z size; number or length expression |
| `corner` | optional | yes | minimum corner; Forge base Box uses this |
| `center` | optional | CSG path uses it | box remains centred when dimensions change |
| `operation` | optional, default `new` | CSG path explicitly uses it | `new`, `join`, `cut`, `intersect` |
| `targets` | optional | yes for join/cut/intersect | body names to operate on |
| `touching` | optional, default `separate` | not currently emitted by ordinary Box | join behaviour |
| `participants` | optional | not currently emitted by ordinary Box | overrides target scope |
| `name` | optional | not normally emitted for Box | timeline feature name |
| `body_name` | optional | yes for new body | Forge owns this name |
| `body_names` | optional | no | names for multiple created bodies |

If both `corner` and `center` are supplied, SolidCraft uses `corner`.

### Forge base Box lowering

Python:

```python
class Board:
    width = 100
    depth = 20
    height = 12

    def build(self):
        return Box(self.width, self.depth, self.height)
```

Forge lowers the centred-X/Y Box to a native primitive:

```json
{
  "command": "solid.box",
  "params": {
    "length": "width",
    "width": "depth",
    "height": "height",
    "corner": ["-(width) / 2", "-(depth) / 2", 0],
    "body_name": "Board"
  }
}
```

No sketch is synthesized.

---

## 4. Shape `.move()`: compile-time geometry placement

Example:

```python
bottom = Box(20, 20, 4).move(
    x=10,
    y=10,
    z=-2,
)
```

This does **not** lower to `solid.move` and does not require a later target
lookup.

Forge folds the shape translation into the primitive coordinates.

Conceptually:

```json
{
  "command": "solid.box",
  "params": {
    "length": 20,
    "width": 20,
    "height": 4,
    "center": [10, 10, -2],
    "operation": "new",
    "body_name": "CornerProtector"
  }
}
```

For a CSG continuation:

```python
bottom = Box(...).move(...)
front = Box(...).move(...)
return bottom + front
```

the first primitive starts the body:

```json
{
  "command": "solid.box",
  "params": {
    "center": [10, 10, -2],
    "operation": "new",
    "body_name": "CornerProtector"
  }
}
```

and later primitives explicitly target that Forge-owned body name:

```json
{
  "command": "solid.box",
  "params": {
    "center": [10, -2, 10],
    "operation": "join",
    "targets": ["CornerProtector"]
  }
}
```

The relationship is therefore explicit in JSON. It is not "apply this to the
previous command".

### Identity rule for shape geometry

```text
body_name = Forge-owned
targets   = explicit references to that Forge-owned name
```

That is why shape geometry does not have the same identity problem as repeated
component occurrences.

---

## 5. Native body move: `solid.move`

SolidCraft also has a real body move/copy command. Forge currently does **not**
use it for `Shape.move()`, but its contract is relevant and must not be
confused with occurrence placement.

### SolidCraft 0.42 complete input contract

```json
{
  "command": "solid.move",
  "params": {
    "bodies": ["BodyName"],
    "occurrences": [[1, 2]],

    "translate": ["x", "y", "z"],
    "origin": ["x", "y", "z"],
    "axis": [0, 0, 1],
    "angle": "90 deg",

    "matrix": [1,0,0,10, 0,1,0,0, 0,0,1,0],
    "tolerance": 1e-9,

    "copy": false,

    "name": "timeline feature name",
    "body_name": "new body name",
    "body_names": ["new body 1"],
    "participants": ["BodyName"]
  }
}
```

Rules:

- `bodies`: bodies to transform;
- `occurrences`: component occurrence paths to copy; requires `copy: true`;
- `translate`: translation after rotation;
- `origin`: rotation pivot;
- `axis`: rotation axis;
- `angle`: angle expression;
- `matrix`: rigid transform alternative to translate/origin/axis/angle;
- `tolerance`: matrix orthonormality tolerance, default `1e-9`, max `1e-3`;
- `copy: true`: keep originals and transform copies;
- scale, shear, mirror and projective matrices are refused.

Forge 0.3.0 choice:

> Do not lower ordinary `Shape.move()` through `solid.move`; keep folding the
> translation into primitive creation coordinates where possible.

---

## 6. Component creation: `component.create`

A Forge model object becomes a reusable SolidCraft component definition and its
first occurrence.

### SolidCraft 0.42 accepted parameters

```json
{
  "command": "component.create",
  "params": {
    "name": "Board",
    "parent": "ParentComponent",
    "parent_path": [1, 4],
    "activate": true,
    "grounded": false
  }
}
```

| Parameter | Meaning | Forge currently uses |
| --- | --- | --- |
| `name` | component definition name | yes |
| `parent` | owning component | for nested/grouped structures |
| `parent_path` | exact placement of parent | not normal flat case |
| `activate` | make new component active | compiler-specific use only |
| `grounded` | ground first occurrence | yes where required |

SolidCraft creates the first occurrence as part of component creation.

---

## 7. Copying a component occurrence: `occurrence.copy`

### SolidCraft 0.42 complete input contract

```json
{
  "command": "occurrence.copy",
  "params": {
    "occurrence": "Board:1",
    "component": "Board",
    "path": [1, 4],
    "parent": "Frame",
    "translate": [400, 0, 0],
    "in_place": false,
    "parent_path": [1]
  }
}
```

Rules:

- give `occurrence` **or** `component`;
- when `occurrence` is present, `component` is ignored;
- `path` identifies an exact selected placement;
- `parent` defaults to the copied occurrence's parent;
- `translate` is numeric XYZ in mm;
- `in_place: false` keeps the selected transform in the parent frame;
- `in_place: true` copies at the selected world transform and interprets
  `translate` in world axes;
- `parent_path` is read with `in_place: true`.

### Forge numeric Position

Python:

```python
left = Board()
right = left.copy().at(Position(x=400))
```

Preferred native lowering:

```json
{
  "command": "occurrence.copy",
  "params": {
    "component": "Board",
    "translate": [400, 0, 0]
  }
}
```

For a purely numeric Position no follow-up occurrence move is required.

---

## 8. Occurrence placement: `occurrence.move`

Forge has **no public occurrence `.move()`**. Native
`occurrence.move` is a SolidCraft lowering mechanism for Position/Placement.

### SolidCraft 0.42 complete input contract

```json
{
  "command": "occurrence.move",
  "params": {
    "occurrence": "Board:2",
    "path": [2],
    "space": "local",

    "translate": ["opening_width / 2", 0, 0],
    "axis": [0, 0, 1],
    "angle": "90 deg",
    "origin": [0, 0, 0],

    "matrix": [1,0,0,10, 0,1,0,0, 0,0,1,0],

    "to": {
      "position": [400, 0, 0],
      "axis": [0, 0, 1],
      "angle": "90 deg"
    },
    "to_matrix": [1,0,0,400, 0,1,0,0, 0,0,1,0],

    "tolerance": 1e-9,
    "capture": true,
    "move_grounded": false,
    "base_transform": []
  }
}
```

### Parameter meaning

| Parameter | Meaning |
| --- | --- |
| `occurrence` | occurrence id or name; required |
| `path` | exact occurrence placement path |
| `space` | `local` or `world`; default `local` |
| `translate` | relative XYZ move; entries may be numbers or length expressions |
| `axis` | rotation axis; default Z |
| `angle` | radians as number, or angle expression |
| `origin` | rotation pivot |
| `matrix` | rigid relative move instead of translate/axis/angle/origin |
| `to` | absolute pose: position plus optional axis/angle |
| `to_matrix` | absolute pose as rigid matrix |
| `tolerance` | matrix tolerance; default `1e-9`, max `1e-3` |
| `capture` | default true; false leaves pending position |
| `move_grounded` | default false; true permits grounded occurrence |
| `base_transform` | explicit starting transform used by browser/drag path |

Mutual-exclusion rules:

- `matrix` cannot be combined with `translate`, `axis`, `angle`, `origin`;
- `to` and `to_matrix` are absolute alternatives;
- an absolute target cannot be combined with the relative move parameters;
- expression-driven `translate` is captured and cannot use
  `capture: false`.

### Forge parametric Position

Python:

```python
right = Board().at(
    Position(x=half(opening_width))
)
```

Current qualified SolidCraft 0.42 lowering:

```json
{
  "command": "occurrence.move",
  "params": {
    "occurrence": "Board:2",
    "translate": ["opening_width / 2", 0, 0]
  }
}
```

SolidCraft stores parameter-referencing translate entries as
`expressed_moves`. If `opening_width` changes later in the saved design, the
occurrence follows without rerunning Forge.

This behaviour was qualified in Forge PR #158.

---

## 9. Identity: body names versus occurrence names

This distinction is essential.

### Body geometry

Forge chooses the body name itself:

```json
{"command":"solid.box","params":{"operation":"new","body_name":"Frame"}}
{"command":"solid.box","params":{"operation":"join","targets":["Frame"]}}
```

So:

```text
"Frame" = Forge-owned identity
```

### Component occurrence

SolidCraft creates occurrence placements and gives them occurrence identity.

Current replay-first Forge 0.42 lowering relies on version-qualified labels such
as:

```text
Board:1
Board:2
```

when a later command must address a copied occurrence.

So:

```text
"Board:2" = SolidCraft occurrence identity used by the 0.42-qualified backend
```

This is a backend/version contract, not part of the public Forge Position API.

---

## 10. Public Forge API decision

### Allowed

```python
board = Board()

left = board.at(Position(x=-400))

rotated = Panel().at(
    Placement(
        position=Position(z=160),
        rotation=(X, 90),
    )
)

right = rotated.copy().at(Position(x=160, z=160))
```

Semantics:

- `.at(Position(...))` replaces XYZ and preserves orientation;
- `.at(Placement(...))` replaces the complete pose;
- `copy()` creates another occurrence of the same reusable definition and
  initially preserves Placement.

### Not part of the occurrence API

```python
Board().move(...)
Board().rotate(...)
```

Those action-style occurrence methods are removed.

Shape geometry still has its own transform API.

---

## 11. Required qualification

The change is complete only when all of these pass:

1. default Position at origin;
2. numeric Position;
3. parametric Position;
4. repeated numeric Position;
5. symmetric repeated parametric Position;
6. Position plus orientation;
7. `copy().at(Position(...))` preserves orientation;
8. Position plus Attachment;
9. no helper/duplicate placement parameters;
10. no hidden placement joint;
11. saved-model parameter mutation moves the occurrence without rerunning Forge;
12. downstream HUB75 WoodFrame uses the new API successfully.

CadQuery may be used as an additional comparison implementation for assembly
Location semantics. SolidCraft remains the native truth for saved parameter
associativity and occurrence identity.

---

## 12. Change-management rule

This document records change **0001**.

Future design changes go into new files:

```text
docs/changes/0002-....md
docs/changes/0003-....md
```

Do not silently rewrite this decision when a later change supersedes it. The
later change must say what it changes and link back to this file.
