# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Complete #430 as the first #378 F7-F9 visual proof with `simple-box`.

F5/F6 are complete: all 32 current model items own local reference geometry
contracts and all four independent reference implementations pass.

## Execution order

1. Complete #430 for `simple-box`:
   - render the saved SolidCraft model in deterministic required views;
   - keep camera/view policy in Forge and generic projection/image mechanics in
     released `lib.py.cad.verfication`;
   - migrate the existing approved simple-box visual baselines model-locally;
   - run visual regression through the released library;
   - produce model-local goal and overlay evidence through the released
     expected-shape APIs.
2. Expand the proven F7-F9 path to the next ten models.
3. Expand F7-F9 to the remaining model catalog.
4. Add #378 F10 diagrams.
5. Add #378 F11 verification summary without rerunning CAD work.
6. Complete #366 only after #378 is complete:
   - durable accepted build output;
   - Pages publication from that durable output.
7. Run the final migration audit and close obsolete historical issues.

## Open issue assessment — 2026-11-19

| Issue | Status | Assessment |
| --- | --- | --- |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | now | Active first F7-F9 proof. Keep scope to simple-box before the next 10-model visual batch. |
| #391 Extract reusable CAD verification library from Forge | effectively complete / adoption in progress | Reusable geometry, visual and semantic mechanics are released through verification-library 0.5.0. Keep open while #378 completes Forge adoption. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Parent migration task. F5/F6 are complete; F7-F9 visual evidence is current, then F10/F11. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Starts only after #378 verification output is complete. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Forge API defect independent of the current verification migration. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | CLI quality work, not a blocker for current verification work. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Product/API work after the current migration. |
| #354 Support standalone sketch extrusions as boolean operands | later | Product/API work after the current migration. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to the superseded qualification architecture; reassess after #378/#366. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement, not required for the current visual migration. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Model/API investigation independent of current verification work. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete / reassess | Old qualification wording/design; measure the final CAD-CI graph before deciding what remains. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog after the generic verification path is complete. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Product behavior issue independent of migration. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog independent of migration. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:
`#430 simple-box visual -> next 10 visual -> all visual -> diagrams -> summary -> #366 -> final migration audit`.
