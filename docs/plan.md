# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

The generic CI stack remains externally owned and accepted:

- `lib.py.cad.ci` 0.8.3;
- `tool.cad.ci` 0.13.3 at
  `bbdd473638d64e01acab69722092b2a12f99b84d`.

Closed-PR durable build cleanup is complete through #507 / PR #513.

The runtime owner released v0.2.0 as two immutable role images:

- `ghcr.io/brainboxemb/cad-solidcraft:v0.2.0`;
- `ghcr.io/brainboxemb/cad-reference:v0.2.0`.

The previous five-model staging was premature. The active performance proof
returns to one model: `simple-box`.

## Current goal

Complete #484 by adopting v0.2.0 and measuring one cold/warm simple-box path.

Required staging:

- `simple-box` is the only active model-verification item;
- anchor-topology-mutation, attach-angle, four-corner-l and xz-anchor are
  `process: false`;
- reference verification is temporarily `process: false` during the timing
  proof;
- model verification uses `cad-solidcraft:v0.2.0`;
- reference verification is pinned to `cad-reference:v0.2.0` for later
  resumption;
- no Forge-local runtime packaging, scheduler or cache is introduced.

## Measured clean baseline

PR #515 run `44758695910` is the first uncontaminated one-model v0.2.0 run.

- structured `simple-box:model_verify` duration: 12.054 s;
- pre-pull host work: about 0.279 s;
- `cad-solidcraft:v0.2.0` pull: about 5.540 s;
- post-pull to verification pass: about 6.115 s;
- post-pull to completed target: about 6.238 s;
- no reference target ran and the reference image was not pulled.

The runtime split therefore removed most of the old ~44 s cold cost. The
remaining post-pull ~6.2 s is still above the historical ~1.4-1.9 s warm-model
range and must be decomposed before #484 is complete.

## Required proof

1. The adoption PR is green with exactly one active model-verification item.
2. A representative simple-box-only source change selects simple-box and its
   normal Forge package dependency path, not the other four models or reference
   verification.
3. Structured CAD-CI evidence confirms the model action duration.
4. The live log separates the v0.2.0 image pull from post-pull model work.
5. Compare against the old ~44 s cold first-model result and ~1.4-1.9 s warm
   model range.
6. Emit diagnostic phase timing for container/Python startup, native replay and
   verification, then explain the remaining ~6.2 s before changing process
   lifetime.

## Execution order

1. #484 — adopt v0.2.0 roles and prove one simple-box runtime path.
2. #430 / #378 — continue the complete visual/evidence proof on simple-box only.
3. #366 / #497 — resume durable build/Pages work after the one-model path is stable.
4. #432 — broader model migration only after the simple-box chain is complete.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #484 Reduce cold SolidCraft runtime overhead without changing model verification semantics | now | v0.2.0 is released; prove it with simple-box only. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | next | Correct continuation after the runtime baseline is stable. |
| #378 Use explicit Forge verification stages instead of integration/native gates | next | Continue through simple-box only. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Resume after simple-box runtime/evidence is stable. |
| #497 Publish stable Pages from the generic build/main baseline | blocked | Depends on #366. |
| #432 Use released declarative CAD verification in model verification | blocked | Broader catalog migration remains paused. |
| #391 Extract reusable CAD verification library from Forge | blocked | Complete only after procedural verification is migrated. |
| #481 Remove stale Forge development branches | blocked | Current connected tooling cannot delete stale refs. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by docker.cad.solidcraft v0.2.0 and #484. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to superseded qualification architecture. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Independent Forge API defect. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | Independent CLI quality work. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Independent product/API work. |
| #354 Support standalone sketch extrusions as boolean operands | later | Independent product/API work. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement after references resume. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Independent model/API investigation. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Independent product behavior. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Major Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:

`#484 simple-box timing -> #430/#378 simple-box evidence -> #366/#497 publication`.
