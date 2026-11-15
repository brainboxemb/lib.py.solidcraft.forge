# Change 0009 — Replay-first occurrence Placement

Status: implementation  
SolidCraft target: **0.42.0**

## Problem

Forge 0.3.x accepts constructor-time `Placement`, but some placements are
currently compiled by creating an occurrence first and targeting it later with
`occurrence.move`.

The later command is addressed with a name Forge predicts SolidCraft will
generate, for example:

```python
native_name = f"{component_name}:{index}"
```

Forge does not own that generated name. A static replayable command document
must not depend on it.

Change 0008 fixed Forge's own occurrence tracking. This change fixes the
ordinary Placement path that can be expressed without a later occurrence
selector.

## SolidCraft 0.42 limits

The pinned 0.42 command contract gives Forge these creation-time options:

- `component.create` creates the component definition and its first occurrence,
  but has no translation or rotation input;
- `occurrence.copy(..., translate=[x, y, z])` can place a copied occurrence
  numerically;
- `occurrence.copy.translate` is numeric-only;
- copied orientation is not an `occurrence.copy` input;
- `occurrence.move` can express symbolic translation and rotation, but it needs
  an existing occurrence id or name.

A runtime id exists after create/copy, but normal Forge output is replay-first
and does not capture command results.

## Decision

For ordinary Placement with no attachment relationship:

1. Forge uses an identity-placed occurrence as SolidCraft's implicit first
   occurrence.
2. Additional concrete, unrotated placements use
   `occurrence.copy(..., translate=...)`.
3. Forge does not generate `occurrence.move` for ordinary Placement.
4. If no identity occurrence exists for that reusable definition, compilation
   fails clearly.
5. A copied ordinary Placement that is symbolic or rotated also fails clearly
   because SolidCraft 0.42 cannot express it safely in `occurrence.copy`.
6. Forge never falls back to a predicted `Component:N` name for these cases.

The compiler may choose which Forge occurrence uses SolidCraft's implicit first
placement. Display numbering is not Forge identity.

## Attachments are separate

This change does not repair joint/attachment addressing.

An attachment may still need a seed pose and a later joint command. Both the
child occurrence and the occurrence used as its attachment parent are therefore
kept on the relationship path in this change. Those paths are handled by the
next relationship change because they need a replay-safe occurrence reference
for the relationship itself.

Keeping that work separate avoids turning ordinary Placement into a joint or
mixing two independent problems in one patch.

## Public API meaning

`Placement` remains constructor/copy metadata. It is still an absolute pose in
the parent coordinate frame.

What changes is the currently supported backend subset. Forge rejects a
Placement that cannot be represented safely in a static SolidCraft 0.42 command
document.

This supersedes the `occurrence.move` fallback described in change 0001 for
ordinary, unattached Placement. The historical record in change 0001 remains
unchanged except for a pointer to this correction.

## Tests

The focused tests must prove:

- one identity occurrence plus a numeric unrotated copy needs no
  `occurrence.move`;
- Forge can bind a later identity occurrence to SolidCraft's implicit first
  occurrence instead of depending on Python list position;
- a definition with no identity occurrence is rejected;
- symbolic ordinary copy Placement is rejected;
- rotated ordinary copy Placement is rejected;
- no ordinary Placement test accepts a generated `Component:N` selector.


## Qualification changes

The old native qualification cases `parametric-move`,
`parametric-placement-pair` and `rotated-copy-placement` depended on the
predicted-name `occurrence.move` fallback. They are removed from the native
Q3-Q6 registry in this change.

Focused Python/command tests remain and now require a clear `ModelError`.
They can return to native qualification only after Forge has a replay-safe
SolidCraft selector for those occurrence placements.

Other qualification cases that used Placement only to spread unrelated bodies
out for screenshots now keep that layout inside their fixed fixture geometry.
Their actual qualification subject (parameter scope, grouping, imported
assemblies, etc.) no longer depends on an unrelated unsupported occurrence
placement.
