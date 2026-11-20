# Native attachment clocking angle

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `associativity`

## Goal

Verify that attach(angle=...) remains a native rigid-joint turn rather than being pre-baked into child geometry or an occurrence rotation.

## Forge API

Arm().attach(base, parent=Anchor.TOP, child=Anchor.BOTTOM, angle=90)

## Forge model

One square Base and one non-square 30x10 Arm. The child definition stays neutral; only the attachment carries the quarter-turn.

## How Forge builds it in SolidCraft

joint.create(type='rigid', angle=90) is the only authored clocking relationship. Forge does not rotate the Arm occurrence separately.

## SolidCraft result

The Arm sits on the Base TOP face and its 30x10 footprint is quarter-turned to 10x30 in world XY.

## Saved-design test

Not required; this case isolates native orientation/clocking and is qualified by measured bounds plus fixed-camera visual regression.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `true`

The non-square arm size shows whether the quarter-turn is correct. The saved SolidCraft model is also checked for the expected joint angle.

## Reference notes

- **SolidCraft** — The joint angle is the persisted native relationship value that clocks the child about the attachment normal.
- **BOSL2** — Conceptually comparable to spin/clocking around an attachment normal, while the child geometry remains reusable and neutral.
