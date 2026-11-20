# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Complete #460: migrate the first ten legacy model verifiers to the declarative
SolidCraft verification path proven by simple-box.

The runtime ownership migration is complete:

- `docker.cad.solidcraft` owns and releases the reusable runtime;
- Forge consumes
  `ghcr.io/brainboxemb/cad-solidcraft:v0.1.0`;
- Forge main is green against that immutable release;
- Forge owns no runtime Dockerfile or publication workflow.

The #460 batch is intentionally limited to models whose current verification
contracts are fully expressible through released
`lib.py.cad.verfication` 0.10.0. No generic checker behavior may be added to
Forge to make a model fit this batch.

## Models in this batch

Exactly these ten models:

- anchor-topology-mutation;
- assembly-owned-anchor;
- attach-angle;
- corner-anchor;
- eight-corner-brackets;
- four-corner-l;
- parametric-anchor;
- parametric-attach;
- parametric-offset;
- xz-anchor.

## Execution order

1. Re-read each selected model's existing procedural verifier and preserve only
   checks that are actually part of its current contract.
2. For each selected model:
   - add model-local `verification/verify.py`;
   - remove procedural `verification/verify_model.py`;
   - switch only that model's `ci.yml` to
     `scripts/model_verify_declarative.py`;
   - keep existing mutation command/data files model-local;
   - do not add incidental parameter/timeline/body expectations that were not
     checked before.
3. Extend the declarative-boundary test so these ten models are explicitly
   declarative while an excluded model remains on the legacy path.
4. Prove the complete affected CAD-CI graph against
   `cad-solidcraft:v0.1.0`.
5. Merge #460 only when all migrated models pass without changes to shared
   Forge verification mechanics.
6. Continue #432 with the next reviewable batch.
7. Before migrating a model that needs missing reusable semantics, add, test
   and release that behavior in `lib.py.cad.verfication` first.
8. Resume #430 visual verification after the model-verification migration is
   sufficiently stable.
9. Complete #378 diagrams/summary and then #366 publication.
10. Run the final ownership audit.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #460 Migrate first ten model verifiers to declarative SolidCraft verification | now | First reviewable model batch after simple-box and the runtime ownership cleanup. |
| #432 Use released declarative CAD verification in model verification | blocked | Umbrella migration; continue after #460 through later reviewable batches. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Resume after model-verification ownership is stable. |
| #391 Extract reusable CAD verification library from Forge | blocked | Close after remaining shared checker code leaves Forge through staged #432 migration. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Umbrella migration; current work is #460 under #432. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Starts after #378 verification output is complete. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Independent Forge API defect. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | Independent CLI quality work. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Product/API work. |
| #354 Support standalone sketch extrusions as boolean operands | later | Product/API work. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to superseded qualification architecture. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Independent model/API investigation. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Predates the released docker.cad.solidcraft runtime. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Independent product behavior. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Major Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:
`#460 -> later #432 batches -> #430 -> #378 -> #366`.
