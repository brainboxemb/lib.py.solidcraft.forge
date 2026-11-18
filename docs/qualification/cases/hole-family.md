# Native Hole family

## Use scenario

A model author needs the common mechanical hole forms without drawing helper
circles or subtraction solids by hand.

The qualified family contains:

- `Hole`: a simple cylindrical through or blind hole;
- `CounterboreHole`: a cylindrical recess above the main bore;
- `CountersinkHole`: a conical entry above the main bore;
- `ThreadedHole`: a tapped hole with cosmetic or modeled thread intent.

## Forge API

```python
body = body + Hole(
    d=6,
    direction=(0, 0, -1),
).at(-45, 0, top)

body = body + CounterboreHole(
    d=6,
    counterbore_d=12,
    counterbore_depth=4,
    direction=(0, 0, -1),
).at(-15, 0, top)

body = body + CountersinkHole(
    d=6,
    countersink_d=12,
    countersink_angle=90,
    direction=(0, 0, -1),
).at(15, 0, top)

body = body + ThreadedHole(
    thread="M6",
    d=5,
    direction=(0, 0, -1),
    thread_depth=10,
    modeled=True,
    ease_out="short",
).at(45, 0, top)
```

## Semantics

Each constructor represents one mechanical manufacturing intent. The family is
kept explicit rather than growing one `Hole` constructor with unrelated
counterbore, countersink and thread options.

The optional `d` on `ThreadedHole` overrides the native tap-drill diameter.
Without it, SolidCraft chooses the drill from the thread designation.

`modeled=False` keeps thread information as native metadata.
`modeled=True` asks SolidCraft to cut the thread geometry.

## SolidCraft mapping

Every feature lowers one-to-one to one native `solid.hole` command:

- simple: diameter/depth only;
- counterbore: `type=counterbore`, `cb_diameter`, `cb_depth`;
- countersink: `type=countersink`, `cs_diameter`, `cs_angle`;
- threaded: `thread` plus optional `hand`, `thread_depth`, `modeled`,
  and `ease_out`.

No helper Sketch, Cylinder or Extrude feature is generated.

## Qualification fixture

The fixture is one 120 × 40 × 12 mm plate with four holes at
X = -45, -15, 15 and 45 mm.

The first three visible hole forms are compared with independent PythonSCAD,
pyBOSL2, CadQuery and build123d geometry.

The threaded reference models intentionally reproduce only the Ø5 M6 tap-drill
envelope. Thread metadata and modeled thread geometry are SolidCraft-native
behaviour and are proved by the native command/history evidence.

## Acceptance criteria

- four native `solid.hole` commands are emitted;
- no helper Sketch is emitted;
- one native plate body remains;
- native history contains four Hole features;
- simple, counterbore, countersink and thread intent remain distinct;
- the shared body × feature unit matrix applies all four constructors to every
  compatible direct and derived body.
