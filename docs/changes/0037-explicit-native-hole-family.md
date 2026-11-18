# 0037 — Explicit native Hole family

**Tracks:** issue #302  
**Scope:** public SCPF Hole API, native lowering, qualification and unit-test contracts.  
**SolidCraft target:** 0.42.0.

## Problem

Forge exposed a simple `Hole` plus countersink-specific optional arguments.
That mixed several distinct mechanical intents into one constructor and still
left native SolidCraft counterbore/thread capabilities unqualified.

The older `anchored-holes` qualification also used a generated Sketch/cut,
so it did not prove native `solid.hole` history.

## Decision

Expose four explicit mechanical features:

- `Hole`
- `CounterboreHole`
- `CountersinkHole`
- `ThreadedHole`

Each feature lowers one-to-one to one native `solid.hole` command when
explicitly positioned with `.at(...)`.

The public API uses engineering dimensions in diameter form. Forge does not
copy SolidCraft's native command parameter names directly.

## Thread intent

`ThreadedHole` keeps the tap drill and thread specification separate.

- `thread="M6"` selects the native thread designation;
- optional `d` overrides the native tap-drill diameter;
- `modeled=False` keeps thread metadata/cosmetic intent;
- `modeled=True` asks SolidCraft to cut modeled thread geometry;
- `thread_depth`, `hand` and `ease_out` remain thread-specific inputs.

## Qualification

The new `hole-family` case places four holes in one plate and proves:

- Q1 public API validation and body × feature compatibility;
- Q2 one native `solid.hole` per feature with no helper Sketch;
- Q3/Q4 native build/history and geometry;
- Q6 visible hole-form evidence.

PythonSCAD, pyBOSL2, CadQuery and build123d independently reproduce the visible
hole envelopes. Their threaded reference is the Ø5 M6 tap-drill envelope;
SolidCraft-native evidence proves thread metadata and modeled geometry.

## Compatibility

Forge is still in unstable release development. The former
`Hole(..., countersink_d=..., countersink_angle=..., countersink_recess=...)`
spelling is removed rather than retained as a compatibility alias. Use
`CountersinkHole` or `CounterboreHole` explicitly.
