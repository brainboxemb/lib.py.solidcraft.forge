# Change 0022 — Native Box origin selection

**Status:** design and implementation  
**SolidCraft target:** 0.42.0

## Problem

Forge currently gives one `Box()` two different native meanings.

The feature-history Box compiler emits:

```text
solid.box(..., corner=[-length / 2, -width / 2, 0])
```

so the box is centred in X/Y and its bottom face is at Z=0.

The direct CSG compiler emits:

```text
solid.box(..., center=[0, 0, 0])
```

for the same unplaced `Box()`, so the box is centred in X/Y/Z.

This also makes Box CENTER alignment ambiguous because Forge cannot know which
primitive datum the model intended.

SolidCraft 0.42 already provides the correct native distinction: `solid.box`
accepts either `corner=[x,y,z]` or `center=[x,y,z]`. A center-authored box
keeps that centre when dimensions change; a corner-authored box keeps its
corner datum.

## Public API

`Box` becomes:

```python
Box(length, width, thickness, *, origin=Anchor.BOTTOM)
```

`origin` means: **which Box anchor is located at model coordinate
`(0, 0, 0)` before any later placement**.

The default remains `Anchor.BOTTOM` and therefore preserves the established
Forge behaviour:

- X/Y centred on zero;
- bottom face at Z=0;
- thickness extends towards +Z.

Examples:

```python
Box(80, 50, 10)                         # bottom-centred, existing default
Box(80, 50, 10, origin=CENTER)          # fully XYZ-centred
Box(80, 50, 10, origin=FRONT + BOTTOM) # front/bottom edge centred on X
```

The existing cardinal selector vocabulary is reused. No separate Box-origin
enum is introduced.

## Native lowering

When `origin=CENTER`, Forge emits native:

```text
solid.box(..., center=[0, 0, 0])
```

When another supported cardinal origin is selected, Forge emits native
`corner=[...]` calculated from that anchor. The corner remains expressed in
terms of symbolic Box dimensions where needed.

A translated CSG Box uses the same rule with the translated point as the
selected origin point. Feature-history and direct-CSG lowering must therefore
describe the same Box geometry.

## `.at()` remains placement

```python
Box(..., origin=CENTER).at(x, y, z, anchor=FRONT + BOTTOM)
```

means that the explicit `.at()` placement puts `FRONT + BOTTOM` at the
requested point. The constructor origin no longer matters after that explicit
placement.

This keeps constructor origin and later placement as separate concepts.

## CENTER alignment

Forge's internal Box centre is derived from its selected origin.

For the default BOTTOM origin, the geometric centre is:

```text
(0, 0, thickness / 2)
```

For `origin=CENTER`, the geometric centre is:

```text
(0, 0, 0)
```

This makes `shape.at(other_shape)` CENTER-to-CENTER alignment consistent with
the native Box datum.

## Taper limit

`Box.taper()` currently assumes a front plane at Z=0 and a rear plane at
Z=depth. Change 0022 keeps that API unchanged and therefore accepts only the
default BOTTOM Box origin.

Calling `taper()` on another Box origin fails early with a clear error. Full
origin-aware tapered-box semantics are separate work.

## CSG migration

Existing CSG fixtures that intentionally use a fully centred Box must say so:

```python
Box(..., origin=CENTER)
```

This is a semantic clarification, not a corrective translation.

## Qualification

Add a `centered-box` case with PythonSCAD, pyBOSL2 and CadQuery references.

Required evidence:

- ordinary `Box()` still emits the existing bottom-centred native corner;
- `Box(..., origin=CENTER)` emits native `solid.box center=[0,0,0]`;
- direct CSG lowering uses the same origin contract;
- a saved centered-box design remains centred after length/width/height
  parameter changes;
- Box CENTER alignment uses the real geometric centre for both BOTTOM and
  CENTER origins;
- explicit `.at(..., anchor=...)` overrides constructor origin placement;
- non-default-origin `taper()` fails before lowering;
- full Q1-Q6 qualification remains green.

## Exit condition

> One Box origin has one meaning in both feature-history and CSG compilation,
> and fully centred Box intent lowers directly to SolidCraft's native
> `center` datum.
