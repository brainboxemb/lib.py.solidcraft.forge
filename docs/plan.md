# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Complete #432: finish restoring the verification ownership boundary across all
32 model verifiers now that the immutable Forge runtime on `main` contains
released `lib.py.cad.verfication` 0.7.0.

Forge keeps SolidCraft measurement parsing, model expectations, history rules,
mutations and other domain policy. Generic comparison and verification-failure
mechanics come from the released verification library.

## Execution order

1. Complete #432:
   - keep the existing numeric/vector/bounds migration to
     `compare_scalar()`, `compare_vector()`, `compare_bounds()` and
     `match_body_envelopes()`;
   - replace remaining local exact-value and predicate helpers with released
     `require_equal()` and `require_condition()`;
   - remove local generic `close`, `vector_close`, `bbox_close`,
     `bounds_match`, `require_bounds`, `require_equal` and
     `require_true` implementations;
   - re-audit all 32 model verifiers;
   - prove the complete affected Forge CI graph against the runtime already
     merged through #434.
2. Resume #430 using released `verify_visual_view()` while keeping
   SolidCraft rendering, camera conversion and model/view policy in Forge.
3. Expand visual verification to the next ten models and then the remaining
   catalog.
4. Complete #378 diagrams and final verification summary.
5. Complete #366 only after #378 verification output is complete.
6. Run the final migration/ownership audit and close or rewrite obsolete
   historical issues.

## Open issue assessment — 2026-11-19

| Issue | Status | Assessment |
| --- | --- | --- |
| #432 Use released CAD verification comparisons in model verifiers | now | Active ownership cleanup. Runtime 0.7.0 is now on main; finish removal of generic comparison/equality/predicate mechanics from all model verifiers and prove full CI. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Resume after #432. Generic one-view orchestration is released; Forge must retain only rendering, camera and model policy. |
| #391 Extract reusable CAD verification library from Forge | effectively complete but still open | Reusable mechanics are released through 0.7.0. Keep open while Forge completes consumer adoption and the final ownership audit. |
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
`#432 -> #430 -> visual expansion -> diagrams -> summary -> #366 -> final migration audit`.
