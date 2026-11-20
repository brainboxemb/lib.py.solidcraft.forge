# Topology-backed corner anchor

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `anchors`

**Saved-design required:** `true`

## Goal

Verify a corner reference that follows both parent width and height changes.

## Forge API

Anchor.FRONT_TOP_RIGHT paired with child Anchor.BACK_TOP_RIGHT

## Forge model

A standard corner Anchor is resolved to an edge/on/corner native topology reference rather than a free point.

## How Forge builds it in SolidCraft

joint.create receives SolidCraft edge/on/corner picks so the saved design can re-find the corner after geometry changes.

## SolidCraft result

The marker sits on the front-top-right corner of the base.

## Saved-design test

Change the base from 40x20 to 80x40 mm; the marker must follow both the new right side and new top.

## Reference notes

- **BOSL2** — BOSL2 supports side/edge/corner anchors; its anchor also carries orientation, which is a useful design reference for Forge.
