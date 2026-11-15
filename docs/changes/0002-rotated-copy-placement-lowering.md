# 0002 — Rotated copy Placement lowering

Status: **active fix for SCPF 0.3.1**  
SolidCraft target: **0.42.0**  
Extends: [0001 — Placement constructor API design](0001-position-api-design.md)

## 1. Problem found by downstream HUB75 qualification

Change 0001 defines one public semantic object:

```python
panel.copy(
    placement=Placement(
        x=-320,
        z=160,
        rotation=(X, 90),
    )
)
```

The complete Placement means one final pose in the parent coordinate frame.

SCPF 0.3.0 incorrectly split a numeric copied Placement into two native
operations:

```json
{"command":"occurrence.copy","params":{
  "component":"Panel",
  "translate":[-320,0,160]
}}
{"command":"occurrence.move","params":{
  "occurrence":"Panel:2",
  "translate":[0,0,0],
  "axis":[1,0,0],
  "angle":"90 deg"
}}
```

SolidCraft 0.42 `occurrence.move` is a relative rigid move. The second command
therefore rotates the transform that already contains the copy translation.
That changes the translation itself; the occurrence no longer ends at
X=-320, Y=0, Z=160.

The downstream five-panel HUB75 native qualification exposed this: copied
panels moved into Y and lost their intended Z position.

## 2. Decision

A single Forge Placement must not be split across native operations when the
later operation would transform an earlier part of that same Placement.

For a copied occurrence:

```text
numeric XYZ, no rotation
    -> occurrence.copy(... translate=XYZ)

numeric XYZ + rotation
    -> occurrence.copy(...) at identity
    -> occurrence.move(... translate=XYZ, axis=..., angle=...)

symbolic XYZ
    -> occurrence.copy(...)
    -> occurrence.move(... expression ...)
```

So the rotated example becomes:

```json
{"command":"occurrence.copy","params":{
  "component":"Panel"
}}
{"command":"occurrence.move","params":{
  "occurrence":"Panel:2",
  "translate":[-320,0,160],
  "axis":[1,0,0],
  "angle":"90 deg"
}}
```

The translation and rotation are now interpreted together from the copied
occurrence's identity transform.

## 3. Public API does not change

This is a compiler lowering correction only.

The SCPF 0.3.x API remains:

```python
Panel(
    placement=Placement(
        x=...,
        y=...,
        z=...,
        rotation=(axis, degrees),
    )
)

copy = panel.copy(
    placement=Placement(...)
)
```

There is still:

- no public `Position` wrapper;
- no occurrence `.at()`, `.move()` or `.rotate()` for initial placement;
- no hidden placement joint.

## 4. Creation-time placement rule refined

Change 0001 says Forge prefers native create/copy-time placement where the
backend can represent it.

This change makes the safety condition explicit:

> Forge may use creation/copy-time placement only when doing so does not change
> the meaning of the remaining Placement operations.

For SolidCraft 0.42, numeric `occurrence.copy.translate` is safe for a
translation-only Placement. It is not safe as the translation half of a
Placement that will receive a later relative rotation.

## 5. Required command contract

For:

```python
first = Panel()
second = first.copy(
    placement=Placement(
        x=30,
        z=40,
        rotation=(X, 90),
    )
)
```

Forge must emit one copy at identity:

```json
{"command":"occurrence.copy","params":{
  "component":"Panel"
}}
```

followed by one complete placement operation:

```json
{"command":"occurrence.move","params":{
  "occurrence":"Panel:2",
  "translate":[30,0,40],
  "axis":[1,0,0],
  "angle":"90 deg"
}}
```

It must not emit `translate` on both commands or split translation and
rotation as separate pose stages.

## 6. Native geometry qualification

A 20 x 10 x 2 mm Panel is authored at:

```text
X = -10 .. +10
Y =  -5 ..  +5
Z =   0 ..  +2
```

A copied Panel with:

```python
Placement(
    x=30,
    z=40,
    rotation=(X, 90),
)
```

must end at:

```text
X = 20 .. 40
Y = -2 .. 0
Z = 35 .. 45
```

The qualification is intentionally geometric. A command sequence can look
plausible while still producing the wrong world transform, which is exactly
how the 0.3.0 defect escaped its command-level tests.

## 7. Release gate

SCPF 0.3.1 may be released only when:

1. command tests require identity `occurrence.copy` for a rotated copy;
2. the subsequent `occurrence.move` contains both final XYZ and rotation;
3. native SolidCraft 0.42 measured bounds match the declared rotated-copy
   geometry;
4. fixed-camera visual regression is approved;
5. the existing SCPF qualification suite remains green;
6. downstream HUB75 native CAD qualification passes with the released 0.3.1
   pin.
