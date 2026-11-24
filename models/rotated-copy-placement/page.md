# Copied Placement with rotation

> Documentation provenance: historical Qualification case text from commit `6472c7ca02090d83a0fedc8ca18f947a3d3d56ca`; lowering wording updated during #559 for replay-bound occurrence IDs restored by change 0013 / #191.

**Legacy group:** `components`

**Saved-design required:** `false`

## Goal

Verify that a copied occurrence combining concrete XYZ and orientation keeps its declared parent-frame position instead of rotating a pre-applied copy translation.

## Forge API

left = Panel(placement=Placement(x=-40, rotation=(Z, 90))); right = left.copy(placement=Placement(x=40, rotation=(Z, 90)))

## Forge model

Two occurrences share one non-square Panel definition. Each carries one complete absolute Placement with X translation and Z-axis orientation.

## How Forge builds it in SolidCraft

Forge creates/copies the Panel occurrence at native identity, binds each real occurrence ID, then applies each complete translation and Z=90 degree orientation through occurrence.move. No predicted Component:N name and no pre-rotated copy translation is used.

## SolidCraft result

Two rotated 10 x 20 x 4 mm envelopes remain centred at X=-40 and X=+40. No placement joint is created.

## Saved-design test

Not required: this case isolates concrete copy-plus-rotation lowering; parameter-driven occurrence recompute is proved by the dedicated parametric Placement cases.

## Geometry evidence

> Geometry-rationale provenance: X/Y placement restored from `qualification/expectations.py` at commit `6472c7ca02090d83a0fedc8ca18f947a3d3d56ca`; Z bounds updated for the current `Box(..., anchor=Anchor.CENTER)` contract introduced by change 0022.

**Bounds sufficient:** `true`

The centred non-square 10 x 20 world envelopes prove that both Panel occurrences are rotated while their X centers remain at the authored -40/+40 positions.

## Reference notes

- **SolidCraft** — Translation and rotation are applied together to each bound occurrence through occurrence.move.
- **PythonSCAD** — Independent geometry proves two 10 x 20 x 4 rotated envelopes at the expected centers.
- **pyBOSL2** — Independent geometry checks the same rotated world envelopes.
- **CadQuery** — Independent Assembly Locations apply the same placement and orientation.
- **build123d** — Independent Rot and Locations reproduce the two placed panels.
