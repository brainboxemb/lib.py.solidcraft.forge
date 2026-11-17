# 0031 — associative sketch pattern and mirror

Status: **implementation in qualification**  
Issue: **#272**  
SolidCraft target: **0.42.0**

## Problem

SolidCraft can keep repeated sketch geometry associative. A user can draw one
Circle or Slot, repeat it with `sketch.pattern.rectangular`, mirror the result,
and save those relationships in the design.

Forge could already draw the Circle or Slot, but it had to expand every repeated
copy as another Python profile. The final shape could look right while the
saved SolidCraft Sketch lost the useful pattern and mirror relationships.

## SolidCraft behaviour

SolidCraft 0.42 provides:

- `sketch.pattern.rectangular`;
- `sketch.mirror`.

Both commands consume ids of curves already present in the active Sketch.

Circle, Slot, pattern and mirror commands return the curves they created in a
top-level `curves` result field.

Forge already has replay variables for exactly this situation: bind a value
returned by one command and pass it to a later command during live execution
and file replay.

## Public Forge API

Initial scope:

```python
with Sketch(name="Pattern", on=body, parent=Anchor.TOP) as sketch:
    seed = Circle2D(d=8)
    row = sketch.rectangular_pattern(
        seed,
        count=4,
        spacing=25,
        direction=Axis.X,
    )
    sketch.mirror(row, axis=Axis.X)
```

The same operations work with a native Slot profile:

```python
with Sketch(name="Slots", on=body, parent=Anchor.TOP) as sketch:
    seed = SlotCenterToCenter2D((20, 20), (40, 20), 8)
    arm = sketch.rectangular_pattern(
        seed,
        count=2,
        spacing=50,
        direction=Axis.X,
    )
    other = sketch.mirror(arm, axis=Axis.Y)
    sketch.mirror(arm, axis=Axis.X)
    sketch.mirror(other, axis=Axis.X)
```

`rectangular_pattern()` returns a Sketch-operation handle. `mirror()` can use
that handle as its source.

Pattern count and spacing may remain normal Forge parameters. Count parameters
are published as unitless SolidCraft parameters; spacing remains a length.

## Replay lowering

User Python never contains SolidCraft-generated curve ids.

When a later Sketch operation needs a profile:

1. Forge binds that profile command's returned `curves` field to a replay
   variable.
2. `sketch.pattern.rectangular` receives that variable as `entities`.
3. Forge binds the pattern command's returned `curves`.
4. A later `sketch.mirror` can consume the pattern result in the same way.

The replay document therefore stays static and replayable. Live execution and
file replay use the same bindings.

## Initial limits

This change intentionally starts with the operations needed by the current
models:

- attached Sketches only;
- rectangular sketch pattern;
- fixed 2D direction vectors or `Axis.X` / `Axis.Y`;
- mirror over the Sketch X or Y origin axis;
- at most 500 pattern instances, matching SolidCraft;
- no per-instance pattern suppression.

SolidCraft also has circular sketch patterns and mirror-by-line support. They
are not exposed by this first Forge API and must not be implied by the docs.

## Qualification

The `sketch-pattern-mirror` case proves both profile families in one model:

- one Circle seed;
- one native Circle rectangular pattern;
- one native Circle mirror;
- one Slot seed;
- one native Slot rectangular pattern;
- three native Slot mirrors;
- one through-cut per Sketch.

Q5 changes the saved SolidCraft design without rerunning Python:

- hole diameter 8 -> 10 mm;
- hole count 4 -> 3;
- hole pitch 25 -> 30 mm;
- Slot count 2 -> 3;
- Slot pitch 50 -> 30 mm.

The rebuilt saved design must change from 8 holes + 8 Slots to 6 holes + 12
Slots while keeping the same two Sketch/cut history entries.
