# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Restore the verification ownership boundary found during the #378 audit.

Two concrete boundary fixes are active:

1. #430 visual verification is blocked until
   `lib.py.cad.verfication` #26 is released; Forge must not own generic
   visual verification orchestration.
2. #432 removes duplicated generic numeric/vector/bounds comparison math from
   model verifiers and uses the already released library APIs.

Reference verification F5/F6 is complete for all 32 current model items.

## Execution order

1. Complete `lib.py.cad.verfication` #26 and release it independently.
2. Complete Forge #432 using released comparison APIs already available in the
   verification library.
3. Update the immutable Forge runtime to the new verification-library release.
4. Resume Forge #430 using only the released generic visual-view API plus
   Forge-owned SolidCraft rendering/camera/model data.
5. Expand the proven visual path to the next ten models, then the remaining
   catalog.
6. Add #378 diagrams and the final verification summary.
7. Complete #366 only after #378 is complete.
8. Run the final verification-library #4 ownership audit and close obsolete
   historical issues.

## Open issue assessment — 2026-11-19

| Issue | Status | Assessment |
| --- | --- | --- |
| #432 Use released CAD verification comparisons in model verifiers | now | Boundary-audit cleanup. Replace duplicated generic numeric/vector/bounds math with released library APIs; keep SolidCraft measurement parsing and model expectations local. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | The first implementation attempt exposed missing generic visual orchestration. Resume only after verification-library #26 is released and the Forge runtime pins it. |
| #391 Extract reusable CAD verification library from Forge | effectively complete / adoption in progress | Core reusable mechanics are released; #26 fills one orchestration gap discovered during consumer adoption, and #432 removes stranded comparison use in Forge. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | F5/F6 reference verification is complete for all 32 models. Current work is boundary cleanup, then F7-F9 visual evidence. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Starts only after #378 verification output is complete. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Forge API defect independent of the current verification migration. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | CLI quality work, not a blocker for current verification work. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Product/API work after the current migration. |
| #354 Support standalone sketch extrusions as boolean operands | later | Product/API work after the current migration. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to the superseded qualification architecture; reassess after #378/#366. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement, not required for the ownership cleanup. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Model/API investigation independent of current verification work. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete / reassess | Old qualification wording/design; measure final CAD-CI behavior before deciding what remains. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog after the generic verification path is complete. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Product behavior issue independent of migration. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog independent of migration. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:
`verification-library #26 -> Forge #432 -> runtime update -> Forge #430 -> visual expansion -> diagrams -> summary -> #366 -> final audit`.
