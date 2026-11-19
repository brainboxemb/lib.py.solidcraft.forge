# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Complete #426: add model-local reference geometry contracts for the next ten
models and run their four existing independent reference implementations through
released `lib.py.cad.verfication`.

The first proof, `simple-box`, is complete.

## Execution order

1. Complete #426 for the next ten models:
   - move only existing historical geometry expectations into local
     `reference_geometry.json` files;
   - preserve historical envelope, volume, watertightness and probe checks;
   - run PythonSCAD, pyBOSL2, CadQuery and build123d for those ten models plus
     simple-box;
   - keep generic validation in the released verification library.
2. Expand the same F5/F6 pattern to the remaining model catalog in a later PR.
3. Continue #378 with visual evidence and expected-shape comparison.
4. Add diagrams and the final verification summary.
5. Complete #366 only after #378 is complete:
   - durable accepted build output;
   - Pages publication from that durable output.
6. Run the final migration audit and close obsolete historical issues.

## Open issue assessment — 2026-11-19

| Issue | Status | Assessment |
| --- | --- | --- |
| #426 Add local reference geometry contracts for the next 10 Forge models | now | Active second F5/F6 batch after the simple-box proof. |
| #391 Extract reusable CAD verification library from Forge | effectively complete / adoption in progress | Reusable mechanics are released through verification-library 0.5.0. Keep open while #378 completes adoption. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Main verification migration. Current step is the next ten local reference contracts and four-reference runs. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Starts only after #378 verification output is complete. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Forge API defect independent of the current verification migration. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | CLI quality work, not a blocker for current verification work. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Product/API work after the current migration. |
| #354 Support standalone sketch extrusions as boolean operands | later | Product/API work after the current migration. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to the superseded qualification architecture; reassess after #378/#366. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement, not required for this reference-contract batch. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Model/API investigation independent of current verification work. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete / reassess | Old qualification wording/design; measure the final CAD-CI graph before deciding what remains. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog after the generic verification path is complete. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Product behavior issue independent of migration. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog independent of migration. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:
`#426 -> remaining references -> visual evidence -> diagrams -> summary -> #366 -> final migration audit`.
