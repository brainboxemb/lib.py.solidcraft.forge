# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Complete #444: make the manually published immutable SolidCraft runtime tag
immediately and reliably pullable.

#449, #446 and #452 are already on green `main`:

- runtime publication is manual-only;
- runtime publication does not use GitHub Actions cache storage;
- normal Forge CAD-CI authenticates Docker to GHCR through released
  `tool.cad.ci` 0.10.0.

#444 changes only publication validation/representation. Runtime package
composition is handled separately by #438.

## Execution order

1. Complete #444:
   - publish the single-platform runtime with `provenance: false`;
   - require both manifest presence and a real Docker pull;
   - treat a missing child manifest as unavailable;
   - prove normal Forge CAD-CI remains green.
2. Complete #438:
   - remove `lib.py.cad.verfication` itself from the runtime image;
   - keep stable heavy dependencies preinstalled for efficiency;
   - supply the exact released verification wheel separately.
3. Complete #440 with **simple-box only**.
4. Continue #432 in small reviewable model batches.
5. Resume #430, finish #378, then #366.
6. Run the final ownership audit.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #444 Keep published immutable SolidCraft runtime image available after merge | now | Fix and prove the immutable runtime publication/pull path on top of current green main. |
| #438 Remove verification-library code from the SolidCraft runtime | next | Correct the package boundary after runtime publication itself is reliable. |
| #440 Prove declarative SolidCraft verification with simple-box | blocked | Exactly one model after #444/#438. |
| #432 Use released declarative CAD verification in model verification | blocked | Continue only after #440 proves the final one-model structure. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Resume after model-verification ownership is stable. |
| #391 Extract reusable CAD verification library from Forge | blocked | Close after remaining shared checker code leaves Forge. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Umbrella migration; current path is #444, #438, #440, then staged model migration. |
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
`#444 -> #438 -> #440 simple-box -> #432 batches -> #430 -> #378 -> #366`.
