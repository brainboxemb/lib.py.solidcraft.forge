# Eight flightcase corner protectors

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `components`

**Saved-design required:** `true`

## Goal

Reuse one neutral three-plate corner protector on all eight case corners. The assembly calculates each XYZ position and 3D orientation directly from case dimensions.

## Forge API

FlightcaseCorner.copy(placement=Placement(x=..., y=..., z=..., rotation=(axis, angle)))

## Forge model

One rounded CaseBlock plus eight occurrences of one neutral trihedral protector. Position and orientation belong to the assembly; there is no Attachment.

## How Forge builds it in SolidCraft

Forge binds the occurrence ids returned by component.create/occurrence.copy to replay variables. Numeric unrotated copies use occurrence.copy translate directly; symbolic positions and rotations use a later occurrence.move addressed by the bound id.

## SolidCraft result

Each of the eight case corners is wrapped by three connected plates: one horizontal and two vertical. The protector outer envelope is a fixed 24x24x24 mm at every corner.

## Saved-design test

Change case_width/depth/height from 120x80x60 to 160x120x90 mm; all protectors follow the calculated corner positions without rerunning Python, while every protector remains exactly 24x24x24 mm.

## Reference notes

- **SolidCraft** — component.create/occurrence.copy return real occurrence ids; the replay executor binds those ids before later parametric occurrence.move commands.
- **BOSL2** — One neutral trihedral part is reused in eight assembly-owned poses.
