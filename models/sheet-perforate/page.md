This verification covers a **native manufacturing perforation field**, not
ordinary B-rep hole cuts.

SolidCraft's `sheet.perforate` contract intentionally keeps the display B-rep
as one sheet while carrying perforations in flat-pattern, DXF and measured-volume
semantics. The ordinary 3D preview may therefore look like a solid plate and is
**not** the visual proof for this capability.

The native checks prove the saved design contains one `PerforateFeature` and
that `sheet.flat_pattern` reports 15 square-pattern perforations at Ø5 mm,
10 mm pitch and 5 mm margin.

The **manufacturing-flat-pattern** visual check exports the saved `.sc` through
native `sheet.export_dxf`. Actual is rendered from DXF `PERFORATION` circles;
Goal is the approved 5 × 3 field. The first Ø5 centre is at (-22.5, -12.5):
that leaves the declared 5 mm material clearance from the sheet edge to the
hole contour, after which centres repeat on the 10 mm square pitch. The check
fails if native manufacturing output loses holes, moves them, changes their
diameter or becomes a solid blank.

Forge deliberately does not replace this feature with repeated solid holes.
