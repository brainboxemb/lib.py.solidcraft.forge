# Selective Sketch profile extrusion

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `associativity`

**Saved-design required:** `true`

## Goal

Verify that one associative Sketch pattern can keep all generated profiles while one native extrusion selects only the intended closed regions by sketch-local points.

## Forge API

sketch.rectangular_pattern(...); sketch.extrude(Depth.THROUGH_ALL, profiles=[(x, y), ...], exact_regions=True)

## Forge model

One 120 x 60 x 5 mm plate, one Circle seed, one native four-instance sketch pattern and one through-all cut selecting three of the four circle profiles.

## How Forge builds it in SolidCraft

Forge emits the Circle and native sketch pattern once, then passes three fixed point selections directly to solid.extrude profiles with exact_regions=true. No profile indices, generated curve ids or deleted pattern copies appear in user Python.

## SolidCraft result

SolidCraft saves one Selected holes Sketch containing the associative four-circle pattern and one cut ExtrudeFeature that removes exactly three profiles while leaving the fourth region uncut.

## Saved-design test

Change hole_diameter 8->10 mm and hole_pitch 20->24 mm in the saved .sc design. Without rerunning Python the three selected cuts must follow their associated pattern profiles, including profiles whose centres move away from the original pick points; the unselected profile remains uncut.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `false`

The selected cuts do not change the plate envelope. Volume, cylindrical wall probes and saved-design mutation are required to prove that exactly the chosen patterned profiles are cut.

## Reference notes

- **SolidCraft** — Native saved-design proves that saved point-based profile selections remain attached to the intended profile curves after pattern spacing and diameter changes.
- **PythonSCAD** — Independent final geometry confirms the baseline three-hole result without using Forge's profile-selection lowering.
- **CadQuery** — Independent final geometry confirms that only three of the four possible patterned positions are cut.
- **build123d** — Independent final geometry confirms the selected-hole plate.
