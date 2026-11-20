# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Make Forge `main` healthy again through #452.

Adopt released `tool.cad.ci` 0.10.0 at exact commit
`c60bf64a393dff33440d22e9e9347cbbaba71c4b`, so normal Forge CAD-CI
authenticates Docker to GHCR before model commands pull the configured immutable
runtime image.

The runtime keeps released `lib.py.cad.verfication` preinstalled and exactly
pinned for efficient repeated model verification.

## Execution order

1. Complete #452:
   - update the reusable-workflow pin from tool 0.9.0 to exact 0.10.0;
   - retain caller `packages: read`;
   - prove the PR run is green;
   - merge and prove the Forge `main` push run is green.
2. Complete #444:
   - merge the directly-pullable runtime publication fix;
   - keep runtime contents unchanged;
   - prove the exact runtime remains pullable.
3. Complete #440 with simple-box only.
4. Continue #432 in small reviewable model batches.
5. Resolve verification-library #44/#45 before migrating models that need
   partial parameter/sketch contracts. Do not add Forge workarounds.
6. Complete #446 and #449 separately; runtime cache policy and publication
   trigger policy are independent changes.
7. Resume #430, then complete #378 diagrams/summary and #366 publication.
8. Run the final ownership audit and close/rewrite obsolete historical issues.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #452 Adopt tool.cad.ci 0.10.0 for authenticated GHCR pulls | now | First priority: restore green Forge main. Released tool and external acceptance are already green. |
| #444 Keep published immutable SolidCraft runtime image available after merge | next | Runtime publication repair is proven on its branch; merge only after main is healthy through #452. |
| #440 Prove declarative SolidCraft verification with simple-box | blocked | Resume only after main is green and #444 is merged. |
| #432 Use released declarative CAD verification in model verification | blocked | Continue only after #440 proves one model. |
| #449 Make SolidCraft runtime publication manual-only | later | Separate publication-trigger policy. |
| #446 Remove GitHub Actions cache from SolidCraft runtime build | later | Separate Buildx-cache policy. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Resume after model-verification ownership is stable. |
| #391 Extract reusable CAD verification library from Forge | blocked | Close after remaining shared checker code leaves Forge; do not move the released verification package out of the runtime. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Umbrella migration; current path is #452, #444, then staged model migration. |
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
`#452 -> main green -> #444 -> #440 simple-box -> #432 batches -> #430 -> #378 -> #366`.
