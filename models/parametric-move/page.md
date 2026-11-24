# Native parametric occurrence Placement

> Documentation provenance: historical Qualification case text from commit `6472c7ca02090d83a0fedc8ca18f947a3d3d56ca`; lowering wording updated during #559 for replay-bound occurrence IDs restored by change 0013 / #191.

**Legacy group:** `components`

**Saved-design required:** `true`

## Goal

Verify that placing one reusable occurrence with a parent parameter is ordinary CAD placement, not an implicit assembly joint.

## Forge API

Block(); Block(placement=Placement(x=self.offset))

## Forge model

Two occurrences share one Block definition. The first remains at the component origin; the second carries an absolute symbolic X Placement.

## How Forge builds it in SolidCraft

Forge publishes offset, creates one reusable Block definition, binds the real copied occurrence ID, then emits occurrence.move with translate=['offset', 0, 0]. No predicted occurrence name and no joint.create is used for ordinary placement.

## SolidCraft result

Two 20 x 20 x 10 mm blocks sit at X=0 and X=40 mm. SolidCraft stores the second occurrence as an expressed move and no assembly joint is required.

## Saved-design test

Change offset from 40 to 70 mm in the saved design; without rerunning Python the second occurrence must move another 30 mm while the first remains fixed.

## Geometry evidence

> Geometry-rationale provenance: X/Y placement and mutation values restored from `qualification/expectations.py` at commit `6472c7ca02090d83a0fedc8ca18f947a3d3d56ca`; Z bounds updated for the current `Box(..., anchor=Anchor.CENTER)` contract introduced by change 0022.

**Bounds sufficient:** `true`

The two centred rectangular body envelopes uniquely describe the baseline and mutated X placements. Saved-design recompute separately proves the symbolic placement remains associative.

## Reference notes

- **SolidCraft** — occurrence.move keeps the length expression as a native expressed move that follows parameter changes.
- **CadQuery** — Assembly child Location is an independent occurrence placement concept, separate from assembly constraints.
- **PythonSCAD** — A translate() is placement rather than a mating relationship.
- **pyBOSL2** — Independent translated block geometry verifies the baseline placement.
- **build123d** — Independent Locations verify the same baseline occurrence positions.
