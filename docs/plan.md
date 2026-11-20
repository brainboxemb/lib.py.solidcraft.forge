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
through released CAD-CI and generated `build/pr/*` scopes are no longer left
behind.

`docker.cad.solidcraft` v0.2.0 is released as two immutable roles:

- `ghcr.io/brainboxemb/cad-solidcraft:v0.2.0`;
- `ghcr.io/brainboxemb/cad-reference:v0.2.0`.

PR #514 is merged. Forge now consumes those two immutable roles and only
`simple-box` remains `process: true` as a model-verification item.

The first decomposed cold `simple-box:model_verify` measurement on v0.2.0 was
about 12.2 s total:

- Forge compile: ~0.12 s;
- SolidCraft image pull: ~7.65 s;
- container creation/start: ~3.17 s;
- Python bootstrap: ~0.17 s;
- verification-library import: ~0.75 s;
- native model production: ~0.11 s;
- SolidCraft verification itself: ~0.04 s.

The model/verification work is therefore no longer the dominant cost. Remaining
cold-path cost is primarily image acquisition plus Docker container startup.

## Current goal

Complete #516 with one representative `simple-box`-specific change so the
end-to-end selected graph and total CI time are measured without shared
runtime/reference changes contaminating selection.

This is the final measurement required before #484 can be closed.

## Required proof

- exactly one `simple-box` model-verification item participates;
- normal Forge package dependency work is selected only where required;
- no other model-verification item runs;
- no independent reference item runs;
- `cad-reference:v0.2.0` is not pulled;
- structured CAD-CI evidence identifies the `simple-box` step durations;
- the live log confirms the already measured cold-path decomposition;
- no verification semantics are changed merely to improve timing.

## Execution order

1. #516 — measure a normal simple-box-only selected run.
2. Close #484 after recording the resulting timing and selection evidence.
3. #430 / #378 — continue visual and staged verification on `simple-box`
   only.
4. #366 / #497 — resume durable main/Pages work only after the one-model path
   is stable.
5. #432 — broader model migration remains blocked until the simple-box proof is
   complete.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #516 Measure one-model simple-box CI after runtime v0.2.0 adoption | now | Final uncontaminated selection/timing proof after merged #514. |
| #484 Reduce cold SolidCraft runtime overhead without changing model verification semantics | blocked | Runtime split and phase timing are proven; close after #516 records the normal simple-box-only run. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | next | Correct one-model continuation after #484/#516. |
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

`#516 simple-box measurement -> close #484 -> #430/#378 simple-box verification -> #366/#497`.
