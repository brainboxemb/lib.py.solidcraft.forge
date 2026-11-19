# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Complete #438: remove `lib.py.cad.verfication` itself from the immutable
SolidCraft runtime image.

The runtime image remains the efficient reusable CAD execution environment. It
may contain SolidCraft, reference CAD tools and stable Python dependencies that
are used on nearly every verification run.

Released application libraries are separate inputs:

- the built Forge/SCPF wheel;
- the released `lib.py.cad.verfication` package.

Changing only either application library must not require rebuilding the CAD
runtime image.

## Execution order

1. Complete #438:
   - remove verification-library version/commit from `runtime.json`;
   - remove installation/version assertion of the verification library from
     the Dockerfile;
   - explicitly retain the stable dependencies needed on every verification
     run, including Pillow, trimesh and scipy;
   - prove whether PyYAML and matplotlib are still runtime requirements and
     remove them if they are not;
   - supply the exact released verification package separately to model
     verification;
   - prove that a verification-library release does not change the runtime
     image ID.
2. Resume #432 with `simple-box` only using the released declarative
   SolidCraft verification API.
3. Expand #432 only after the simple-box path is clear and green.
4. Resume #430 visual verification.
5. Continue #378 and then #366.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #438 Remove verification-library code from the SolidCraft runtime | now | Correct the runtime/package boundary before Forge consumes the new declarative verification API. |
| #432 Use released declarative CAD verification in model verification | blocked | Wait for #438; then prove simple-box only. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Resume after #432 establishes the final model-verification structure. |
| #391 Extract reusable CAD verification library from Forge | blocked | Library is released; keep open until Forge removes remaining shared checker code. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Umbrella migration; current work is #438 then #432. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Starts after verification output is complete. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Independent Forge API defect. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | Independent CLI quality work. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Product/API work. |
| #354 Support standalone sketch extrusions as boolean operands | later | Product/API work. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to superseded qualification architecture. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Independent model/API investigation. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Original issue predates current runtime design; reassess after #438. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Independent product behavior. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:
`#438 -> #432 simple-box -> #432 expansion -> #430 -> #378 -> #366`.
