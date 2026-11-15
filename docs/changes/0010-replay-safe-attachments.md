# Change 0010 — Replay-safe attachments

Status: implementation  
SolidCraft target: **0.42.0**

## Problem

After change 0009, ordinary Placement no longer predicts SolidCraft-generated
occurrence names. Attachment lowering still does.

The old compiler builds names such as:

```python
native_name = f"{component_name}:{index}"
```

and uses those strings in `joint.create`, `joint.origin`,
`joint.as_built` and sometimes `occurrence.move`.

Forge does not control SolidCraft's occurrence numbering. A replayable command
document must not depend on those generated names.

## Native SolidCraft 0.42 evidence

The focused native probe is on
`qualification/0010-joint-reference-probe`.

Probe run **43765272041** established:

- `joint.create` accepts a component name as the selector for that component's
  first occurrence;
- `joint.origin` accepts the component name for the first occurrence;
- `joint.as_built` accepts component names for first occurrences;
- a copied occurrence can be found by `joint.create` from a world face/point
  when that pick is unique;
- four copied occurrences were each resolved correctly from four different
  world points;
- `occurrence.move(occurrence="Block", ...)` fails with
  `no occurrence Block`.

A second focused probe tested two occurrences of the same `Block` definition
whose mating faces occupy the same world point.

- coincident copy inference **fails** because SolidCraft resolves both joint
  origins to the first occurrence;
- moving the copy temporarily away from the mating face makes the same
  occurrence inference **pass**.

This means occurrence inference is useful, but the compiler must give a copied
attached child a unique temporary seed pose before `joint.create`.

## Decision

### First occurrence

For relationship commands that SolidCraft 0.42 explicitly supports, Forge uses
the Forge-controlled **component name** to address the first occurrence.

This is allowed for:

- `joint.create`;
- `joint.origin`;
- `joint.as_built`.

It is **not** allowed for `occurrence.move`; the native probe proves that
command does not resolve a component name as an occurrence.

### Copied occurrence

Forge does not invent a selector for a copy.

For `joint.create`:

- omit the `occurrence` field for the copied side;
- provide the actual world topology/point at the copy's native seed pose;
- let SolidCraft 0.42 resolve the occurrence from that pick.

### Temporary seed gap

A copied normal attachment is created in a temporary assembly-wide parking
slot before its joint is authored.

Parking slots are 1000 mm apart. Slot `n` uses the temporary translation:

```text
(+1000n, -1000n, +1000n) mm
```

Only copied attached children use these positions. The first occurrence can be
addressed by the qualified component-name selector and stays at native
identity.

The copy and its world joint pick move together. Different copied children
therefore have different native positions even when their authored attachment
math produces the same pre-joint pose. This avoids the native 0.42 ambiguity
proved by the coincident same-definition probe.

The parking translation is compiler setup state only. The authored
`attach()` relationship remains the final relationship and moves every parked
copy to its requested position. Saved-design relationship behaviour is checked
after the native joint solve, not from the temporary parking coordinates.

### No generated occurrence names

Generated SolidCraft names such as `Block:2` may appear in native inspection
output, but Forge does not put them into the command document.

Human-readable joint names use Forge object names or labels such as
`Block occurrence 2`. Those labels are display text only.

## Explicitly unsupported in this change

### Relationship rotation

A relationship occurrence with `Placement(rotation=...)` is rejected.

The old implementation required `occurrence.move` with a predicted native
name. Correct rotated attachment transforms are handled separately by the
transform-safe attachment change.

### As-built copied occurrence

`joint.as_built` takes occurrence selectors only; it has no point-based
occurrence inference.

An as-built relationship involving a copied occurrence is therefore rejected
until SolidCraft provides a replay-safe selector for that copy.

A non-identity first as-built occurrence is also unsupported because
`component.create` cannot place it before the as-built joint is recorded.

### Chained attachments

An attached occurrence used as the parent of another attachment is rejected in
this change. Its world pick changes when the first joint solves, so it needs
explicit relationship ordering/transform qualification before Forge can claim
it is replay-safe.

## Qualification

Required command tests:

- no generated `Component:N` selector appears in an attachment plan;
- first occurrences use component names;
- copied joint origins omit `occurrence`;
- copied attached children receive distinct parking seeds;
- same-definition parent/child attachment remains one reusable component plus a
  copy;
- repeated copied brackets use point inference without generated names;
- rotated relationship Placement is rejected;
- copied as-built attachment is rejected;
- symbolic absolute Placement on a relationship target is rejected.

Required native tests:

- reusable two-block attachment;
- standard corner and XZ anchors;
- parametric attachment gap/offset cases;
- four/eight repeated corner components;
- saved-design mutations for relationships that claim associativity.

The native result, not the temporary seed position, determines whether the
relationship is qualified.
