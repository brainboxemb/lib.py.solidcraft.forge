# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Complete #418 as the first consumer step of #378: prove simple-box independent
reference verification through released `lib.py.cad.verfication` 0.5.0.

## Execution order

1. Complete #418:
   - use released verification library 0.5.0 in the immutable runtime;
   - keep simple-box reference geometry local to the model;
   - run PythonSCAD, pyBOSL2, CadQuery and build123d independently;
   - verify all exported STL files through the released verification library.
2. Complete #424 after #418 is on main:
   - keep `runtime.json` as the runtime build definition;
   - declare the exact runtime/version expected by CI in root `cad-ci.yml`;
   - remove unnecessary workflow-only runtime metadata plumbing.
3. Continue #378 by expanding the same reference path to all model items, then
   add visual evidence, diagrams and the final result summary.
4. Complete #366 only after the verification graph is complete: durable build
   output first, then Pages.

## Open issue assessment — 2026-11-19

| Issue | Status | Assessment |
| --- | --- | --- |
| #424 Declare the expected Forge CI runtime in cad-ci.yml | next | Do immediately after #418 so the CI expectation is fixed against the runtime build definition actually present on main. |
| #418 Use released verification library for simple-box independent references | now | Active PR. First proof that Forge consumes verification-library 0.5.0 without reintroducing generic verification logic. |
| #391 Extract reusable CAD verification library from Forge | effectively complete / adoption in progress | Reusable verification mechanics are released through 0.5.0. Keep open while #378 proves and expands Forge consumption. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Parent migration task. #418 is its current F5/F6 step; continue references, visuals, diagrams and summary afterward. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Starts only after #378 verification output is complete. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Forge API defect, independent of the current verification/CI path. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | CLI quality work, not a blocker for the current migration. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Product/API work after the current migration. |
| #354 Support standalone sketch extrusions as boolean operands | later | Product/API work after the current migration. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Coverage backlog after migration work. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog after migration work. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to the superseded qualification architecture; reassess after #378/#366. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement, not required for the current simple-box proof. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Model/API investigation independent of the current CI work. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete / reassess | Old qualification wording/design; measure the final CAD-CI graph before deciding what remains. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog after the generic verification path is restored. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Product behavior issue independent of migration. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog independent of migration. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:
`#418 -> #424 -> #378 remaining verification -> #366 -> final migration audit`.
