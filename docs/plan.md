# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Complete #449: make SolidCraft runtime publication manual-only.

Changing the runtime definition must not automatically build or publish an
image. Runtime publication is an explicit operator action through
`workflow_dispatch`.

After #449, continue the runtime/package-boundary correction in #438.

The verification library remains independently designed, tested and released,
but is intentionally preinstalled in the shared runtime image because every
model verification uses it. This avoids reinstalling the same released package
for every model check.

Release 0.10.0 provides:

- generic comparison/assertion/reporting mechanics;
- the SolidCraft verification adapter;
- declarative `SolidCraftVerification`;
- baseline, saved-design and inspection execution;
- partial timeline contracts that do not force generated SolidCraft names into
  model-specific expectations.

## Execution order

1. Complete #449:
   - remove automatic push/pull-request triggers from the runtime workflow;
   - keep only manual `workflow_dispatch`;
   - add a regression test for this boundary.
2. Complete #438:
   - pin verification-library 0.10.0 exact commit in
     `docker/solidcraft_runtime/runtime.json`;
   - use the already-published immutable runtime image produced from that
     definition;
   - update root `cad-ci.yml` to that exact image;
   - prove normal Forge CI against it.
3. Complete #440 with **simple-box only**:
   - keep only model-specific expectation/mutation data in the model;
   - keep Forge compilation/replay in a shared Forge producer path;
   - let released `run_solidcraft_verification()` own the actual verification;
   - remove simple-box's procedural `verify_model.py`;
   - change no other model verifier in that proof PR.
4. Continue umbrella issue #432 only after #440 is green, using small reviewable
   model batches.
5. Resolve verification-library #44/#45 before migrating models that need
   partial parameter/sketch contracts. Do not work around those gaps in Forge.
6. Resume #430 visual verification after the model-verification boundary is
   proven.
7. Complete #378 diagrams and final verification summary.
8. Complete #366 only after #378 verification output is complete.
9. Run the final ownership audit and close/rewrite obsolete historical issues.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #449 Make SolidCraft runtime publication manual-only | now | Runtime publication must only run through explicit workflow_dispatch; repository changes must not build/publish images automatically. |
| #446 Remove GitHub Actions cache from SolidCraft runtime build | now | Remove GitHub Actions cache transport from runtime builds. |
| #438 Update Forge verification runtime to lib.py.cad.verfication 0.10.0 | next | Runtime-only prerequisite. The released verification library stays preinstalled in the shared runtime for efficiency. |
| #440 Prove declarative SolidCraft verification with simple-box | next | First consumer proof after #438. Exactly one model; establishes the final launcher/definition shape. |
| #432 Use released declarative CAD verification in model verification | blocked | Umbrella migration. Continue only after #440 proves the one-model path. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Resume after the model-verification ownership path is stable. |
| #391 Extract reusable CAD verification library from Forge | blocked | Reusable library functionality is released through 0.10.0. Close only after remaining shared checker code is removed from Forge. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Migration umbrella; current path is #438, #440, then staged #432 migration. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Starts after #378 verification output is complete. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Forge API defect independent of current verification work. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | CLI quality work, not a blocker for current verification work. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Product/API work after current migration. |
| #354 Support standalone sketch extrusions as boolean operands | later | Product/API work after current migration. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to superseded qualification architecture; reassess after #378/#366. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement, not required for ownership migration. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Independent model/API investigation. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Predates the current reusable runtime/CAD-CI design; reassess after the current migration. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Independent product behavior. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:
`#449 -> #446 -> #438 -> #440 simple-box -> #432 batches -> #430 -> diagrams -> summary -> #366 -> final ownership audit`.
