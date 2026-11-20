# Eight vertical L-profiles: two per side corner

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `components`

**Saved-design required:** `true`

## Goal

Place two short vertical angle profiles on each rounded side corner, one at the bottom and one at the top. The assembly calculates all eight poses directly from frame dimensions.

## Forge API

LProfile.copy(placement=Placement(x=..., y=..., z=..., rotation=(Z, ...)))

## Forge model

One rounded parametric FrameBlock plus eight occurrences of one neutral LProfile definition. Position and clocking belong to the assembly; there is no Attachment.

## How Forge builds it in SolidCraft

Forge binds the occurrence ids returned by component.create/occurrence.copy to replay variables. Numeric unrotated copies use occurrence.copy translate directly; symbolic positions and rotations use a later occurrence.move addressed by the bound id.

## SolidCraft result

Each rounded vertical side corner carries exactly two outside angle profiles. On the 60 mm frame they occupy Z=0..16 and Z=44..60.

## Saved-design test

Change frame_width/depth/height from 120x80x60 to 160x120x90 mm; all four corner pairs follow the calculated X/Y positions and each upper member moves to Z=74..90.

## Reference notes

- **SolidCraft** — component.create/occurrence.copy return real occurrence ids; the replay executor binds those ids before later parametric occurrence.move commands.
- **BOSL2** — One neutral component is repeated by assembly-owned placement.
