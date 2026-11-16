# Change 0022 — Native Box anchor datum

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

`anchor` means which Box datum lies at model coordinate `(0, 0, 0)` before
later placement.

The default is the geometric centre:

```python
Box(80, 50, 10)
Box(80, 50, 10, anchor=BOTTOM)
Box(80, 50, 10, anchor=FRONT + BOTTOM)
Box(80, 50, 10, anchor=FRONT + LEFT + BOTTOM)
```

Forge is still in unstable-release development. Change 0022 deliberately picks
the simpler CENTER default instead of preserving the previous accidental
bottom-centred behaviour.

Other primitives keep their current constructor semantics in this change. They
can be normalised separately, with their own native and qualification contract.

## Native lowering

For the default CENTER datum Forge emits:

```text
solid.box(..., center=[0, 0, 0])
```

For another supported Box anchor Forge calculates the matching native
`corner=[...]` directly from the dimensions.

Feature-history and direct CSG use the same rule. A translated CSG Box adds the
translation to the selected native datum; Forge does not add a corrective move.

## `.at()` remains placement

Constructor `anchor=` chooses the unplaced Box datum. `.at(..., anchor=...)`
is later placement and may choose another Box anchor for that placement.

For example:

```python
Box(80, 50, 10).at(0, 0, 0, anchor=BOTTOM)
```

places the Box bottom-face centre at the requested point even though the
constructor default is CENTER.

## `taper()`

`Box.taper(from_z=..., inset=...)` is anchor-aware.

`from_z` is measured from the Box bottom face regardless of which constructor
anchor lies at model origin. The native section sketches are emitted at the
real bottom/start/top planes.

## Qualification

Change 0022 proves:

- ordinary `Box()` emits native `center=[0,0,0]`;
- `anchor=BOTTOM` and cardinal edge/corner anchors emit the correct native
  `corner=[...]`;
- feature-history and CSG use the same Box datum contract;
- a saved default Box remains centred after length/width/height parameter
  changes without rerunning Python;
- `Box.taper()` keeps the same taper intent for CENTER and BOTTOM;
- explicit `.at(..., anchor=...)` selects the requested placement datum;
- existing qualification fixtures that require a bottom datum say so explicitly;
- PythonSCAD, pyBOSL2 and CadQuery references describe the same centred Box;
- full Q1-Q6 qualification remains green.

## Exit condition

> One Box anchor has one meaning in every compiler path, and ordinary
> `Box(...)` is centred on the model origin.
