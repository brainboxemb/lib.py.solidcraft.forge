# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Complete #444: make the explicitly published immutable SolidCraft runtime
reliably pullable.

Forge `main` is green on released `tool.cad.ci` 0.10.0. The runtime
remains manual-only, uses no GitHub Actions Buildx cache, and keeps the exact
released `lib.py.cad.verfication` package preinstalled for efficiency.

#444 changes publication/availability checks only; it does not change runtime
contents.

## Execution order

1. Complete #444:
   - publish the single-platform runtime with `provenance: false`;
   - define runtime availability as manifest present plus successful real
     `docker pull`;
   - treat a missing child manifest as unavailable;
   - keep authentication/network failures as errors;
   - merge only after normal Forge CI is green.
2. Complete #440 with simple-box only.
3. Continue #432 in small reviewable model batches.
4. Resolve verification-library #44/#45 before migrating models that need
   partial parameter/sketch contracts. Do not add Forge workarounds.
5. Resume #430, then complete #378 diagrams/summary and #366 publication.
6. Run the final ownership audit and close/rewrite obsolete historical issues.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #444 Keep published immutable SolidCraft runtime image available after merge | now | Current runtime-publication correctness work. Runtime contents remain unchanged. |
| #440 Prove declarative SolidCraft verification with simple-box | next | First model proof after runtime publication is stable. |
| #432 Use released declarative CAD verification in model verification | blocked | Continue only after #440 proves one model. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Resume after model-verification ownership is stable. |
| #391 Extract reusable CAD verification library from Forge | blocked | Close after remaining shared checker code leaves Forge; do not move the released verification package out of the runtime. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Umbrella migration; current path is #444, #440, then staged model migration. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Starts after #378 verification output is complete. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Independent Forge API defect. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | Independent CLI quality work. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Product/API work. |
| #354 Support standalone sketch extrusions as boolean operands | later | Product/API work. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to superseded qualification architecture; reassess after #378/#366. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Independent model/API investigation. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Predates current runtime/CAD-CI design; reassess after migration. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Independent product behavior. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:
`#444 -> #440 simple-box -> #432 batches -> #430 -> #378 -> #366`.
