# Native sketch Slot family

> Documentation provenance: the original case description traces to the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. The SolidCraft 0.45 parametric additions in this revision are derived from the canonical runtime registry in [`docs/reference/solidcraft/0.45.0/`](../../docs/reference/solidcraft/0.45.0/) and are proven by [`verification/solidcraft.py`](verification/solidcraft.py) plus the saved-design mutation [`verification/change_size.json`](verification/change_size.json).

**Legacy group:** `features`

**Saved-design required:** `true`

## Goal

Qualify all five SolidCraft 0.45 Slot construction methods as direct Forge
sketch profiles, and prove the native parametric contracts that Forge exposes.

The three straight Slot variants keep axis-aligned length and position editable.
All five Slot variants keep width editable. Forge must not approximate any Slot
with rounded rectangles or hand-built curves.

## Forge API

```python
SlotCenterToCenter2D(...)
SlotOverall2D(...)
SlotCenterPoint2D(...)
SlotArcThreePoint2D(...)
SlotArcCenter2D(...)
```

inside one explicit `Sketch`.

## Forge model

One 160 × 120 × 5 mm plate contains five Slot profiles in one named sketch.

Baseline geometry intentionally matches the historical qualification:

- width: 8 mm;
- straight-Slot Y: -35 mm;
- centre-to-centre Slot centres: X=-60 .. -40;
- overall Slot endpoints: X=-10 .. 20;
- centre-point Slot: centre X=55, end-centre X=65;
- both arc Slot paths retain fixed authored points.

The lower-case straight-Slot coordinates and `slot_width` are normal editable
Forge model parameters.

## How Forge builds it in SolidCraft

Fixed authored Slot points still use the direct native `sketch.slot.*` creator.

For the three straight Slots, symbolic authored endpoints are evaluated only for
numeric seed geometry. Forge then uses native `sketch.draw.dimensioned` with
the SolidCraft 0.45 `length` role, constrains the returned native
`centre_line` horizontal/vertical and dimensions the returned native
`middle` point from the sketch origin.

The direct Slot point fields therefore remain numeric while native SolidCraft
dimensions retain the editable length and position expressions.

The two arc Slots keep fixed authored points but share the same editable native
width expression.

## SolidCraft result

SolidCraft saves:

- one plate body;
- one solved `Slot family` sketch with five closed native Slot profiles;
- one error-free through-cut extrusion.

The native timeline must not contain `sketch.rectangle.rounded` as a Slot
substitute.

## Saved-design test

Without rerunning Forge Python, change the saved SolidCraft parameters:

- `slot_width`: 8 -> 10 mm;
- `straight_y`: -35 -> -20 mm;
- centre-to-centre end X: -40 -> -35 mm;
- overall end X: 20 -> 25 mm;
- centre-point end X: 65 -> 70 mm.

The saved design must rebuild solved native Slot geometry with the new width,
straight lengths and position. The body envelope stays the same while the
through-cut volume changes deterministically.

## Geometry evidence

> Geometry-rationale provenance: the unchanged baseline envelope/volume contract descends from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`; the new mutated-volume expectation is derived directly from the five native Slot dimensions declared in this case.

**Bounds sufficient:** `false`

The five Slot cuts do not change the plate envelope. Baseline volume and 3D
slot-wall probes remain required. The saved-design mutation additionally checks
the mutated parameter values, solved sketch state and resulting body volume.

## Reference notes

- **SolidCraft** — the canonical command/reference baseline is SolidCraft 0.45.0
  from immutable runtime v0.3.4. Straight Slot roles are `length` and
  `width`; direct authored Slot point fields remain numeric.
- **Independent references** — baseline geometry remains unchanged, so the
  existing PythonSCAD, pyBOSL2, CadQuery and build123d reference geometry stays
  valid for Q3/Q6 baseline comparison.
