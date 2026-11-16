# Change 0022 — Native Box anchor datum

**Status:** design and implementation  
**SolidCraft target:** 0.42.0

## Problem

Forge gave one `Box()` two different native meanings:

- feature-history Box: XY centred, bottom face at Z=0 through `corner=[-L/2,-W/2,0]`;
- direct CSG Box: fully centred through `center=[0,0,0]`.

That made the meaning depend on the compiler path.

SolidCraft 0.42 already has the useful primitive distinction: `solid.box`
accepts either a native `center` datum or a native `corner` datum.

Forge is still an unstable API, so this change does not preserve the old
bottom-based default merely for compatibility. The default should be the most
useful and predictable primitive behaviour.

## Public API

`Box` is:

```python
Box(length, width, thickness, *, anchor=Anchor.CENTER)
```

The anchor is the Box point placed at model coordinate `(0, 0, 0)` before
any later `.at()` placement.

Examples:

```python
Box(80, 50, 10)                         # fully centred around XYZ = 0
Box(80, 50, 10, anchor=BOTTOM)          # bottom-face centre at Z = 0
Box(80, 50, 10, anchor=FRONT + BOTTOM) # front/bottom edge centred on X
```

The same Anchor vocabulary is used for primitive datum choice and later Box
placement. No second Box-origin enum and no compatibility `origin=` alias are
added.

## Native lowering

For the default CENTER anchor Forge emits native:

```text
solid.box(..., center=[0, 0, 0])
```

For BOTTOM or another cardinal anchor Forge calculates the corresponding native
corner and emits:

```text
solid.box(..., corner=[...])
```

Feature-history and direct-CSG lowering use the same rule. A plain `Box()`
therefore has the same geometry regardless of compiler path.

Forge does not emulate CENTER with a corrective move.

## `.at()` remains later placement

```python
Box(...).at(x, y, z, anchor=FRONT + BOTTOM)
```

means that the explicit `.at()` call places the selected Box anchor at the
requested point. That explicit placement takes precedence over the constructor
anchor datum.

## CENTER alignment

A plain Box has geometric centre `(0,0,0)`.

For an explicitly bottom-anchored Box the centre is
`(0,0,thickness/2)`. Other cardinal anchors are handled from the same selector
vector.

This keeps `shape.at(other_shape)` CENTER-to-CENTER alignment consistent with
the real native datum.

## Taper limit

`Box.taper()` currently describes a front plane at Z=0 and rear plane at
Z=depth. Therefore taper requires:

```python
Box(..., anchor=BOTTOM).taper(...)
```

Calling taper on the default centred Box fails early. Origin-aware taper
semantics are separate work.

## Qualification

The existing `simple-box` case now qualifies the useful default rather than
preserving the old API behaviour.

Required evidence:

- `Box()` emits native `solid.box center=[0,0,0]`;
- feature-history and CSG Box use the same default;
- PythonSCAD, pyBOSL2 and CadQuery reference models are centred;
- changing length/width/height in the saved SolidCraft design keeps the centre
  fixed while all six bounds move symmetrically;
- `anchor=BOTTOM` and a combined cardinal anchor lower to native corner data;
- explicit `.at(..., anchor=...)` controls later placement;
- taper requires explicit BOTTOM;
- no corrective sketch or move is emitted.

## Exit condition

> A plain Box is centred everywhere, and a different datum is requested
> explicitly with the existing Anchor vocabulary.
