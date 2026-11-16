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
- omitting an occurrence selector can make SolidCraft infer an occurrence from
  geometry, but this is not an explicit occurrence reference and therefore is
  **not accepted as a Forge identity mechanism**;
- `occurrence.move(occurrence="Block", ...)` fails with
  `no occurrence Block`.

The copy-inference probes remain useful evidence of SolidCraft behaviour, but
they are not a supported Forge implementation strategy. An inference that works
only while a pick is unique can become ambiguous after geometry, placement or
assembly changes.

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

Forge has no explicit replay-safe SolidCraft 0.42 selector for a copied
occurrence in the relationship commands covered by this change.

Therefore a copied occurrence is **not supported as an attachment endpoint**.

Forge does not:

- omit the occurrence selector and rely on geometry inference;
- move the copy temporarily to make a pick unique;
- invent a generated occurrence name;
- add runtime result binding.

If copied-occurrence relationship support is needed later, it requires a
separate design change based on an explicit SolidCraft reference mechanism.
If that mechanism is not clearly reliable, it must be discussed before
implementation.

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
- copied occurrences used as attachment endpoints are rejected;
- same-definition parent/child attachment is rejected when one side would be a
  copy;
- repeated copied brackets that require attachment relationships are rejected
  rather than inferred from geometry;
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
