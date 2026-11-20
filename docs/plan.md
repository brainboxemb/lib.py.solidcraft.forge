# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

The generic CAD-CI baseline is accepted:

- `lib.py.cad.ci` 0.8.3;
- `tool.cad.ci` 0.13.3 at
  `bbdd473638d64e01acab69722092b2a12f99b84d`;
- external acceptance covers nested selection/publication and streamed concise
  execution logging.

Durable PR build lifecycle cleanup is complete. Closed PR scopes are removed
through released CAD-CI and the accumulated stale `build/pr/*` scopes have been
removed; the generated build branch currently contains only `main/`.

`docker.cad.solidcraft` v0.2.0 is released as two immutable roles:

- `ghcr.io/brainboxemb/cad-solidcraft:v0.2.0`;
- `ghcr.io/brainboxemb/cad-reference:v0.2.0`.

Hosted-runner clean-pull evidence for the immutable release was:

- SolidCraft role: 13.386 s;
- reference role: 46.679 s.

The preceding `:edge` proof measured 9.974 s and 23.073 s respectively.
Normal model verification must therefore load only the lightweight SolidCraft
role; reference-image cost must not be charged to the model path.

The previous five-model Forge staging was premature. The active model proof is
again exactly one model: `simple-box`.

## Current goal

Complete #484 by adopting the two immutable v0.2.0 runtime roles and measuring
the remaining cold path with only `simple-box` active as a model-verification
item.

## Required proof

- `FORGE_RUNTIME_IMAGE` is exactly
  `ghcr.io/brainboxemb/cad-solidcraft:v0.2.0`;
- `REFERENCE_RUNTIME_IMAGE` is exactly
  `ghcr.io/brainboxemb/cad-reference:v0.2.0`;
- model verification consumes only `FORGE_RUNTIME_IMAGE`;
- independent reference verification consumes only
  `REFERENCE_RUNTIME_IMAGE`;
- `simple-box` is the only model item with `process: true`;
- every other historical model item remains explicit `process: false`;
- structured CAD-CI evidence and the live log identify the actual
  `simple-box:model_verify` duration;
- the live log separates SolidCraft image acquisition from the subsequent
  container/model work;
- no verification semantics are weakened to improve timing.

Broader model/reference migration does not resume merely because this PR is
green. The one-model timing must first be understood.

## Execution order

1. #484 — adopt runtime v0.2.0 and prove the one-model `simple-box` path.
2. #430 / #378 — continue visual and staged verification on `simple-box`
   only.
3. #366 / #497 — resume durable main/Pages work only after the one-model path
   is stable.
4. #432 — broader model migration remains blocked until the simple-box proof is
   complete.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #484 Reduce cold SolidCraft runtime overhead without changing model verification semantics | now | v0.2.0 is released; adopt the two roles and analyze one simple-box model path. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | next | Correct one-model continuation after #484. |
| #378 Use explicit Forge verification stages instead of integration/native gates | next | Continue through simple-box only after runtime timing is stable. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Resume after the one-model runtime/verification path is stable. |
| #497 Publish stable Pages from the generic build/main baseline | blocked | Depends on stable durable generated output. |
| #432 Use released declarative CAD verification in model verification | blocked | Broader catalog migration must not resume before simple-box is stable. |
| #391 Extract reusable CAD verification library from Forge | blocked | Complete only after procedural verification is migrated. |
| #481 Remove stale Forge development branches | blocked | Current connected tooling cannot delete the stale refs. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by docker.cad.solidcraft v0.2.0 and #484. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to superseded qualification architecture. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Independent Forge API defect. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | Independent CLI quality work. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Independent product/API work. |
| #354 Support standalone sketch extrusions as boolean operands | later | Independent product/API work. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Independent model/API investigation. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Independent product behavior. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Major Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:

`#484 simple-box runtime proof -> #430/#378 simple-box verification -> #366/#497`.
