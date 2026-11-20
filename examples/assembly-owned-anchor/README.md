# Assembly-owned named anchor

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `anchors`

**Saved-design required:** `true`

## Goal

Verify that an assembly can publish a semantic attachment name without putting that application-specific datum on the reusable component, and that a consumer of the name still lowers to an associative native relationship.

## Forge API

(base + companion).with_anchor('inspection_corner', base, Anchor.FRONT_TOP_RIGHT); datum = frame.anchor('inspection_corner'); Marker().attach(datum.target, parent=datum.reference, ...)

## Forge model

The assembly stores a name mapped to an existing target occurrence plus a normal Forge anchor reference. The reusable Base knows nothing about the semantic name.

## How Forge builds it in SolidCraft

with_anchor()/anchor() are Forge-side semantic indirection only. The resulting native joint is the same topology-backed FRONT_TOP_RIGHT relationship that a direct attach would emit; no extra native helper object is required.

## SolidCraft result

The marker sits on the base front-top-right corner while an unrelated companion occurrence remains part of the same assembly.

## Saved-design test

Change base_width/base_height from 40x20 to 80x40 mm in the saved .sc design; the marker created through the assembly-owned name must follow the moved corner without rerunning Python.

## Reference notes

- **BOSL2** — Semantic attachment names belong naturally to the assembly that owns their meaning rather than to a generic reusable component.
- **SolidCraft** — The semantic name disappears during lowering; the persisted native relationship remains topology-backed and associative.
