# SolidCraft 0.42 joint occurrence references

Status: **captured from pinned native runtime**  
SolidCraft: **0.42.0**  
Research branch: `qualification/0010-joint-reference-probe`

This file records the replay-relevant occurrence addressing behaviour used by
Forge change 0010.

It is intentionally concrete. Do not infer that one SolidCraft command accepts
the same selector as another command.

## Schema facts

### joint.create

A joint origin may contain an optional `occurrence` id/name.

When `occurrence` is omitted, SolidCraft may find the occurrence from the
supplied world point/topology pick.

### joint.origin

The occurrence selector accepts the component name for that component's first
occurrence.

### joint.as_built

The `a` and `b` occurrence selectors accept a component name for that
component's first occurrence.

### occurrence.move

The `occurrence` field accepts an occurrence id/name. It does **not** treat a
component name as an alias for the first occurrence.

## Native probes

### First occurrence by component name

PASS:

- `joint.create` with `occurrence: "Base"`;
- `joint.origin` with `occurrence: "Base"`;
- `joint.as_built` with `a: "Base", b: "Marker"`.

These commands resolved the first native occurrence of the named component.

### Copied occurrence from a world pick

PASS:

- copied occurrence selected from a unique face pick with no `occurrence`;
- copied occurrence selected from a unique point/frame pick with no
  `occurrence`;
- four copies of one reusable definition selected independently from four
  different world points.

The resulting native joint inspection reported the expected generated
occurrences (`Bracket:1` through `Bracket:4`). Those names were native output;
they were not present in the input command document.

### Component name passed to occurrence.move

FAIL:

```text
occurrence.move(occurrence="Block", ...)
-> no occurrence Block
```

Therefore Forge must not assume that the first-occurrence component-name
selector used by joint commands also works for `occurrence.move`.

### Coincident copies

FAIL:

Two occurrences of the same component definition had mating origins at the same
world point. The copied side omitted `occurrence`.

SolidCraft resolved both joint origins to the first occurrence and rejected the
joint because both sides referred to the same native occurrence.

PASS after separating the copied occurrence before `joint.create`.

This is why Forge change 0010 gives copied attached children distinct temporary
parking poses before authoring their joints. The parking pose only makes native
occurrence inference unambiguous; the joint still defines the final
relationship.

## Forge rule derived from these probes

For replay-first SolidCraft 0.42 output:

- first occurrence in a joint command: component-name selector is allowed;
- copied side of `joint.create`: omit `occurrence` and use an unambiguous
  world topology/point pick;
- copied side of `joint.as_built`: unsupported because there is no equivalent
  point-based selector;
- `occurrence.move`: never substitute a component name for an occurrence
  selector;
- never predict generated labels such as `Component:2`.

Probe runs used during change 0010 include `43765272041` and the later
same-definition coincidence probes on the same research branch.
