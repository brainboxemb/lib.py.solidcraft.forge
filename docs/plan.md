# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Restore the verification ownership boundary found during the #378 audit.

Released `lib.py.cad.verfication` 0.7.0 at exact commit
`a7b2eede634508d3c04a115a201ea91b9d0e2714` now contains:

- generic numeric/vector/bounds/body-envelope comparisons;
- generic visual primitives and one-view orchestration;
- generic semantic result composition;
- generic exact-value and predicate verification helpers.

Forge #432 has already proved the numeric/bounds migration on its branch. The
next required step is #434: rebuild the immutable Forge runtime with 0.7.0 so
#432 can remove the remaining local `require_equal` / `require_true`
helpers before merge.

## Execution order

1. Complete #434:
   - pin verification-library 0.7.0 exact commit in `runtime.json`;
   - publish the resulting immutable runtime image;
   - update root `cad-ci.yml` to that exact image;
   - prove normal Forge CI with the new runtime.
2. Rebase/refresh #432 on the new main:
   - retain the already-green numeric/vector/bounds library migration;
   - replace all remaining local `require_equal` / `require_true` helpers
     with released `require_equal()` / `require_condition()`;
   - re-audit all 32 model verifiers.
3. Resume #430:
   - keep SolidCraft rendering/camera/model data in Forge;
   - use released `verify_visual_view()` for generic visual verification.
4. Expand visual verification to the next ten models, then the remaining
   catalog.
5. Complete #378 diagrams and final verification summary.
6. Complete #366 only after #378 is complete.
7. Return to verification-library #4 for the final ownership audit.

## Open issue assessment — 2026-11-19

| Issue | Status | Assessment |
| --- | --- | --- |
| #434 Update Forge verification runtime to lib.py.cad.verfication 0.7.0 | now | Required before #432 can consume the final generic assertion helpers. Keep runtime build definition and CI runtime expectation separate. |
| #432 Use released CAD verification comparisons in model verifiers | blocked on #434 | Numeric/vector/bounds migration is green on the branch. Do not merge until runtime 0.7.0 exists and local exact/predicate helpers are also removed. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked on #432 | Generic visual orchestration is released in library 0.6.0+, but visual work resumes only after the ownership cleanup is complete. |
| #391 Extract reusable CAD verification library from Forge | effectively complete / adoption in progress | Reusable library functionality now reaches 0.7.0. Keep open until #378 consumer adoption and final audit are complete. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Reference F5/F6 is complete for all 32 models. Current work is ownership cleanup, then F7-F11. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Starts only after #378 verification output is complete. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Forge API defect independent of the verification migration. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | CLI quality work, not a blocker for current migration. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Product/API work after current migration. |
| #354 Support standalone sketch extrusions as boolean operands | later | Product/API work after current migration. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to the superseded qualification architecture; reassess after #378/#366. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement, not required for ownership cleanup. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Model/API investigation independent of current migration. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete / reassess | Old qualification terminology/design; measure final CAD-CI behavior before deciding what remains. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog after generic migration. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Product behavior issue independent of migration. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog independent of migration. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:
`#434 -> #432 -> #430 -> visual expansion -> diagrams -> summary -> #366 -> verification-library #4 final audit`.
