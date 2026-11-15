# Foundational CAD model

Status: **normative design foundation for SCPF 0.3.0**

This document defines the occurrence-positioning model that implementation,
qualification, guides and downstream CAD models must follow.

## 1. Separate concepts

### ModelDefinition

A ModelDefinition describes what one reusable physical part is: geometry,
features, material, parameters and local anchors. Multiple occurrences may
share one definition.

### Position

A Position is an absolute XYZ coordinate in an occurrence's parent coordinate
frame.

```python
Position(
    x=-half(opening_width) - half(frame_wood_thickness),
    z=opening_bottom_z,
)
```

Coordinates may be numbers, Parameters or Expressions. "Absolute" means in the
parent coordinate frame; it does not mean numeric-only or evaluated once.

Position is data. It never means "move by this amount".

### Placement

A Placement is the complete pose of one occurrence:

```python
Placement(
    position=Position(x=100, z=half(frame_height)),
    rotation=(Y, 90),
)
```

Placement combines Position with one absolute axis-angle orientation.

### Attachment

An Attachment describes a relationship between occurrences.

```python
bracket = CornerBracket().attach(
    board,
    parent=Anchor.FRONT_TOP_LEFT,
    child=Anchor.BACK_BOTTOM_RIGHT,
)
```

Attachment may lower to a native SolidCraft joint. Position/Placement alone
must not create a joint.

## 2. Public occurrence API

Occurrence positioning is declarative:

```python
left = Board().at(Position(x=-400))
right = left.copy().at(Position(x=400))
```

`at(Position(...))` replaces only XYZ and preserves the occurrence's current
orientation.

```python
rotated = Panel().at(
    Placement(
        position=Position(z=160),
        rotation=(X, 90),
    )
)

copy = rotated.copy().at(Position(x=160, z=160))
```

The copy keeps the X-axis 90 degree orientation while receiving the new
Position.

`at(Placement(...))` replaces the complete pose.

There is no public occurrence `.move()` or `.rotate()`. Shape-level
`Shape.at()`, `Shape.move()` and geometry transforms are separate APIs and
are unaffected.

## 3. Copy contract

`copy()`:

- creates another occurrence of the same ModelDefinition;
- preserves the source Placement initially;
- clears occurrence-specific attachment and explicit occurrence name;
- does not duplicate component feature history.

A copied occurrence is normally repositioned declaratively:

```python
right = left.copy().at(Position(x=half(spacing)))
```

This is not a relative displacement. The resulting right-hand X position is
exactly `half(spacing)` in the parent coordinate frame.

## 4. API semantics versus native lowering

Forge Position/Placement are CAD-domain concepts. SolidCraft command names are
backend implementation details.

A parametric source position such as:

```python
right = Block().at(Position(x=self.offset))
```

may lower to:

```json
{"command":"occurrence.move","params":{
  "occurrence":"Block:2",
  "translate":["offset",0,0]
}}
```

That does not make Forge `at()` a move action. The native command stores the
declared position expression.

For concrete copied positions, Forge may use creation-time placement:

```text
occurrence.copy(..., translate=[40, 0, 0])
```

The compiler chooses the native representation; the public semantics remain the
same.

## 5. Proven SolidCraft 0.42 behaviour

PR #158 already qualified native parametric occurrence placement:

- one reusable Block definition;
- a second Block occurrence;
- native `occurrence.move.translate=["offset",0,0]`;
- no hidden placement joint;
- saved-model mutation `offset=40 -> 70`;
- the second occurrence moved from X=40 to X=70 without rerunning Python.

SCPF 0.3.0 changes the public source vocabulary to
`at(Position(...))`. It must retain that proven associative native behaviour.

## 6. Required use cases

### P1 — origin

```python
block = Block()
```

Expected Position is (0, 0, 0), identity orientation, no placement joint.

### P2 — numeric Position

```python
block = Block().at(Position(x=40, y=10, z=5))
```

Expected final XYZ is exactly (40, 10, 5).

### P3 — parametric Position

```python
block = Block().at(Position(x=self.offset))
```

Baseline: `offset=40 -> x=40`.

After mutating the saved SolidCraft design to `offset=70`: `x=70`, without
rerunning Python and without a placement joint.

### P4 — repeated numeric Position

```python
left = Block().at(Position(x=-40))
right = left.copy().at(Position(x=40))
```

Expected: one shared Block definition and two occurrences at -40/+40.

### P5 — repeated parametric Position

```python
left = Block().at(Position(x=-half(spacing)))
right = left.copy().at(Position(x=half(spacing)))
```

For `spacing=80`: -40/+40. After saved-model mutation to `spacing=120`:
-60/+60, without rerunning Python.

This is mandatory because it matches the HUB75 WoodFrame dependency shape.

### P6 — Position plus orientation

```python
strip = Strip().at(
    Placement(
        position=Position(z=half(height)),
        rotation=(Y, 90),
    )
)
```

After `height=100 -> 140`, Z changes 50 -> 70 while orientation remains
Y=90 degrees.

### P7 — copy preserves orientation

```python
first = Panel().at(
    Placement(
        position=Position(x=-160, z=160),
        rotation=(X, 90),
    )
)
second = first.copy().at(Position(x=160, z=160))
```

Both occurrences remain X=90 degrees. Only Position differs.

### P8 — Position plus Attachment

A parent may have a parametric Position while a child is attached to it. After
saved-model mutation the parent follows its Position expression and the child
follows through the explicit Attachment. Forge must not introduce a hidden
placement joint.

### P9 — parameter scope

Position expressions reuse existing parent parameters. Forge must not publish
derived helper parameters such as `Board_x`, `Board_offset` or
`Board_half_width`.

## 7. HUB75 WoodFrame release case

```python
left = Board().at(
    Position(
        x=-half(opening_width) - half(frame_wood_thickness),
        z=opening_bottom_z,
    )
)

right = Board().at(
    Position(
        x=half(opening_width) + half(frame_wood_thickness),
        z=opening_bottom_z,
    )
)
```

Changing `opening_width` in the saved SolidCraft design must move left toward
-X and right toward +X without:

- rerunning Forge;
- duplicating component definitions;
- hidden placement joints;
- duplicate/helper placement parameters.

## 8. Identity is a separate compiler concern

The CAD contract answers "where/how should this occurrence stand?" Occurrence
identity answers "how does a backend command address it?". These are separate
layers.

An identity limitation must not redefine Position or invalidate already
qualified parametric placement semantics. Runtime result-handle execution is a
separate possible future mode tracked by issue #168 and is not part of the
normal SCPF 0.3.0 replay-first contract.

## 9. Release gate

SCPF 0.3.0 is a valid baseline only when:

- P1-P9 API/command tests are green where applicable;
- P3 and P5 have saved-design mutation evidence;
- parametric Position retains the proven SolidCraft 0.42 expressed-placement
  behaviour from PR #158;
- no public occurrence `.move()` or `.rotate()` remains;
- `.at()` accepts Position or Placement only;
- no hidden placement joint is generated;
- parameter scope remains clean;
- the downstream HUB75 model is migrated and qualified.
