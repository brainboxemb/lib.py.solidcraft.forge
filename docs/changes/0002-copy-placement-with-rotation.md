# 0002 — Copy Placement with rotation lowering

Status: **active fix for SCPF 0.3.1**  
SolidCraft target: **0.42.0**  
Extends: [0001 — Placement constructor API design](0001-position-api-design.md)

## 1. Problem

Change 0001 made occurrence pose declarative constructor/copy metadata:

```python
second = first.copy(
    placement=Placement(
        x=40,
        z=160,
        rotation=(X, 90),
    )
)
```

SCPF 0.3.0 optimised a concrete copied XYZ position into
`occurrence.copy(..., translate=[...])` even when the copy also had a
rotation. It then emitted `occurrence.move` only for the rotation with a zero
translation.

That is not equivalent in SolidCraft 0.42. The later rotation also rotates the
translation already applied by `occurrence.copy`.

The downstream five-panel HUB75 model exposed the failure. A copy declared at:

```text
x = -320
y = 0
z = 160
rotation = X 90°
```

was saved natively near:

```text
x = -320
y = -160
z = 0
```

instead of the declared Placement.

## 2. Public API decision

There is **no public API change**.

This remains correct:

```python
panel = Panel(
    placement=Placement(
        z=160,
        rotation=(X, 90),
    )
)

copy = panel.copy(
    placement=Placement(
        x=-320,
        z=160,
        rotation=(X, 90),
    )
)
```

`Placement` still means the complete absolute occurrence pose in the parent
coordinate frame.

## 3. Lowering rule

Creation-time `occurrence.copy.translate` is used only when all of these are
true:

1. the copied XYZ Placement is concrete;
2. the copied occurrence has **no rotation**.

So this remains optimised:

```python
right = left.copy(
    placement=Placement(x=400)
)
```

```json
{
  "command": "occurrence.copy",
  "params": {
    "component": "Board",
    "translate": [400, 0, 0]
  }
}
```

But a copy with rotation is created at native identity first:

```python
right = left.copy(
    placement=Placement(
        x=40,
        rotation=(Z, 90),
    )
)
```

and lowers to:

```json
{"command":"occurrence.copy","params":{"component":"Panel"}}
{"command":"occurrence.move","params":{
  "occurrence":"Panel:2",
  "translate":[40,0,0],
  "axis":[0,0,1],
  "angle":"90 deg"
}}
```

Translation and rotation therefore belong to one native placement operation and
produce the declared final pose.

## 4. Why not compensate the translation?

Forge must not pre-rotate or otherwise compensate XYZ before emitting the
native commands. That would make Forge a second transform solver and would
obscure the parent-frame semantics of `Placement`.

The smallest correct lowering is:

```text
copy without rotation + concrete XYZ
    -> occurrence.copy(translate=XYZ)

copy with rotation
    -> occurrence.copy()
    -> occurrence.move(translate=XYZ, axis=..., angle=...)

symbolic copy Placement
    -> occurrence.copy()
    -> occurrence.move(expression XYZ, ...)
```

## 5. Custom anchor implication

A copied occurrence with rotation is no longer considered positioned during
`occurrence.copy`. Any persistent custom `joint.origin` authored before the
later placement therefore remains in the component's local identity frame.

This is consistent with the complete-pose lowering: SolidCraft owns the later
local-to-world transformation.

## 6. Qualification

SCPF 0.3.1 adds a native regression with one reusable non-square Panel:

```python
left = Panel(
    placement=Placement(
        x=-40,
        rotation=(Z, 90),
    )
)

right = left.copy(
    placement=Placement(
        x=40,
        rotation=(Z, 90),
    )
)
```

The unrotated Panel is 20 × 10 × 4 mm. After Z=90° rotation the native bounds
must be:

```text
left  X=-45..-35, Y=-10..10, Z=0..4
right X= 35.. 45, Y=-10..10, Z=0..4
```

Required evidence:

- one reusable Panel definition;
- one `occurrence.copy` with **no** `translate`;
- two native `occurrence.move` commands with full translations -40 and +40;
- both moves carry Z=90°;
- no placement joint;
- SolidCraft 0.42 native measured bounds match the expected result;
- visual regression is approved.

The downstream HUB75 CAD model remains an additional integration regression.
