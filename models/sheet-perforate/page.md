# Native whole-sheet perforation

**Group:** `sheet-metal`
**Saved-design required:** `true`

> Documentation provenance: Forge #779 publishes the native SolidCraft 0.45 whole-sheet perforation capability as public Verification.

## Goal

Prove that Forge can author manufacturing perforations as native SolidCraft sheet history instead of approximating them with repeated B-rep holes.

## Forge API

`Shape.perforate(diameter=..., pitch=..., margin=..., pattern=...)` applies a whole-sheet field to existing sheet material.

## Forge model

A 60 × 40 × 2 mm native sheet uses an explicit sheet rule. The baseline adds Ø5 mm perforations on a 10 mm square pitch with a 5 mm margin.

## How Forge builds it in SolidCraft

Forge first emits the normal native sheet rule/base history, then emits one `sheet.perforate` command against the current sheet body. Diameter, pitch and optional margin remain parameterized. The initial API does not expose a Sketch/profile-bounded region.

## SolidCraft result

One connected closed native sheet body retains the perforation field as manufacturing/flat-pattern semantics. Forge does not create a repeated collection of solid Hole or Boolean-cut features.

## Saved-design test

Without rerunning Forge Python, mutate perforation diameter from 5 to 6 mm, pitch from 10 to 12 mm and margin from 5 to 6 mm. Rebuild/reopen must preserve one connected sheet body and coherent native perforation/flat-pattern evidence.

## Geometry evidence

> Geometry-rationale provenance: Forge #779 native perforation qualification.
**Bounds sufficient:** `false`

The folded B-rep envelope intentionally does not prove the perforation field: SolidCraft owns its manufacturing, DXF, flat-pattern and measured-volume semantics. Native history plus flat-pattern inspection is therefore required.

## Reference notes

- **Native SolidCraft history** — This capability is specifically a native manufacturing-field contract. External solid kernels are optional evidence and must not be substituted with repeated physical holes that change the semantics.
