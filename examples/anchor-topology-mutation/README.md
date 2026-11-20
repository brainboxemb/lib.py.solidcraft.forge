# Explicit topology pick follows parent resize

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `anchors`

**Saved-design required:** `true`

## Goal

Verify the AnchorTopology contract directly: Forge supplies fixed baseline edge/face/corner pick coordinates once, then native SolidCraft must retain that selected topology when the parent dimensions change.

## Forge API

anchors() -> AnchorTopology(edge=..., on=..., corner=..., z=..., x=...); attach(parent='front_top_left_pick', child=AnchorFrame())

## Forge model

One parametric Board, one named topology anchor with deliberately fixed numeric pick points, and one centered Marker attached to that anchor.

## How Forge builds it in SolidCraft

AnchorTopology is inlined into joint.create as edge/on/corner plus optional z/x. No persistent joint.origin and no Forge-side recomputation of the pick coordinates occurs after the saved design is mutated.

## SolidCraft result

On the 40x20x20 board the marker is centered on the front-top-left corner selected by the explicit topology pick.

## Saved-design test

Change base_width/base_height from 40x20 to 80x40 mm in the saved .sc design; the unchanged native relationship must move the marker to the new front-top-left corner without rerunning Python.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `true`

The board and marker positions describe the visible result. After resizing the saved model, the marker must still follow the same selected edge and corner.

## Reference notes

- **SolidCraft** — This is a direct test of native topology persistence: the initial pick identifies topology, while later parameter changes move that topology.
- **BOSL2** — The higher-level intent is still a semantic attachment point, but this fixture specifically qualifies Forge's lower-level explicit topology reference.
