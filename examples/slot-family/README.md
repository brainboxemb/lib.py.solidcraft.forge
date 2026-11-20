# Native sketch Slot family

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `features`

## Goal

Qualify all five SolidCraft 0.42 Slot construction methods as direct SCPF sketch profiles rather than approximating them with rounded rectangles or hand-built curves.

## Forge API

SlotCenterToCenter2D(...); SlotOverall2D(...); SlotCenterPoint2D(...); SlotArcThreePoint2D(...); SlotArcCenter2D(...) inside one explicit Sketch

## Forge model

One 160 x 120 x 5 mm plate with five separate closed Slot profiles in one named sketch, removed with one through-all cut.

## How Forge builds it in SolidCraft

Each public constructor emits exactly its matching sketch.slot.* command; the sketch is finished once and one native cut extrusion removes all five profiles.

## SolidCraft result

SolidCraft saves one plate, one Slot family sketch containing five closed profiles and one error-free cut extrusion. The native timeline must not contain sketch.rectangle.rounded as a substitute for Slot construction.

## Saved-design test

No saved-design mutation is required; this case isolates the five native sketch construction methods and their saved feature history.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `false`

The five slot cuts do not change the plate envelope. Volume and 3D slot-wall probes are required.

## Reference notes

- **SolidCraft** — Native integration through geometry checks additionally prove the five sketch.slot.* command identities. The four comparison libraries independently prove the resulting five cut shapes.
