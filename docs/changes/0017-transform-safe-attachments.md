# Change 0017 — Reject rotated normal attachments before lowering

Status: implementation  
SolidCraft target: **0.42.0**

## Problem

Forge supports rotated ordinary `Placement` by applying an
`occurrence.move` to the occurrence returned by SolidCraft.

Normal attachments are different. Their `Anchor`, `AnchorFrame` and
`AnchorTopology` references are currently lowered from component-local
coordinates. Forge does not yet apply an occurrence Placement rotation to every
point and orientation vector in those references.

Applying only the translation would create a plausible-looking but wrong joint.

The existing compiler has several local checks for rotated relationships. The
checks are spread over component-definition handling and corner-anchor helpers,
so the rule is not expressed once for every supported attachment reference.

## Contract

For a normal attachment (`as_built=False`):

- the child occurrence must not have a rotated `Placement`;
- the target/parent occurrence must not have a rotated `Placement`;
- this is checked before component geometry and joint references are lowered.

Validation happens before Forge emits any component, occurrence or joint command.

This rule applies equally to:

- standard `Anchor` references;
- direct `AnchorFrame`;
- direct `AnchorTopology`;
- named component anchors that resolve to `AnchorFrame` or
  `AnchorTopology`;
- mixed combinations of those reference types.

Forge raises `ModelError` with a clear rotated-normal-attachment message. It
does not try a translation-only fallback.

## Ordinary Placement remains supported

A rotated occurrence that is not part of a normal attachment continues to use
the replay-safe `occurrence.move` path from changes 0013/0014.

## As-built relationships remain supported

An `as_built=True` relationship does not lower anchor points or orientation
frames. It relates two occurrences in their already-declared poses.

Therefore rotated Placement remains allowed for as-built relationships when the
occurrence pose itself is replay-safe.

## Why reject instead of transform now

A correct transform implementation must rotate:

- point/edge/on/corner pick coordinates;
- AnchorFrame `x` and `z` axes;
- AnchorTopology optional `x` and `z` axes;
- standard face/corner frame orientation;
- parent and child references independently.

That needs its own native SolidCraft qualification. Until that exists, early
rejection is safer than silently emitting an incomplete transform.

## Non-goals

- no new rotation math in this change;
- no change to ordinary rotated Placement;
- no change to `attachment.angle`, planar offset or gap;
- no change to as-built joint semantics;
- no guessed SolidCraft occurrence names.

## Qualification

Required regressions:

- rotated parent + standard Anchor -> early error;
- rotated child + standard Anchor -> early error;
- rotated parent/child + direct AnchorFrame -> early error;
- rotated parent/child + direct AnchorTopology -> early error;
- rotated named custom frame/topology anchor -> early error;
- no joint/partial reference commands are emitted after rejection;
- rotated ordinary Placement still compiles;
- rotated as-built relationship still compiles using bound occurrence ids.

## Exit condition

> Forge never lowers a normal attachment through a rotated Placement unless the
> complete attachment reference frame can be transformed correctly.
