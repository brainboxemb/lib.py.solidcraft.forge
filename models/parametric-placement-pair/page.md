# Symmetric parametric occurrence Placement

> Documentation provenance: historical Qualification case text from commit `6472c7ca02090d83a0fedc8ca18f947a3d3d56ca`; lowering wording updated during #559 for replay-bound occurrence IDs restored by change 0013 / #191.

**Legacy group:** `components`

**Saved-design required:** `true`

## Goal

Verify the WoodFrame-style dependency shape: two occurrences of one reusable definition are placed symmetrically from one parent spacing parameter.

## Forge API

left = Block(placement=Placement(x=-half(self.spacing))); right = left.copy(placement=Placement(x=half(self.spacing)))

## Forge model

Two occurrences share one Block definition. Their absolute X placements are the negative and positive halves of the same parent parameter.

## How Forge builds it in SolidCraft

Forge publishes spacing, creates one Block definition, binds both real occurrence IDs, and emits two occurrence.move expressions using -(spacing / 2) and spacing / 2. No predicted occurrence name and no placement joint is used.

## SolidCraft result

With spacing=80 mm the two 20 mm blocks are centred at X=-40 and X=+40.

## Saved-design test

Change spacing from 80 to 120 mm in the saved design; without rerunning Python the two centres must move symmetrically to X=-60 and X=+60.

## Geometry evidence

> Geometry-rationale provenance: X/Y placement and mutation values restored from `qualification/expectations.py` at commit `6472c7ca02090d83a0fedc8ca18f947a3d3d56ca`; Z bounds updated for the current `Box(..., anchor=Anchor.CENTER)` contract introduced by change 0022.

**Bounds sufficient:** `true`

The two centred disjoint Block envelopes prove the symmetric baseline and mutation positions. Saved-design recompute proves both native placement expressions remain tied to the same spacing parameter.

## Reference notes

- **SolidCraft** — Both occurrence translations remain parameter-referencing expressed moves in the saved design.
- **CadQuery** — Independent Assembly Locations provide a comparison for symmetric occurrence placement without constraints.
- **PythonSCAD** — Symmetric translate(-spacing/2) and translate(spacing/2) express the same visible intent.
- **pyBOSL2** — Independent translated blocks verify the baseline symmetric geometry.
- **build123d** — Independent Locations verify the two baseline centers.
