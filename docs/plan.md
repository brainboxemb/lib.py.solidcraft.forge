# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Complete #452: adopt released `tool.cad.ci` 0.10.0 at exact commit
`c60bf64a393dff33440d22e9e9347cbbaba71c4b`.

The runtime publication repair in #444 has already proved that the configured
runtime tag can be published and pulled from an authenticated Docker session.
Normal Forge CAD-CI still uses tool 0.9.0 and therefore does not authenticate
to GHCR before consumer commands call `docker pull`.

This change updates only the reusable-workflow pin. Registry login remains
generic `tool.cad.ci` behavior; Forge scripts do not gain credentials or
registry logic.

## Execution order

1. Complete #452:
   - update the reusable-workflow pin from tool 0.9.0 to exact 0.10.0;
   - retain caller `packages: read`;
   - prove normal Forge CAD-CI can pull the configured immutable runtime.
2. Complete #444:
   - merge the already-proven directly-pullable runtime publication fix;
   - keep cache/publication-trigger policy in #446/#449.
3. Complete #438:
   - remove verification-library code from the runtime image;
   - keep stable heavy dependencies preinstalled;
   - supply the exact released verification wheel separately.
4. Complete #440 with simple-box only.
5. Continue #432 in small model batches.
6. Resume #430, finish #378, then #366.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #452 Adopt tool.cad.ci 0.10.0 for authenticated GHCR pulls | now | Released tool/tag and external acceptance are proven; only the Forge reusable-workflow pin changes. |
| #444 Keep published immutable SolidCraft runtime image available after merge | blocked | Publication fix is proven in PR #451; normal Forge consumption needs #452 authentication before that PR can be green. |
| #438 Remove verification-library code from the SolidCraft runtime | blocked | PR #447 exists; resume after #444/#452 establish a reliable authenticated runtime path. |
| #449 Make SolidCraft runtime publication manual-only | later | Separate publication-trigger policy. |
| #446 Remove GitHub Actions cache from SolidCraft runtime build | later | Separate build-cache policy. |
| #440 Prove declarative SolidCraft verification with simple-box | blocked | Exactly one model after runtime/package prerequisites. |
| #432 Use released declarative CAD verification in model verification | blocked | Continue only after #440 proves the final one-model structure. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Resume after model-verification ownership is stable. |
| #391 Extract reusable CAD verification library from Forge | blocked | Close after remaining shared checker code leaves Forge. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Umbrella migration; current blockers are runtime publication/authentication/package boundaries. |
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
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:
`#452 -> #444 -> #438 -> #440 simple-box -> #432 batches -> #430 -> #378 -> #366`.
