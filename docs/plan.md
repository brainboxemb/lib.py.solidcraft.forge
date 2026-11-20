# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Complete #440 with **simple-box only**.

The repository baseline is healthy:

- runtime publication is manual-only;
- runtime publication uses no GitHub Actions cache storage;
- the immutable runtime is directly pullable;
- normal Forge CAD-CI uses released `tool.cad.ci` 0.10.0 and is green;
- the runtime contains released `lib.py.cad.verfication` 0.10.0.

For #440, Forge keeps only simple-box-specific expectation/mutation data.
Released `run_solidcraft_verification()` owns the actual SolidCraft
verification execution/reporting.

## Execution order

1. Complete #440:
   - keep Forge compile/replay as the shared producer step;
   - add a small simple-box `verification/definition.py`;
   - remove simple-box's procedural `verify_model.py`;
   - make the shared model launcher load the declarative definition and call
     released `run_solidcraft_verification()`;
   - change no other model verifier;
   - prove the complete simple-box `model_verify` path through normal CAD-CI.
2. Continue #432 in small reviewable model batches only after #440 is green.
3. When a later model needs reusable verification semantics not present in the
   released library, implement/test/release them in
   `lib.py.cad.verfication` first.
4. Resume #430 visual verification.
5. Complete #378 diagrams/summary and then #366 publication.
6. Run the final ownership audit.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #440 Prove declarative SolidCraft verification with simple-box | now | One-model proof of the final declarative model-verification structure. |
| #432 Use released declarative CAD verification in model verification | blocked | Continue only after #440 proves the final one-model structure. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Resume after model-verification ownership is stable. |
| #391 Extract reusable CAD verification library from Forge | blocked | Close after remaining shared checker code leaves Forge through staged #432 migration. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Umbrella migration; current work is #440, then staged #432 migration. |
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
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Predates current runtime/CAD-CI design. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Independent product behavior. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Major Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:
`#440 simple-box -> #432 batches -> #430 -> #378 -> #366`.
