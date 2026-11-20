# 0001 — Placement constructor API design

Status: **active design for SCPF 0.3.0**  
SolidCraft target: **0.42.0**

> **Correction:** change [0009](0009-replay-first-placement.md) supersedes the
> ordinary `occurrence.move` fallback described below. The fallback depended on
> predicted SolidCraft occurrence names. The historical text remains here to
> record the 0.3.0 design, but it is no longer the approved replay-first
> implementation.

This change replaces ad-hoc occurrence-position parameters such as
`_x_position`, `_y_position` and `_z_position` with one explicit Forge
`Placement` value supplied when the occurrence is created.

## 1. The problem this change solves

The motivating WoodFrame code currently mixes two different kinds of data in
one component constructor:

```python
left = Board(
    name="left",
    width=self.frame_wood_thickness,
    depth=self.cabinet_depth,
    height=self.opening_height,
    _x_position=-(
        self.opening_width / 2
        + self.frame_wood_thickness / 2
    ),
    _y_position=0.0,
    _z_position=opening_bottom,
    material_name="LIGHTPLY side board",
).attach(
    bottom,
    as_built=True,
).group("WoodBoxFrame")
```

`width`, `depth`, `height` and `material_name` describe the reusable
**Board definition**.

`_x_position`, `_y_position` and `_z_position` do not describe the Board
at all. They describe where this particular **occurrence of the Board** belongs
inside its parent assembly.

Those placement values therefore must not be disguised as private Board model
parameters.

## 2. Decision

Occurrence placement is supplied as Forge metadata at occurrence creation time:

```python
left = Board(
    name="left",
    width=self.frame_wood_thickness,
    depth=self.cabinet_depth,
    height=self.opening_height,
    placement=Placement(
        x=-(half(self.opening_width) + half(self.frame_wood_thickness)),
        y=0.0,
        z=opening_bottom,
    ),
    material_name="LIGHTPLY side board",
).attach(
    bottom,
    as_built=True,
).group("WoodBoxFrame")
```

The important boundary is:

```text
Board(...)
    component-definition arguments
    + reserved occurrence metadata

Placement(...)
    occurrence pose only
```

`placement` is consumed by Forge. It is not passed to the component's
`build()` method and it does not become a Board parameter.

## 3. Public Placement type

The public value is deliberately small:

```python
Placement(
    x=0,
    y=0,
    z=0,
    rotation=None,
)
```

Where:

- `x`, `y`, `z` are the absolute coordinates of the occurrence origin in
  its parent coordinate frame;
- each coordinate may be numeric, a Forge Parameter or an Expression;
- `rotation` is optional absolute axis-angle orientation, currently
  `(axis, degrees)`;
- omitted coordinates default to zero;
- omitted rotation means identity orientation.

Example with orientation:

```python
panel = Panel(
    placement=Placement(
        x=160,
        z=160,
        rotation=(X, 90),
    )
)
```

There is **no separate public `Position` class** in this design.
`Placement` already contains the position, so wrapping XYZ in another object
adds syntax without adding a required modelling concept.

### Readable symbolic arithmetic with `half()`

Placement expressions should stay readable in Python without losing their
native parameter dependency. Prefer:

```python
placement=Placement(
    x=-(half(self.opening_width) + half(self.frame_wood_thickness)),
    z=opening_bottom,
)
```

over manually repeating `/ 2`.

`half(value)` is a Forge/Python readability helper. It returns the symbolic
expression `value / 2`; SolidCraft does not need a `half` function.

For example, Python such as:

```python
x=-(half(self.opening_width) + half(self.frame_wood_thickness))
```

lowers to an ordinary SolidCraft arithmetic expression equivalent to:

```text
-((opening_width / 2) + (frame_wood_thickness / 2))
```

The original parameters therefore remain native and editable in the saved
SolidCraft design.

## 4. Placement is creation state, not a move action

The central semantic rule is:

> **An occurrence has its Placement when Forge creates that occurrence.**

The user is not asking Forge to:

```text
1. create object at origin
2. move object afterwards
```

The user is declaring:

```text
create/place this occurrence at this pose
```

Therefore this:

```python
Board(
    placement=Placement(x=400)
)
```

means "the Board occurrence is at X=400 in its parent frame".

It does **not** mean "move the Board +400 from wherever it currently happens to
be".

The same rule applies to copies.

## 5. Copy creates a new occurrence with its Placement

A repeated occurrence should not require a post-copy placement call.

Preferred API:

```python
left = Board(
    name="left",
    width=self.frame_wood_thickness,
    depth=self.cabinet_depth,
    height=self.opening_height,
    placement=Placement(
        x=-(half(self.opening_width) + half(self.frame_wood_thickness)),
        z=opening_bottom,
    ),
    material_name="LIGHTPLY side board",
)

right = left.copy(
    name="right",
    placement=Placement(
        x=half(self.opening_width) + half(self.frame_wood_thickness),
        z=opening_bottom,
    ),
)
```

`copy()` still shares the same reusable component definition. Its
`placement` argument describes the newly created occurrence.

