# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Complete #438: remove the released verification-library code itself from the
immutable SolidCraft runtime while keeping repeated verification efficient.

The runtime remains the shared CAD execution environment and may preinstall
stable/heavy Python dependencies used by nearly every verification run.
`lib.py.cad.verfication` itself remains a separately released CAD-CI input.

The exact verification wheel is built once per affected CAD-CI graph and reused
by all model/reference verification items.

## Execution order

1. Complete #438:
   - remove verification-library version/commit from the runtime definition;
   - remove verification-library installation/version assertion from Docker;
   - explicitly retain compatible Pillow/trimesh/scipy runtime dependencies;
   - build the exact released verification-library wheel once as a reusable
     CAD-CI item;
   - make all model/reference verification depend on and mount that wheel;
   - prove the runtime image ID no longer depends on the verification release;
   - preserve manual-only, cache-free, directly pullable runtime publication.
2. Manually publish the new immutable runtime image.
3. Update `cad-ci.yml` to that exact image and prove the complete affected
   graph.
4. Rebase #460 on the corrected main.
5. Migrate exactly the ten #460 models using `verification/verify.py`.
6. Continue #432 through later reviewable batches.
7. Add/release missing generic verification semantics in
   `lib.py.cad.verfication` before models that need them.
8. Resume #430, then #378 and #366.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #438 Remove verification-library code from the SolidCraft runtime | now | Correct runtime/package boundary before further model migration. |
| #460 Migrate first ten model verifiers to declarative SolidCraft verification | blocked | Resume only after #438 is merged. |
| #432 Use released declarative CAD verification in model verification | blocked | Umbrella migration; proceeds through #460 and later batches. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Resume after model-verification ownership is stable. |
| #391 Extract reusable CAD verification library from Forge | blocked | Close after remaining shared checker code leaves Forge through staged #432 migration. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Umbrella migration. |
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
`#438 -> manual runtime publication -> #460 -> later #432 batches -> #430 -> #378 -> #366`.
