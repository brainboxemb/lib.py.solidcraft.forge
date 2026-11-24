# Native circular feature pattern

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/solidcraft.py`](verification/solidcraft.py).

**Legacy group:** `features`

**Saved-design required:** `true`

## Goal

Qualify one real SolidCraft circular History pattern over an existing direct native Hole feature, rather than Forge-expanded repeated holes.

## Forge API

source = Hole(d=8, direction=(0, 0, -1)).at(pcd / 2, 0, 6); body = body + source; body.circular_pattern(source, count=bolts, axis=Axis.Z)

## Forge model

One 100 x 100 x 6 mm plate, one direct native Ø8 Hole source on a 60 mm pitch circle and one native six-instance circular feature pattern.

## How Forge builds it in SolidCraft

Forge emits one direct `solid.hole` source, resolves its native history identity as `Hole1`, then emits exactly one `solid.pattern.circular` with `features=['Hole1']`; `bolts` is a dimensionless native count parameter and `pcd` remains a millimetre parameter used by the source position.

## SolidCraft result

SolidCraft saves one plate with six through holes, one native HoleFeature named `Hole1`, and one native CircularPatternFeature that references that Hole feature.

## Saved-design test

Required because bolts is a saved native pattern-count parameter. Change bolts from 6 to 4 in the saved .sc design; the pattern must rebuild to four holes without rerunning Python while retaining one direct source Hole and one CircularPatternFeature.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `false`

The six bolt holes do not change the plate envelope. Volume, cylindrical-wall probes and native pattern-history checks are required.

## Reference notes

- **SolidCraft** — Native integration through saved-design checks prove one saved CircularPatternFeature and count mutation. The four comparison libraries independently prove the baseline six-hole geometry.
