# Native rectangular feature pattern

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `features`

**Saved-design required:** `true`

## Goal

Qualify a real SolidCraft rectangular History pattern over one existing cut feature, rather than Forge-expanded repeated geometry.

## Forge API

source = slot.extrude(-4); body = body - source; body.rectangular_pattern(source, count=columns, spacing=pitch, direction=Axis.X, count2=rows, spacing2=row_pitch, direction2=Axis.Y)

## Forge model

One 120 x 80 x 4 mm plate, one native straight Slot cut and one native 3 x 2 rectangular feature pattern.

## How Forge builds it in SolidCraft

Forge emits the source Sketch/cut once, then exactly one solid.pattern.rectangular with features=['Slot']; columns/rows are dimensionless native parameters and pitches remain millimetre parameters.

## SolidCraft result

SolidCraft saves one plate with six slot cuts and one native rectangular pattern History feature that references the original Slot cut.

## Saved-design test

Required because columns and pitch are saved native pattern parameters. Change columns from 3 to 2 and pitch from 24 to 30 mm in the saved .sc design; the pattern must rebuild to a 2 x 2 layout without rerunning Python while retaining one source Slot cut and one RectangularPatternFeature.

## Reference notes

- **SolidCraft** — Native integration through geometry checks additionally prove one saved RectangularPatternFeature. The four comparison libraries independently prove the final 3 x 2 slot geometry.
