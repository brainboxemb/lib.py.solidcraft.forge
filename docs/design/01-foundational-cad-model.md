# Foundational CAD model

Status: **normative design foundation for SCPF 0.3.0**

This document defines the occurrence model that must be implemented and
qualified before Forge 0.3.0 is a valid downstream CAD baseline.

## 1. Three separate concepts

Forge deliberately separates three concepts.

### ModelDefinition

A ModelDefinition describes **what a reusable physical part is**: geometry,
material, features, parameters and local anchors. Multiple occurrences may
share one definition.

### Placement

A Placement describes **the complete pose of one occurrence in its parent
coordinate frame**.

```python
Board(
    width=frame_wood_thickness,
    height=opening_height,
    placement=Placement(
        x=-half(opening_width) - half(frame_wood_thickness),
        z=opening_bottom_z,
    ),
)
```

Placement is declarative occurrence data, not an action. Position may contain
numbers, Parameter values or Expressions. Rotation is part of the same pose:

```python
Placement(
    x=100,
    z=half(frame_height),
    rotation=(Y, 90),
)
```

"Absolute" means relative to the occurrence's parent coordinate frame. It does
**not** mean "numeric only" or "evaluated once". A parametric Placement must
remain associative in the saved SolidCraft design.

### Attachment

An Attachment describes **a relationship between occurrences**.

```python
bracket = CornerBracket(...).attach(
    board,
    parent=Anchor.FRONT_TOP_LEFT,
    child=Anchor.BACK_BOTTOM_RIGHT,
)
```

Attachments may lower to native SolidCraft joints. Placement alone must not.

## 2. Public occurrence API

The primary placement API is constructor data:

```python
part = Part(..., placement=Placement(...))
```

A repeated occurrence receives its desired pose explicitly:

```python
right = left.copy(
    placement=Placement(x=half(opening_width))
)
```

The public occurrence API intentionally has no movement-operation conveniences:

- no `occurrence.move(...)`;
- no `occurrence.at(...)`;
- no `occurrence.rotate(...)`.

Those methods made declarative occurrence state look like a sequence of
imperative transformations. Rotation belongs in Placement.

`copy()` without an explicit Placement preserves the source Placement.
`copy(placement=...)` replaces it for the new occurrence. Copying never
duplicates the shared ModelDefinition.

## 3. API semantics are not backend command names

Forge Placement is a CAD-domain concept. SolidCraft `occurrence.move` is a
native implementation mechanism.

Therefore this is valid lowering:

```text
Forge:
    placement=Placement(x=half(opening_width))

SolidCraft:
    occurrence.move(..., translate=["opening_width / 2", 0, 0])
```

It does **not** mean Forge exposes a move action.

The compiler may choose different native commands for different Placement
forms, provided the saved SolidCraft model preserves the same declared pose.

## 4. Proven native SolidCraft 0.42 placement capability

PR #158 already qualified native parametric occurrence placement.

The proven native shape is:

```json
{"command":"parameters.add","params":{"name":"offset","expression":"40 mm"}}
{"command":"occurrence.copy","params":{"component":"Block"}}
{"command":"occurrence.move","params":{
  "occurrence":"Block:2",
  "translate":["offset",0,0]
}}
```

The saved design was mutated from `offset=40` to `offset=70` without
rerunning Python. The second Block moved from X=40 to X=70 and no placement
joint was generated.

SCPF 0.3.0 changes the **public source representation** from `.move(...)` to
`Placement(...)`; it must retain this proven native associative behaviour.

## 5. Foundational use cases

These use cases drive implementation and release qualification.

### P1 — default Placement

```python
block = Block()
```

Equivalent occurrence pose:

```python
Placement()
```

Expected: origin position, identity orientation, no placement joint.

### P2 — numeric Placement

```python
block = Block(placement=Placement(x=40, y=10, z=5))
```

Expected final occurrence pose is exactly (40, 10, 5). The compiler may use
the appropriate native creation/placement command.

