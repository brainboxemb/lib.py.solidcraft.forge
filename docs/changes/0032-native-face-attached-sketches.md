# 0032 — native face-attached explicit Sketches

Status: **implemented; Q1-Q6 qualified on qualification commit `7918c437ebeaea95fa9936d90797c34648656215`**  
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


## Qualification result

The full Forge qualification workflow passed the native SolidCraft 0.42 build
for the implementation on commit `09a74905a0b70ebc65c427304ad5bb5930b0286b`;
the qualification branch adds only trigger metadata at
`7918c437ebeaea95fa9936d90797c34648656215`.

Native evidence confirms:

- `slot-family` resolves the TOP face from `model.faces`, then
  `sketch.create` returns `attachment: "exact_face"`;
- its five Slot profiles retain the expected coordinates, body bounds, volume,
  face counts and visual result;
- `rectangular-pattern` also returns `attachment: "exact_face"`, passes Q4
  and its required Q5 saved-design mutation;
- `rounded-rectangle-sketch` returns `attachment: "exact_face"` and passes
  Q4 plus visual validation;
- all native timelines in these cases contain no feature errors.

For the Slot fixture, SolidCraft selected the exact TOP face
`F1:+z` (face index 0) and supplied a valid pick point. Forge did not calculate
that point.
