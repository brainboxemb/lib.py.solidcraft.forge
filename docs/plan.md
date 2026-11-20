# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

The staged F1-F11 verification proof is complete.

- the five staged qualification cases use declarative model verification;
- each staged case has four independent nested reference items;
- durable `build/main` uses the generic CAD-CI build-store and contains only
  current configured items;
- released/accepted `tool.cad.ci 0.14.2` owns durable removed-item cleanup;
- workflow YAML is test-owned rather than a Forge-package input, so
  workflow-only changes no longer fan out through every model consumer.

The current public Pages state is preserved exactly on
`backup/gh-pages-before-f11-2026-11-20` at
`127adb3900cdc9ca6194edb1102ea7d505316295`.

A Pages compatibility audit found:

- the preserved public Qualification site contains 32 case pages, all PASS;
- current source still contains the same 32 `examples/<case>/model.yml`
  presentation records;
- current durable `build/main` contains current qualification evidence for
  only the five staged cases.

Cutting Pages over now from `build/main` would therefore shrink the public
Qualification catalog from 32 current-looking cases to 5. Do not do that.

## Current goal

Resume #432 and rebuild current durable evidence for the remaining Qualification
catalog in reviewable batches of approximately 10 cases.

The first batch follows the existing public Qualification order rather than a
new arbitrary ordering:

1. `anchored-holes`;
2. `hole-family`;
3. `sheet-fold`;
4. `top-sketch-after-chamfer`;
5. `parameter-scope`;
6. `parent-derived-child-size`;
7. `components`;
8. `repeated-parent-attachments`;
9. `assembly-decorator`;
10. `group-hierarchy`.

All ten still use procedural `verification/verify_model.py` today.

Do not implement Forge-local verification workarounds. The first-batch audit
identified reusable SolidCraft semantics that must land in
`lib.py.cad.verification` first:

- #44 partial parameter expectations;
- #45 partial sketch expectations;
- #51 declarative count expectations;
- #52 multiple bodies sharing one name prefix;
- #53 projected/tolerant inspection expectations.

These library changes should be merged separately but released together as the
next verification-library release once the complete first-batch prerequisite
set is green.

## Required proof for each ~10-case Forge batch

- every migrated case replaces procedural `verify_model.py` with data-only
  declarative `verify.py`;
- existing model contract semantics are preserved; incidental SolidCraft fields
  are not promoted into new expectations;
- every case gets the same four independent reference child items as the staged
  proof cases;
- migrated cases become normal processed CAD-CI items;
- no inactive/unrelated case is accidentally selected;
- durable `build/main` gains current model/reference evidence for the batch;
- selection and runtime are measured before starting the next batch;
- a batch that unexpectedly selects the whole remaining catalog is treated as a
  selection defect, not normal build time.

## Execution order

1. Complete lib.py.cad.verification #44, #45, #51, #52 and #53.
2. Release that prerequisite set once and update the immutable SolidCraft
   runtime only if the runtime owns the verification-library pin.
3. Migrate the first ten cases above under #432 and measure selection/runtime.
4. Migrate the next approximately ten remaining cases.
5. Migrate the final remaining catalog cases.
6. #497 — rebuild stable Pages from current source + complete authoritative
   `build/main`, comparing against
   `backup/gh-pages-before-f11-2026-11-20`.
7. #366 — finish remaining Pages preview/cleanup/cut-over lifecycle.
8. Continue independent Forge API/product backlog.
9. #484 runtime/image-distribution optimization may continue independently.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #432 Use released declarative CAD verification in model verification | now | Resume in ~10-case batches; first batch is blocked only on verification-library #44/#45/#51/#52/#53. |
| #497 Publish stable Pages from the generic build/main baseline | blocked | Keep current 32-case site unchanged until current durable evidence again covers the public Qualification catalog. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Durable build storage is already generic; final Pages lifecycle follows #497. |
| #484 Reduce cold SolidCraft runtime overhead without changing model verification semantics | later, non-blocking | Broad 34-target run showed cold image acquisition plus broad selection; keep performance work independent from verification correctness. |
| #391 Extract reusable CAD verification library from Forge | effectively complete but still open | Generic verification ownership is already external; remaining procedural consumer migration is #432. |
| #481 Remove stale Forge development branches | blocked | Current connected tooling cannot safely delete the stale refs. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by the runtime repository/current #484 measurements. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to superseded qualification architecture. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Independent Forge API defect. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | Independent CLI quality work. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Independent product/API work. |
| #354 Support standalone sketch extrusions as boolean operands | later | Independent product/API work. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Independent model/API investigation. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Independent product behavior. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Major Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:

`verification lib #44/#45/#51/#52/#53 -> Forge #432 ~10-case batches -> #497 stable 32-case Pages -> #366 final Pages lifecycle`.
