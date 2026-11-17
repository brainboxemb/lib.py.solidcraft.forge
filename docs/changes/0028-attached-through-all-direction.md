# 0028 — attached Sketch through-all direction

Status: **implemented; qualification required before merge**  
Issue: **#218**  
SolidCraft target: **0.42.0**

## Problem

An attached Sketch on a body's TOP face could compile this cut without an
error and still leave the body unchanged:

```python
with Sketch(name="Cuts", on=body) as cuts:
    Circle2D(d=20)

body = body - cuts.extrude(Depth.THROUGH_ALL)
```

Forge emitted `through_all=true` but omitted `direction`. SolidCraft 0.42
treats a missing extrusion direction as `positive`. On the TOP support face
the positive XY sketch normal points away from the body, so the cut can miss
the target completely.

An error-free timeline is therefore not enough to prove this operation.

## Native SolidCraft contract

The pinned SolidCraft 0.42 `solid.extrude` schema has separate
`through_all` and `direction` fields:

- `through_all=true` selects the through-all extent;
- `direction` is `positive`, `negative` or `symmetric`;
- a missing direction defaults to `positive`.

Forge must send the direction needed by the selected support face instead of
depending on that default.

## Forge API contract

The public API remains:

```python
sketch.extrude(Depth.THROUGH_ALL)
```

for an attached Sketch cut. No new argument is added.

For the qualified cardinal support faces:

- `parent=Anchor.TOP` cuts in the native `negative` direction;
- `parent=Anchor.BOTTOM` cuts in the native `positive` direction.

This means THROUGH_ALL cuts through the body from the selected support face.
Finite signed Sketch extrusion keeps the change-0024 contract unchanged.

Other support anchors are not newly qualified by this change.

## Lowering

`Sketch.extrude()` records the native direction together with the
`Depth.THROUGH_ALL` marker.

The feature compiler emits both fields:

```json
{
  "command": "solid.extrude",
  "params": {
    "through_all": true,
    "direction": "negative",
    "operation": "cut"
  }
}
```

for a normal TOP-face cut. BOTTOM emits `direction="positive"`.

## Qualification

The smallest reproduction is kept as its own fixture:

```text
examples/attached-through-all/scpf/model.py
```

It contains one bottom-anchored Box, one attached TOP-face Sketch and one
Circle2D profile. Its Q2 test proves the emitted native cut uses
`through_all=true`, `direction="negative"` and no finite `distance`.

A focused compiler regression separately proves both TOP and BOTTOM support
directions, so BOTTOM cannot regress merely because the public reproduction is
the normal TOP-face cut.

The existing Slot-family qualification remains a separate Slot-constructor
case. After this fix its SCPF fixture can remove the temporary fixed `-5 mm`
workaround and again use `Depth.THROUGH_ALL` while keeping the same geometry
and the same four independent reference models.

That existing Q4 check already proves the same attached-Sketch THROUGH_ALL
lowering changes the native body by checking exact qualified volume, face count
and face types. A no-op plate with six planar faces and full uncut volume cannot
pass it. This reuses an existing native geometry gate; it does not make #218 a
Slot API change.

The existing signed-distance regressions continue to prove positive, negative
and symmetric finite Sketch extrusion from change 0024.
