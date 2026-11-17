# 0032 — native face-attached explicit Sketches

Status: **implementation / native qualification in progress**  
Issue: **#266**  
SolidCraft target: **0.42.0**

## Problem

Forge's public `Sketch(on=target, parent=Anchor.TOP)` described a sketch on a
body face, but the compiler did not create a SolidCraft face-attached sketch.

Instead Forge created a free XY sketch, moved it to a calculated Z offset and
added a Forge-calculated target-face centre to every profile coordinate. That
duplicated face attachment and sketch-frame behaviour already owned by
SolidCraft.

The 0.6.2 repair in change 0030 only removed one false symbolic dependency from
that calculation. It did not remove the duplicated attachment model.

## Pinned SolidCraft 0.42 contract

The version-pinned runtime contracts now include both commands used by this
lowering:

- `model.faces(body=...)` returns each face's `index`, `area`,
  `plane_normal` and a `point` that picks that face;
- `sketch.create` accepts
  `plane={face: [x,y,z], body: ..., index: ...}` and reports how the new
  sketch was attached.

These contracts are stored under
`docs/vendor/solidcraft/0.42.0/runtime/contracts/`.

## Decision

For a TOP-attached explicit Sketch, Forge now emits:

1. `model.faces(body=<current body>)`;
2. replay bindings that select the unique largest face whose outward
   `plane_normal` is `[0, 0, 1]`, binding its `point` and `index`;
3. `sketch.create` with the returned point, body and index;
4. authored profile commands using their sketch-local coordinates directly.

Forge sets `project_edges=false` explicitly.

If the face query has no matching face or more than one equally largest
matching face, replay fails instead of silently choosing one.

## Replay

Replay v2 extends the existing result-binding mechanism so a binding may select
one record from a returned list and bind one field from that record.

This does not create a second modelling API. The replay document still contains
symbolic variables and every execution fills them from the actual SolidCraft
result before the later command runs.

Replay v1 remains accepted for existing files.

## Scope

This change moves `Anchor.TOP` attached Sketches to native face attachment.

`Anchor.CENTER`, `Anchor.BOTTOM` and `Anchor.INNER_BOTTOM` retain their
existing plane lowering until each has a separately qualified native mapping.
In particular CENTER is a mid-plane intent, not a body face.

## Regression contract

The Slot-family fixture must prove:

- the parent Box dimensions stay editable;
- direct Slot coordinates remain numeric;
- `model.faces` is emitted;
- `sketch.create` uses runtime face point/index variables and no XY offset;
- the resulting replay builds and cuts successfully in SolidCraft 0.42;
- the native sketch is face-attached rather than a free offset plane.

The Simple MFT model is the downstream model that exposed the problem; it is
not special-cased in Forge.
