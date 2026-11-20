# Associative sketch pattern and mirror

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `associativity`

**Saved-design required:** `true`

## Goal

Verify that one Circle seed and one Slot seed drive repeated sketch geometry through native SolidCraft rectangular patterns and mirrors instead of Python-expanded copies.

## Forge API

seed = sketch.add(Circle2D(...)); sketch.rectangular_pattern(seed, ...); sketch.mirror(pattern, axis=Axis.X/Y); same flow for SlotCenterToCenter2D

## Forge model

One 240 x 160 x 5 mm plate with two attached Sketches. Dog holes use one Circle seed, one native sketch pattern and one mirror. Clamp slots use one Slot seed, one native sketch pattern and three mirrors. Each Sketch is cut once.

## How Forge builds it in SolidCraft

Forge binds the real native curves returned by the seed profile, feeds those ids into sketch.pattern.rectangular, binds the pattern curves, and feeds those into sketch.mirror. User Python never contains SolidCraft-generated ids.

## SolidCraft result

SolidCraft saves one Dog holes Sketch and one Clamp slots Sketch with associative pattern/mirror relationships. Baseline geometry contains 8 Ø8 holes and 8 straight Slots. No expanded set of independent seed commands is emitted.

## Saved-design test

Change hole_diameter 8->10 mm, hole_pitch 25->30 mm and slot_pitch 50->30 mm in the saved .sc design. Without rerunning Python all existing pattern and mirror copies must follow the changed seed and spacing. Pattern counts remain native editable parameters, but SolidCraft 0.42 mirrors a fixed selected entity set and does not automatically adopt new entities added later by an upstream count change.

## Reference notes

- **SolidCraft** — The native saved design is the source of truth for the associative sketch pattern/mirror relationships and their saved-design mutation.
- **PythonSCAD** — Independent final geometry confirms the repeated cuts without relying on Forge's command lowering.
- **CadQuery** — Independent final geometry confirms the expected hole and Slot positions.
- **build123d** — Independent final geometry confirms the expected profile repetition and cut result.