Copy rules:

- no `placement` supplied: inherit the source occurrence Placement;
- `placement=Placement(...)`: the new occurrence receives that complete
  Placement;
- occurrence-specific attachment is not inherited;
- an explicitly supplied occurrence `name` belongs to the new occurrence.

This is the copy equivalent of constructor-time placement; no public
`.at()` step is required.

## 6. API deliberately not selected

This change does **not** use:

```python
Board().at(Position(x=400))
Board().move(Position(x=400))
Board().move(x=400)
```

Reasons:

- the occurrence would first be constructed without the information that
  belongs to its creation;
- `Position` duplicates the position part already naturally contained by
  `Placement`;
- public occurrence `move` invites ambiguity between an absolute pose and a
  relative displacement;
- the WoodFrame source remains clearest when definition data and occurrence
  metadata are visible together in one constructor.

A future API may add an explicit editing operation if Forge ever needs to
mutate an already-existing occurrence object. That is a separate change and
does not define initial placement.

## 7. Shape geometry is a separate layer

Forge remains object-first at assembly level and expression-first inside
component geometry.

This is still valid inside a component:

```python
bottom = Box(20, 20, 4).move(
    x=10,
    y=10,
    z=-2,
)
```

Shape `.move()` is not occurrence placement.

Forge currently folds that shape translation into native primitive creation
coordinates. For example:

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

The native body is therefore created at the intended geometry coordinates; no
later `solid.move` is needed.

## 8. SolidCraft 0.42 `solid.box` contract

Complete relevant input contract:

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

| Parameter | SolidCraft 0.42 | Forge use |
| --- | --- | --- |
| `length` | required | yes |
| `width` | required | yes |
| `height` | required | yes |
| `corner` | optional | base Box path |
| `center` | optional | translated CSG primitive path |
| `operation` | optional, default `new` | explicit in CSG path |
| `targets` | optional | join/cut/intersect |
| `touching` | optional | not normally emitted by Box |
| `participants` | optional | not normally emitted by Box |
| `name` | optional | not normally emitted by Box |
| `body_name` | optional | yes for a new body |
| `body_names` | optional | not currently needed |

If both `corner` and `center` are supplied, SolidCraft uses `corner`.

A normal Forge Box remains a native primitive; Forge must not synthesize a
Sketch just to create a rectangular solid.

## 9. Shape CSG naming

For:

```python
bottom = Box(...).move(...)
front = Box(...).move(...)
return bottom + front
```

Forge creates the first body using a Forge-owned name:

```json
{
  "command": "solid.box",
  "params": {
    "operation": "new",
    "body_name": "CornerProtector",
    "center": [10, 10, -2]
  }
}
```

and explicitly targets that same body on subsequent CSG primitives:

```json
{
  "command": "solid.box",
  "params": {
    "operation": "join",
    "targets": ["CornerProtector"],
    "center": [10, -2, 10]
  }
}
```

This is not an implicit "previous command" relationship.

```text
body_name = chosen by Forge
targets   = explicit reference to that Forge-owned body name
```

## 10. Native `solid.move` is not Placement

SolidCraft also has `solid.move`, whose relevant 0.42 contract is:

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

`solid.move` is a body feature operation. It is **not** the public
implementation model for occurrence `Placement`.

Forge continues to fold ordinary Shape translation into primitive creation
coordinates where possible.

## 11. SolidCraft component creation

A reusable Forge model definition is lowered through
`component.create`.

SolidCraft 0.42 accepts:

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

| Parameter | Meaning |
| --- | --- |
| `name` | component definition name |
| `parent` | owning component |
| `parent_path` | exact placement of the parent |
| `activate` | activate the new component |
| `grounded` | ground its first occurrence |

Important SolidCraft 0.42 limitation:

> `component.create` creates the first occurrence but has no translation or
> pose parameter.

Therefore Forge cannot always express constructor-time Placement in that one
native command. That is a backend limitation, not a change to Forge semantics.

## 12. SolidCraft occurrence copy

SolidCraft 0.42 `occurrence.copy` accepts:

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

- give `occurrence` or `component`;
- `path` can disambiguate an exact placement;
- `parent` chooses the destination parent;
- `translate` is numeric XYZ in mm;
- `in_place` controls parent-local versus selected-world placement;
- `parent_path` applies to the `in_place` case.

For a numeric copied Placement:

```python
right = left.copy(
    placement=Placement(x=400)
)
```

Forge should lower directly to:

```json
{
  "command": "occurrence.copy",
  "params": {
    "component": "Board",
    "translate": [400, 0, 0]
  }
}
```

No later occurrence command is needed in this case.

## 13. SolidCraft occurrence placement fallback

SolidCraft 0.42 `occurrence.move` accepts the following placement/movement
surface:

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

Relevant rules:

