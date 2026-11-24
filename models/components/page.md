# Reuse one component definition in two placements

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/solidcraft.py`](verification/solidcraft.py).

**Legacy group:** `components`

## Goal

Verify that one reusable component definition can have two occurrences with ordinary Placement and no attachment relationship.

## Forge API

left = Block(); right = left.copy(placement=Placement(x=Block.length))

## Forge model

Two ModelInstance occurrences share one ModelDefinition. The second occurrence carries only Placement metadata; neither occurrence carries an Attachment.

## How Forge builds it in SolidCraft

Forge creates one Block component definition and one occurrence.copy with translate=[40,0,0]. No joint.create and no later occurrence.move are needed.

## SolidCraft result

Two identical blocks touch face-to-face at X=20 while retaining one shared editable component definition.

## Saved-design test

No mutation in this base case; parameter-driven Placement is qualified separately.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `true`

The two body sizes and positions describe the visible result. The saved SolidCraft model is checked separately to confirm that both occurrences reuse one component definition.

## Reference notes

- **SolidCraft** — One component definition may be placed more than once; this case qualifies that basic component/occurrence structure without introducing a joint.