A directly executed reusable component file is currently compiled as standalone
root geometry rather than an occurrence. Explicit non-zero root-component
Placement is therefore a documented capability gap; P2 is qualified inside an
assembly occurrence.

### P3 — parametric Placement

```python
placed = Block(
    placement=Placement(x=self.offset)
)
```

Baseline:

```text
offset = 40
x = 40
```

Saved-model mutation:

```text
offset = 70
x = 70
```

No Python rerun and no generated placement joint. This is the public-API
successor of the already-qualified PR #158 parametric-move fixture.

### P4 — repeated numeric Placement

```python
left = Block(placement=Placement(x=-40))
right = left.copy(placement=Placement(x=40))
return left + right
```

Expected:

- one shared Block definition;
- two occurrences;
- left X=-40;
- right X=40.

Where SolidCraft supports concrete creation-time translation, Forge may lower
the second occurrence directly through `occurrence.copy(..., translate=...)`.

### P5 — repeated parametric Placement

```python
left = Block(
    placement=Placement(x=-half(spacing))
)
right = left.copy(
    placement=Placement(x=half(spacing))
)
```

For `spacing=80`, positions are -40/+40. After saved-model mutation to
`spacing=120`, positions must become -60/+60 without rerunning Python.

This is a mandatory qualification because it represents the same dependency
shape used by the HUB75 WoodFrame.

### P6 — Placement plus rotation

```python
strip = Strip(
    placement=Placement(
        z=half(height),
        rotation=(Y, 90),
    )
)
```

After `height=100 -> 140`, Z must change 50 -> 70 while orientation remains
Y=90 degrees.

### P7 — Placement plus Attachment

```python
parent = Board(
    placement=Placement(x=half(frame_width))
)
child = Bracket(...).attach(parent, ...)
```

Placement describes the parent's pose. Attachment describes the child's
relationship to the parent. After parameter mutation the parent follows its
Placement expression and the child follows through the explicit Attachment.

A child may have an initial seed Placement before attachment, but Forge must
not manufacture a hidden placement joint.

### P8 — parameter scope

Expressions used only by Placement must reference the existing parent
parameters. Forge must not publish derived helper parameters such as
`Board_x`, `Board_offset` or `Board_half_width`.

Shared parent parameters are emitted once.

## 6. HUB75 WoodFrame release case

The WoodFrame must support symmetric parametric board Placement:

```python
left = Board(
    ...,
    placement=Placement(
        x=-half(opening_width) - half(frame_wood_thickness),
        z=opening_bottom_z,
    ),
)

right = Board(
    ...,
    placement=Placement(
        x=half(opening_width) + half(frame_wood_thickness),
        z=opening_bottom_z,
    ),
)
```

Changing `opening_width` in the saved SolidCraft design must move the left
board toward -X and the right board toward +X, without:

- rerunning Forge;
- creating new component definitions;
- hidden placement joints;
- duplicate placement parameters.

## 7. Occurrence identity is a separate compiler contract

Two questions must remain separate:

1. What does Placement mean?
2. How does a backend command reliably target an occurrence?

The first is the Forge CAD model defined above. The second is a compiler/native
identity problem.

A backend identity limitation must not redefine Placement or invalidate already
qualified native parametric placement. If a particular lowering is unreliable,
that lowering must be corrected or explicitly capability-gapped.

Runtime result-handle execution is a separate possible future execution mode
tracked in roadmap issue #168. It is not part of the normal SCPF 0.3.0
replay-first compiler contract.

## 8. Release gate

SCPF 0.3.0 may be released only when:

- P1-P8 command/API tests are green where applicable;
- parametric Placement reuses the proven SolidCraft 0.42 expressed-move
  behaviour from PR #158;
- saved-design parameter mutation proves P3 and P5;
- no public occurrence movement convenience remains;
- no hidden placement joint is emitted;
- parameter-list scope remains clean;
- the downstream HUB75 CAD model is migrated to Placement and passes its
  qualification/tests.