- `occurrence`: occurrence id or name;
- `path`: exact occurrence placement path;
- `space`: `local` or `world`, default `local`;
- `translate`: relative XYZ; entries may be numbers or length expressions;
- `axis`, `angle`, `origin`: relative rotation form;
- `matrix`: rigid relative transform alternative;
- `to`: absolute pose;
- `to_matrix`: absolute rigid pose;
- `tolerance`: matrix tolerance;
- `capture`: default true;
- `move_grounded`: allow a grounded occurrence to be placed;
- `base_transform`: explicit starting transform used by interactive paths.

Mutual exclusion:

- `matrix` is not combined with `translate`, `axis`, `angle`, `origin`;
- `to` and `to_matrix` are alternatives;
- absolute forms are not combined with relative move forms;
- a parameter-expression `translate` is captured.

Forge may use this native command **only as a backend fallback** when
SolidCraft 0.42 cannot express constructor-time Placement in
`component.create` or `occurrence.copy`.

Known 0.42 gaps:

```text
first occurrence with non-origin Placement
    component.create has no pose
    -> component.create(...)
    -> occurrence.move(...)

copied occurrence with parametric XYZ
    occurrence.copy.translate is numeric-only
    -> occurrence.copy(...)
    -> occurrence.move(... expression ...)

orientation
    occurrence.copy has no orientation input
    -> occurrence.move(...) when required
```

These later native commands do **not** change the Forge API meaning. The
Placement existed before compilation.

## 14. Parametric Placement

Example:

```python
right = left.copy(
    placement=Placement(
        x=self.opening_width / 2
            + self.frame_wood_thickness / 2,
        z=opening_bottom,
    )
)
```

If those coordinates contain Forge expressions, SolidCraft 0.42 cannot put
them in `occurrence.copy.translate`.

The qualified fallback is therefore conceptually:

```json
{"command":"occurrence.copy","params":{"component":"Board"}}
{"command":"occurrence.move","params":{
  "occurrence":"Board:2",
  "translate":[
    "opening_width / 2 + frame_wood_thickness / 2",
    0,
    "opening_bottom"
  ]
}}
```

SolidCraft stores parameter-referencing translations associatively. PR #158
already proved that changing the parameter in the saved SolidCraft model moves
the occurrence without rerunning Python/Forge.

The important distinction is:

```text
Forge source:
    constructor-time declarative Placement

SolidCraft 0.42 lowering:
    occurrence.move expression only because creation cannot encode it
```

## 15. Occurrence identity

Body geometry and occurrences have different identity mechanics.

For body CSG, Forge controls the body name:

```text
CornerProtector
```

and emits it explicitly in `body_name` / `targets`.

For occurrences, SolidCraft creates occurrence identity. Current replay-first
Forge 0.42 lowering uses version-qualified labels such as:

```text
Board:1
Board:2
```

when a later fallback command must address the created occurrence.

That targeting rule is a SolidCraft 0.42 backend contract, not part of public
`Placement` semantics.

## 16. Required WoodFrame result

The original code:

```python
left = Board(
    name="left",
    width=self.frame_wood_thickness,
    depth=self.cabinet_depth,
    height=self.opening_height,
    _x_position=-(
        self.opening_width / 2
        + self.frame_wood_thickness / 2
    ),
    _y_position=0.0,
    _z_position=opening_bottom,
    material_name="LIGHTPLY side board",
).attach(
    bottom,
    as_built=True,
).group("WoodBoxFrame")
```

must become:

```python
left = Board(
    name="left",
    width=self.frame_wood_thickness,
    depth=self.cabinet_depth,
    height=self.opening_height,
    placement=Placement(
        x=-(half(self.opening_width) + half(self.frame_wood_thickness)),
        z=opening_bottom,
    ),
    material_name="LIGHTPLY side board",
).attach(
    bottom,
    as_built=True,
).group("WoodBoxFrame")
```

The result must have:

- no `_x_position`, `_y_position`, `_z_position` Board parameters;
- no helper placement parameters generated by Forge;
- one reusable Board definition;
- occurrence Placement kept separate from Board geometry parameters;
- saved SolidCraft parameter changes continuing to drive placement;
- no hidden placement joint.

## 17. Qualification gate

SCPF 0.3.0 is not complete until these cases pass:

1. constructor with default Placement;
2. constructor with numeric XYZ Placement;
3. constructor with parametric XYZ Placement;
4. constructor with Placement plus rotation;
5. `copy()` inherits Placement when no override is supplied;
6. `copy(placement=...)` creates the copy at the supplied Placement;
7. copied parametric symmetric placements remain associative after saved-model
   parameter mutation;
8. Placement plus explicit Attachment works without a hidden placement joint;
9. placement expressions reuse existing parameters and create no helper
   parameters;
10. HUB75 WoodFrame no longer contains private position constructor parameters;
11. native SolidCraft 0.42 saved/reopen mutation evidence is green.

## 18. Change-management rule

This is change **0001**.

Future design changes are added as new records:

```text
docs/changes/0002-....md
docs/changes/0003-....md
```

A later change that supersedes this design must explicitly link back to
`0001` and state what is being replaced. Do not silently turn old change
records into a different design history.
