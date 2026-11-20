# TOP Sketch on circular body

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `fundamentals`

## Goal

Verify that a TOP-attached explicit Sketch can select the largest +Z planar face of a circular extrusion without rectangular-body metadata.

## Forge API

disc = Sketch(... Circle2D ...).extrude(10); with Sketch(on=disc, parent=Anchor.TOP): Circle2D(d=44); body + hub.extrude(16)

## Forge model

One Ø100 x 10 mm circular base plus one Ø44 x 16 mm hub joined from the selected top face.

## How Forge builds it in SolidCraft

Forge emits the circular base extrusion, model.faces with plane_normal=[0,0,1] and max=area, then a face-attached Hub Sketch and join extrusion. No rectangular base lookup is required.

## SolidCraft result

One stepped cylindrical body spans Z=0..26 mm. Disc and Hub remain two solved native Sketch/Extrude feature pairs and the Hub is attached to the actual top face of the Disc.

## Saved-design test

No saved-design mutation; this fixture isolates support-face lookup on a non-rectangular feature body.

## Reference notes

- **SolidCraft** — Native geometry proves the face-attached Hub Sketch builds on the circular Disc and stays solved.
- **PythonSCAD** — Independent CSG reference proves the stepped-cylinder geometry.
- **CadQuery** — Independent union reference proves the same two-radius stepped body.
- **build123d** — Independent builder reference proves the same baseline geometry.
