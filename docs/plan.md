# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Complete the verification ownership correction without adding another checker
layer to Forge.

Forge keeps the Forge library, models and model-specific expectation data.
`lib.py.cad.verfication` owns both generic verification mechanics and
CAD-tool-specific verification adapters.

#432 is currently blocked on `lib.py.cad.verfication#32`. The SolidCraft
adapter must be independently designed, tested and released there before Forge
consumer code continues.

## Execution order

1. Complete and release `lib.py.cad.verfication#32` with the SolidCraft
   verification adapter.
2. Resume #432 with one representative model:
   - keep model-specific expected values/data in Forge;
   - pass those declarations to the released SolidCraft adapter;
   - remove Forge-local SolidCraft result parsing/eval/mutate/inspect helpers;
   - remove local generic comparison/assertion helpers;
   - remove `verification/solidcraft_measurements.py`.
3. Expand the proven #432 path to the remaining 31 model verifiers and run the
   complete affected Forge CI graph.
4. Resume #430 using released verification APIs. Forge keeps model-specific
   view/camera/baseline data; reusable SolidCraft rendering/checking behavior
   belongs in the verification library adapter.
5. Expand visual verification to the next ten models and then the remaining
   catalog.
6. Complete #378 diagrams and final verification summary.
7. Complete #366 only after #378 verification output is complete.
8. Run the final migration/ownership audit and close or rewrite obsolete
   historical issues.

## Open issue assessment — 2026-11-19

| Issue | Status | Assessment |
| --- | --- | --- |
| #432 Use released CAD verification adapter in model verification | blocked | Blocked on `lib.py.cad.verfication#32` and its release. After release prove one model first, then migrate the remaining catalog. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Resume after #432. Generic one-view orchestration is released; Forge must retain only rendering, camera and model policy. |
| #391 Extract reusable CAD verification library from Forge | blocked | The generic mechanics are released, but the ownership audit exposed remaining SolidCraft checker knowledge in Forge. Close only after #32 is released and #432 removes it. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Main migration umbrella. Reference verification is complete; current work is ownership cleanup followed by visual, diagram and summary evidence. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Starts after #378 verification output is complete. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Forge API defect independent of the current verification migration. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | CLI quality work; not a blocker for the current migration. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Product/API work after the current migration. |
| #354 Support standalone sketch extrusions as boolean operands | later | Product/API work after the current migration. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to the superseded qualification architecture; reassess after #378/#366. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement; not required for ownership cleanup. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Model/API investigation independent of the current verification migration. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Refers to the old qualification architecture. Measure final CAD-CI behavior before deciding whether a replacement performance issue is needed. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog after the generic migration. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Product presentation issue independent of migration. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog independent of migration. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:
`verification-library #32 -> release -> #432 one model -> #432 remaining models -> #430 -> visual expansion -> diagrams -> summary -> #366 -> final migration audit`.
