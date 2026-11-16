# Change 0022 — Native Box anchor selection

**Status:** design and implementation  
**SolidCraft target:** 0.42.0

## Problem

Forge gave one `Box()` two different native meanings.

The feature-history path used a bottom-centred corner:

```text
solid.box(..., corner=[-length / 2, -width / 2, 0])
```

while the direct CSG path used:

```text
solid.box(..., center=[0, 0, 0])
```

for the same unplaced Box.

SolidCraft 0.42 already has the right native distinction: `solid.box` accepts
either `center=[x,y,z]` or `corner=[x,y,z]`.

## Public API

`Box` uses the existing anchor vocabulary:

```python
Box(length, width, thickness, *, anchor=Anchor.CENTER)
```

`anchor` means: **which Box anchor is located at model coordinate
`(0, 0, 0)` before later placement**.

The useful default is the geometric centre:

```python
Box(80, 50, 10)                          # fully centred
Box(80, 50, 10, anchor=BOTTOM)           # bottom-face centre at Z=0
Box(80, 50, 10, anchor=FRONT + BOTTOM)   # front/bottom edge centre at origin
Box(80, 50, 10, anchor=FRONT + LEFT + BOTTOM)  # corner at origin
```

Forge is still in unstable-release development. Change 0022 deliberately picks
one clear default instead of preserving the previous accidental bottom-centred
behaviour.

## Native lowering

For the default `CENTER` anchor Forge emits:

```text
solid.box(..., center=[0, 0, 0])
```

For another supported anchor Forge calculates the corresponding native
`corner=[...]` directly from the Box dimensions and selected datum.

The feature-history and direct-CSG paths use the same rule.

A translated CSG Box adds the translation to the selected native datum; it does
not add a corrective move after construction.

## `.at()` remains placement

Constructor `anchor=` chooses the Box's unplaced datum. `.at(..., anchor=...)`
is later placement.

For example:

```python
Box(80, 50, 10).at(0, 0, 0, anchor=BOTTOM)
```

creates a centred Box constructor, then explicitly places its bottom-face centre
at the requested point. The resulting native Box is emitted from that placement
datum directly.

## `taper()`

`Box.taper(from_z=..., inset=...)` is anchor-aware.

`from_z` is a distance measured from the Box's bottom face, regardless of
which Box anchor is located at model origin. For a centred Box, the front plane
is therefore at `-thickness / 2`; for `anchor=BOTTOM` it is at `Z=0`.

The section sketches and loft use those native offsets directly. No corrective
translation is added.

## Qualification

Change 0022 proves:

- ordinary `Box()` emits native `center=[0,0,0]`;
- `anchor=BOTTOM` and cardinal edge/corner anchors emit the correct native
  `corner=[...]`;
- direct feature-history and CSG lowering use the same anchor contract;
- a saved default Box remains centred after length/width/height parameter
  changes without rerunning Python;
- `Box.taper()` keeps the same physical geometry for CENTER and BOTTOM anchor
  choices, expressed through the correct native section offsets;
- explicit `.at(..., anchor=...)` overrides constructor datum placement;
- PythonSCAD, pyBOSL2 and CadQuery references describe the same centred default;
- full Q1-Q6 qualification remains green.

## Exit condition

> One Box anchor has one meaning in every compiler path, and ordinary
> `Box(...)` means a native Box centred on its model origin.
