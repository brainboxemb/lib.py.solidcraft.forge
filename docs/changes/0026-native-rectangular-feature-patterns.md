# 0026 — native rectangular feature patterns

Status: **active design**  
Issue: **#215**  
SolidCraft target: **0.42.0**

## Goal

Add SCPF support for SolidCraft's native rectangular **feature pattern** command.

The main concern in this change is the JSON/native command contract. The public
Python spelling should stay small and expression-first; it must not force users
to manage SolidCraft history-name strings manually.

## Native SolidCraft command

Forge must emit:

```text
solid.pattern.rectangular
```

for an existing source feature.

Relevant SolidCraft 0.42 fields:

```json
{
  "command": "solid.pattern.rectangular",
  "params": {
    "features": ["<native-feature-id-or-name>"],
    "dir1": [1, 0, 0],
    "count1": 6,
    "spacing1": 16,
    "dir2": [0, 1, 0],
    "count2": 3,
    "spacing2": 22,
    "alignment": "right",
    "alignment2": "right",
    "reversed": false,
    "reversed2": false
  }
}
```

Direction 2 is optional.

Counts include the original feature.

## Forge responsibility

A Shape operation such as `Sketch.extrude()` already represents a native
history feature when it is lowered.

To pattern that result later, Forge must retain enough internal identity to emit
the correct `features=[...]` reference in the JSON command.

This identity is an implementation detail between the SCPF expression tree and
the SolidCraft JSON plan.

The user should not have to repeat a SolidCraft history label as a string just
to reference the source operation.

Conceptually:

```python
slot_cut = slot.extrude(-4)
plate = plate - slot_cut

plate = plate.rectangular_pattern(
    slot_cut,
    columns=6,
    spacing_x=16,
    rows=3,
    spacing_y=22,
)
```

The compiler is responsible for turning `slot_cut` into the correct native
feature reference in `features`.

## Naming

The official Vent Plate example happens to use:

```text
Sketch: Slot
Extrusion feature: Vent
Pattern: RectangularPattern1
```

Those are example/history labels, not an API requirement for SCPF.

A separate optional display/history name may be useful later, but native
feature-pattern support must not depend on the user manually naming the source
feature.

## Parameters and directions

- `count1`, `spacing1`, `count2` and `spacing2` should preserve native
  expressions when SCPF Parameters/Expressions are used and the SolidCraft
  field accepts them.
- Principal-axis convenience may map `Axis.X/Y/Z` to native direction vectors.
- The lower-level implementation should still allow the SolidCraft contract to
  represent arbitrary valid direction vectors where needed.
- Alignment/reversed values should be passed through using the native
  SolidCraft semantics.

## Existing Hole.pattern()

`Hole.pattern()` is a different SCPF concept. It expands a layout before
lowering and currently becomes sketch circles plus a cut.

Do not silently redefine `Hole.pattern()` as a native history pattern in this
change.

Do not add `Hole.grid()` as the primary solution.

## Qualification

Forge must qualify this capability itself before the CAD library consumes it.

Use one small abstract source cut and prove:

- the source feature is emitted once;
- one `solid.pattern.rectangular` command is emitted;
- `features` points at the actual emitted source feature;
- one-direction and two-direction command forms work;
- counts/spacings remain native expressions where supported;
- SolidCraft 0.42 saves one native rectangular pattern timeline feature;
- Q4 proves the pattern changes geometry;
- Q6 shows the patterned result.

The full Vent Plate remains a downstream CAD-library example.

## Non-goals

- no Simple MFT logic;
- no product-specific grid API;
- no Python-loop emulation of a native pattern;
- no circular/path pattern API in this change;
- no requirement for users to manage native history labels manually.
