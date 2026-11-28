# Post-Extrude geometry edits as suppressible configuration history

Status: Proposed  
Tracking: #669  
Motivating consumer: brainboxemb/2026-011-02.cad.solidcraft#281

## Change

The configuration mechanism is not being redesigned.

The required consumer history is the same pattern already proven by
`configuration-position-suppression`:

~~~text
base geometry
    |
    +-- later CAD history operation      [suppressed in base state]
~~~

For the HUB75 tube clamp the intended history is:

~~~text
Free profile
    |
    +-- Extrude -> physical Free clamp
    |
    +-- Installed geometry adjustment    [suppressed in Free]
~~~

`Free` must therefore be the already-authored physical clamp. `Installed`
must be one later geometry-changing history step. The final configuration only
suppresses or enables that step.

This is deliberately different from rebuilding the clamp from another parameter
row.

## Existing evidence

`configuration-position-suppression` already proves the generic state model:

~~~text
normal panel
    |
    +-- solid.move ServicePosition       [suppressed in Normal]
~~~

SolidCraft stores `solid.move` as one normal history feature and a saved
configuration can suppress/enable it without rerunning Forge Python.

Forge's existing public contract is also the intended contract here:

~~~python
with feature("installed", suppressed=True) as installed:
    body = body.some_geometry_edit(...)

body.configure(
    active="Free",
    columns=(installed,),
    rows={
        "Free": (True,),
        "Installed": (False,),
    },
)
~~~

The open question is the geometry operation inside that scope, not the
configuration API around it.

## Why this change is needed

The earlier Installed acceptance did not close the motivating clamp case.

The synthetic clamp probe used a second cylindrical cut. That correctly proved
feature suppression transport but did not model opening a preloaded clamp.

The later consumer acceptance then kept the tube clamp parameter-driven and used
the frame-coupler panel-pin revolve as the named-feature proof. That proved the
API mechanism, but not this required consumer history:

~~~text
Free clamp -> later Installed geometry change -> suppress/enable
~~~

Issue #669 restores that missing acceptance requirement.

## Probe A — edit the source Sketch after Extrude

SolidCraft 0.50 exposes:

~~~text
sketch.edit
sketch.move_point
sketch.move_points
sketch.transform
~~~

These commands edit an existing Sketch and rebuild features after it.

The first probe creates a Sketch, extrudes it, then edits the earlier Sketch and
moves two points after the Extrude has already been authored.

Question:

> Does that edit become a new timeline/history feature that can independently
> represent Installed, or does it only rewrite the earlier Sketch?

The expected evidence from `timeline.inspect` and the saved design is the
actual feature history after the edit.

If no later feature exists, Forge must not pretend that `sketch.move_points`
is itself a suppressible `feature(...)` operation.

## Probe B — real post-Extrude direct geometry history

SolidCraft also exposes direct geometry operations after body creation, including
`solid.offset_face`, `solid.replace_face` and `solid.move`.

The second probe creates a Sketch and Extrude, then applies one named
`solid.offset_face` feature named `Installed`.

It configures exactly that feature:

~~~text
Free       Installed = suppressed
Installed  Installed = active
~~~

The geometry is intentionally a rectangular diagnostic, not a clamp model. The
probe answers only whether an ordinary post-Extrude geometry edit is retained as
one suppressible saved history feature.

## Decision matrix

### A. Sketch edit is independently suppressible

If Probe A proves that the edit itself has independent history identity, Forge
should expose the smallest semantic sketch-edit operation needed by the consumer
and let the existing `feature(...)` contract name it.

No new configuration abstraction is required.

### B. Sketch edit rewrites the earlier Sketch, but direct geometry history works

If Probe A shows in-place Sketch mutation while Probe B succeeds, the intended
Forge direction is:

- keep `feature(...)` and `model.configure(...)` unchanged;
- expose the required generic post-Extrude direct-modeling operation through
  `Shape`;
- keep selection semantic and replay-bound, as with existing topology-aware
  modifiers;
- use that operation as the one Installed history step.

The clamp may expose a missing direct-modeling requirement, but that is a
geometry API issue, not a configuration issue.

### C. SolidCraft cannot represent the required later edit as one feature

If the clamp requires pointwise movement that none of the current native
post-Extrude operations can represent as one history feature, record that as a
precise SolidCraft capability gap.

Forge must not replace the missing backend operation with:

- a clamp-specific `flex()`;
- an oversized bore cut;
- hidden multiple features behind one semantic identity;
- a parameter-driven Installed rebuild.

## Proposed Forge API shape

No public spelling is approved yet.

The preferred shape, if the native operation maps cleanly, is an ordinary
Shape modifier inside the existing feature scope, for example:

~~~python
with feature("installed", suppressed=True) as installed:
    body = body.<generic_geometry_edit>(...)

body.configure(
    active="Free",
    columns=(installed,),
    rows={
        "Free": (True,),
        "Installed": (False,),
    },
)
~~~

The API name and arguments must follow the generic native operation proven by
the probes. They must not mention clamp, flex, preload or Installed.

## Acceptance

This design may move from Proposed only when:

1. Probe A records whether a post-Extrude Sketch edit is independent history or
   an in-place edit of the earlier Sketch.
2. Probe B proves or disproves saved suppression of a real post-Extrude geometry
   feature.
3. The next API proposal is based on that runtime evidence rather than a
   synthetic clamp operation.
4. The configuration contract remains the existing named-feature contract.
5. The selected operation is generic enough to belong in Forge independent of
   the HUB75 consumer.
