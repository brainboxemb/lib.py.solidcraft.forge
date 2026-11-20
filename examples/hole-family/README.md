# Native Hole family

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `features`

## Goal

Qualify the four normal mechanical hole intents as direct native features: simple, counterbore, countersink and threaded.

## Forge API

Hole(...); CounterboreHole(...); CountersinkHole(...); ThreadedHole(...)

## Forge model

One 120 x 40 x 12 mm plate with four explicitly positioned Hole-family features. ThreadedHole keeps thread intent separate from the simple bore diameter.

## How Forge builds it in SolidCraft

Each Forge Hole-family object lowers one-to-one to one native solid.hole command. Counterbore and countersink use the native hole type fields; ThreadedHole uses native thread metadata/modeling fields. No sketch or helper subtraction solid is synthesized.

## SolidCraft result

One plate contains four editable native Hole features: Ø6 simple, Ø6/Ø12 x 4 counterbore, Ø6/Ø12 90° countersink, and an M6 modeled threaded hole using an explicit Ø5 tap drill.

## Saved-design test

No saved-design mutation is required in this first Hole-family qualification; unit, integration and native geometry checks prove API, native command identity and geometry while visual proves the visible forms.

## Reference notes

- **build123d** — build123d 0.12.0 provides native Hole, CounterBoreHole and CounterSinkHole operations. Its core library has no equivalent native tapped-hole metadata feature, so the fourth reference cut is the Ø5 M6 tap-drill envelope.
- **CadQuery** — CadQuery independently expresses simple, counterbore and countersink geometry; the threaded reference uses the Ø5 tap-drill envelope because native thread metadata is SolidCraft-specific.
- **PythonSCAD** — Constructive geometry independently reproduces the four hole envelopes; the thread reference is the Ø5 tap-drill envelope.
- **pyBOSL2** — Constructive geometry independently reproduces the four hole envelopes; the thread reference is the Ø5 tap-drill envelope.
