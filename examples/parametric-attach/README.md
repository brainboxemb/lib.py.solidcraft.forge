# Editable distance between attached components

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `associativity`

**Saved-design required:** `true`

## Goal

Verify that distance along the attachment normal remains a native editable joint parameter.

## Forge API

attach(..., gap=self.gap)

## Forge model

Rigid Attachment with a symbolic gap expression; anchor identities are unchanged.

## How Forge builds it in SolidCraft

The child receives a symbolic seed pose so a floating graph starts at the authored mating position; joint.create(type='rigid', offset='gap') remains the relationship and the gap remains a native expression in both places rather than a flattened number.

## SolidCraft result

The child sits 10 mm away from the parent's RIGHT face along the joint normal.

## Saved-design test

Change gap from 10 to 30 mm in the saved .sc design; the child must move another 20 mm without rerunning Python.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `true`

The two rectangular body bounds describe the baseline gap geometry. Saved joint recompute is proved separately by saved-design.

## Reference notes

- **BOSL2** — Conceptually similar to an attachment displacement along the local anchor normal rather than a world-axis translate.
