# Four centred vertical L-profiles

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Legacy group:** `components`

**Saved-design required:** `true`

## Goal

Place one short vertical angle profile around each of the four rounded side corners of a rectangular frame. The assembly calculates each occurrence pose directly from frame dimensions.

## Forge API

LProfile.copy(placement=Placement(x=..., y=..., z=..., rotation=(Z, ...)))

## Forge model

One rounded parametric FrameBlock plus four occurrences of one neutral vertical LProfile definition. Position and clocking belong to the assembly; there is no Attachment.

## How Forge builds it in SolidCraft

Forge binds the occurrence ids returned by component.create/occurrence.copy to replay variables. Numeric unrotated copies use occurrence.copy translate directly; symbolic positions and rotations use a later occurrence.move addressed by the bound id.

## SolidCraft result

One vertical angle profile wraps each front-left, front-right, rear-right and rear-left rounded side corner. All four occupy Z=22..38 on the 60 mm frame.

## Saved-design test

Change frame_width/depth from 120x80 to 160x120 mm in the saved .sc design; all four profiles follow the calculated corner positions while remaining centred at the same frame height.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `true`

This case adds placement of four already-qualified L-profile components around the frame. The component profile itself is qualified by the bracket case; these bounds describe this case's additional geometry.

## Reference notes

- **SolidCraft** — component.create/occurrence.copy return real occurrence ids; the replay executor binds those ids before later parametric occurrence.move commands.
- **BOSL2** — The neutral angle profile is reused while the assembly owns position and orientation.
