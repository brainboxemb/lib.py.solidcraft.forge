# Editable local offset at an attachment

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `associativity`

**Saved-design required:** `true`

## Goal

Verify the existing local (u,v) attachment-plane offset and make its coordinate semantics explicit.

## Forge API

attach(..., offset=(u, v))

## Forge model

Attachment stores two symbolic local planar values; these are not world X/Y/Z coordinates.

## How Forge builds it in SolidCraft

The computed child seed pose retains the symbolic local offset, then the actual relationship is joint.create(type='planar', values=[u,v,angle]). The seed move is not an additional joint.

## SolidCraft result

The marker moves within the selected corner anchor's local attachment plane.

## Saved-design test

Change shift from 5 to 10 mm in the saved design; the marker must follow the same local axis by another 5 mm.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `true`

The base and marker sizes and positions show the local offset. The saved SolidCraft model is then changed to confirm that the planar joint updates correctly.

## Reference notes

- **BOSL2** — Important reference: attach() operates in the local coordinate system at the parent anchor, not blindly in world coordinates.
- **OpenSCAD** — A raw translate([x,y,z]) is world/object transform syntax and therefore is not equivalent to this local joint offset.
