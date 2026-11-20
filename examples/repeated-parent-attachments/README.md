# Attachments on repeated parent occurrences

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `associativity`

**Saved-design required:** `true`

## Goal

Verify two disconnected rigid-joint graphs when two occurrences of one shared parent definition each own one attached child.

## Forge API

right = left.copy(placement=Placement(x=60)); marker_a = Marker().attach(left, parent=Anchor.TOP, child=Anchor.BOTTOM); marker_b = marker_a.copy().attach(right, parent=Anchor.TOP, child=Anchor.BOTTOM)

## Forge model

Two Parent occurrences share one definition and one parent_height dependency. Two Marker occurrences share one definition. Each Marker has exactly one rigid Attachment to a different Parent occurrence.

## How Forge builds it in SolidCraft

Forge creates one Parent definition plus one translated copy and one Marker definition plus one copy. Each Marker receives its symbolic computed seed Placement through a replay-bound occurrence.move, followed by exactly one authored rigid joint.create to its replay-bound Parent occurrence. No generated placement joint is allowed.

## SolidCraft result

Both markers sit on their own parent TOP face. After parent_height changes in the saved design, both disconnected joint graphs must rebuild so both markers follow the changed top faces.

## Saved-design test

Change parent_height from 40 to 60 mm in the saved .sc design; both Parent occurrences become 60 mm tall and both Marker occurrences move from Z=40..50 to Z=60..70 without rerunning Python.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `true`

Four rectangular body bounds expose both parent heights and both child positions. saved-design mutation separately proves that both disconnected native joint graphs follow the shared parent-height change.

## Reference notes

- **SolidCraft** — This case isolates the 0.42 joint-solver behaviour for two disconnected graphs that share reusable component definitions.
- **BOSL2** — Two independent TOP-to-BOTTOM attachments express the same parent/child intent without SolidCraft-specific replay identity.
