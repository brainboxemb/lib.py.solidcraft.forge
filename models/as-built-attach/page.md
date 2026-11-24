# As-built rigid relationship preserves pose

> Documentation provenance: historical Qualification case text from commit `6472c7ca02090d83a0fedc8ca18f947a3d3d56ca`; lowering wording updated during #559 for replay-bound occurrence IDs restored by change 0013 / #191.

**Legacy group:** `components`

**Saved-design required:** `false`

## Goal

Verify that attach(as_built=True) records a rigid native assembly relationship without re-positioning or re-orienting a child occurrence that already has an authored pose.

## Forge API

Marker(placement=Placement(x=50, y=20, z=15, rotation=(Z,90))).attach(base, as_built=True)

## Forge model

One Base and one non-square Marker occurrence. The Marker already owns a translation and rotation before the Attachment is added; the as-built relationship carries no parent/child anchor, offset, gap or angle.

## How Forge builds it in SolidCraft

Forge binds the real Base and Marker occurrence IDs returned by native component creation, applies the complete Marker pose through replay-bound occurrence.move, then emits joint.as_built(type='rigid') using those bound IDs. No predicted Component:N occurrence name and no anchor-origin solve is used.

## SolidCraft result

The Base remains centred at Z=0: [-20,-15,-5]..[20,15,5]. The 30x10 Marker remains quarter-turned to a 10x30 footprint at [45,5,11]..[55,35,19] after the native as-built joint is created.

## Saved-design test

Not required: an as-built relationship intentionally captures the current relative pose rather than defining a parameter-driven placement rule.

## Geometry evidence

> Geometry-rationale provenance: X/Y placement restored from `qualification/expectations.py` at commit `6472c7ca02090d83a0fedc8ca18f947a3d3d56ca`; Z bounds updated for the current `Box(..., anchor=Anchor.CENTER)` contract introduced by change 0022.

**Bounds sufficient:** `true`

The two disjoint rectangular body envelopes fully describe the baseline pose; command-contract verification separately proves that the native relationship is an as-built rigid joint rather than a repositioning attachment.

## Reference notes

- **SolidCraft** — The native as-built rigid relationship constrains two already-positioned occurrences without solving a new mating position.
- **PythonSCAD** — Independent geometry preserves the translated and rotated Marker pose without using Forge.
- **pyBOSL2** — Independent bottom-anchored geometry verifies the same world-space Marker envelope.
- **CadQuery** — Assembly Location independently represents the authored occurrence pose.
- **build123d** — Independent placed and rotated box geometry verifies the same visible baseline.
