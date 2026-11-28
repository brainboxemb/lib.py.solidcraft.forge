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


## Probe results — SolidCraft 0.50.0

PR #670 qualification run 46166188263 is green for both focused probes.

### Probe A — source Sketch edit

Result: **the edit is not a later history feature**.

The saved design contains exactly two timeline features after
`sketch.edit` + `sketch.move_points`:

~~~text
1  FreeProfile   sketch
2  ClampExtrude  extrude
~~~

The right-hand Sketch points are stored at their edited coordinates (X=12
instead of X=10), so the operation has rewritten the existing `FreeProfile`
feature and rebuilt `ClampExtrude`.

There is no third timeline feature for the edit.

Decision:

- do not expose `sketch.move_points` as though it were a later suppressible
  `feature(...)`;
- a chronological Installed state cannot be implemented by editing the
  upstream source Sketch after its Extrude and expecting that edit to be
  independently suppressible.

This is a timeline/history fact, not a Forge configuration limitation.

### Probe B — post-Extrude direct geometry

Result: **a real later solid edit is exactly the required history form**.

The saved design contains:

~~~text
1  FreeProfile   sketch
2  ClampExtrude  extrude
3  Installed     offset_face
~~~

The native configuration stores feature 3 as its suppression column:

~~~text
Free       Installed = suppressed
Installed  Installed = active
~~~

The run switches Installed and back to Free successfully without rerunning
Forge authoring.

Decision:

- the existing `feature(...)` / `model.configure(...)` contract is correct;
- the missing consumer capability is a suitable generic post-Extrude
  solid-edit operation;
- configuration must not be redesigned.

### Why Offset Face is evidence, not the clamp solution

`solid.offset_face` is intentionally only the positive history probe.

For the clamp, one common offset distance cannot simultaneously move the inner
and outer cylindrical faces to the required new radii while preserving the
2.0 mm wall. Using it only on the bore would simply replace the old oversized
cutter with another wall-thinning approximation.

Therefore the green Offset Face probe proves the feature-history architecture,
not the final HUB75 geometry operation.

## Newer SolidCraft candidate: Transform Face

Current SolidCraft `main` contains a direct-modeling command
`solid.transform_face`.

Its generic contract is:

- select one face;
- rotate it, translate it, or do both;
- neighbouring faces extend or trim to meet the moved face;
- the operation is retained as a normal named modelling feature.

The current command schema accepts `name`, so it matches the same native
feature identity/suppression architecture as the successful Offset Face probe.

This operation is **not present in the SolidCraft 0.50.0 command reference
used by Forge v0.27.0**. It therefore cannot be adopted or claimed by this
change until it exists in the versioned Forge runtime/reference and has its own
probe there.

It is also singular-face today. The HUB75 consumer must still prove whether one
face transform can express the intended clamp state, or whether the required
generic operation must move a related face/section set atomically.

Do not widen Forge's API merely because a newer backend command exists.

## Revised next step

The next implementation/design slice is now precise:

1. keep the existing configuration and named-feature API unchanged;
2. treat post-Extrude solid editing as the required capability family;
3. qualify the smallest native operation that can reproduce the HUB75
   Installed geometry while preserving its wall and physical intent;
4. only then add the matching generic Shape modifier to Forge;
5. require the Forge operation itself to produce exactly one history feature so
   it remains valid inside `feature("installed", suppressed=True)`.

The CAD consumer must not proceed with `offset_face` merely because Probe B is
green.


## Correction — Installed is not a row axis

The first #669 proposal incorrectly showed:

~~~python
model.configure(
    active="Free",
    columns=(installed,),
    rows={
        "Free": (True,),
        "Installed": (False,),
    },
)
~~~

That is the wrong user model.

It conflates two independent axes:

1. the ordinary configuration row axis;
2. the physical Free/Installed state switch.

The required presentation is one ordinary row (for example `Normal`) plus an
independent native checkbox named `Installed`.

Conceptually:

~~~text
Configuration row: Normal

Installed [ ]
    off -> Installed feature suppressed -> Free geometry

Installed [x]
    on  -> Installed feature active     -> Installed geometry
~~~

If a consumer already has `Small / Medium / Large` rows, those rows remain
unchanged and the Installed checkbox remains orthogonal to them. Do not create
`Small-Free`, `Small-Installed`, `Medium-Free`, etc.

### Native SolidCraft 0.50 mechanism

SolidCraft 0.50 `config.rule` supports:

- an independent `enabled` checkbox;
- `condition: always`;
- `effect: drive_suppression`;
- a concrete feature id as the suppression target.

Therefore the native lowering for the authored Installed feature is:

~~~text
Normal row
    suppress Installed = true

Configuration Rule "Installed"
    enabled = false
    condition = always
    drive suppression(Installed) = false
~~~

When the rule is disabled, the row's Free/base suppression is restored.
When the rule is enabled, the same real history feature becomes active.

This is the same orthogonal rule behavior that the older Installed baseline
proved for parameter driving, but now applied to the correct authored feature
instead of changing `clamp_bore`.

### Forge API consequence

The earlier audit conclusion that Configuration Rules were unnecessary is no
longer valid for this consumer requirement.

Forge needs a semantic way to author an independent configuration switch over a
real feature. It must lower to the native rule checkbox without exposing
SolidCraft feature ids.

The exact public spelling is still a design question. The required semantics
are now fixed:

~~~text
row axis                 stays row-owned
Installed state switch   independent enabled checkbox
target                    semantic authored feature
enabled effect            unsuppress that feature
disabled effect           restore row/base suppression
~~~

Do not represent Installed as a second row.
