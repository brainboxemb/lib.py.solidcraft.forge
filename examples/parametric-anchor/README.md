# Face anchor follows parent geometry

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `anchors`

**Saved-design required:** `true`

## Goal

Verify that a standard face anchor remains tied to changing parent topology.

## Forge API

Anchor.RIGHT / Anchor.LEFT with parent parameter propagation

## Forge model

The attachment references the parent's semantic RIGHT face, not a frozen absolute X coordinate.

## How Forge builds it in SolidCraft

joint.create uses a native face reference derived from the parent occurrence; the parent width remains a SolidCraft parameter.

## SolidCraft result

The attached block stays on the parent's right face.

## Saved-design test

Change base_width from 40 to 80 mm in the saved design; the block follows the moved RIGHT face.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `true`

The two body sizes and positions show the initial face-relative placement. The saved SolidCraft model is then changed to confirm that the same anchor is still used.

## Reference notes

- **BOSL2** — BOSL2 cardinal anchors similarly express a meaningful side of the parent instead of an absolute coordinate.
