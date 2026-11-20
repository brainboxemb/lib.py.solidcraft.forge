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

Complete #538 before starting #537 batch 1.

The runtime/package boundary is corrected as follows:

- docker.cad.solidcraft v0.3.1 removes lib.py.cad.verification from both role
  images;
- Forge owns one CAD-CI dependency item, cad-verification-package;
- that item prepares exactly one wheel from released
  lib.py.cad.verification 0.12.0 at
  1254eca6681faaff62b9605fbb5a25178ab71f9a;
- model verification consumes forge-package + cad-verification-package;
- reference verification consumes cad-verification-package;
- both runtime containers receive the verification wheel read-only through
  PYTHONPATH.

This decouples verification-library releases and model-local verify.py changes
from Docker runtime releases.

## Required proof for #538

- the verification package item builds/prepares one wheel only once per selected
  graph;
- the resulting wheel metadata reports version 0.12.0;
- staged five declarative model items pass against cad-solidcraft v0.3.1, which
  contains no cad_verification package;
- staged reference children pass against cad-reference v0.3.1, which likewise
  contains no cad_verification package;
- CAD-CI evidence shows normal dependency ownership rather than per-model wheel
  downloads;
- no verification implementation is copied into Forge.

## Required proof for each ~10-case Forge batch

- every migrated case replaces procedural verify_model.py with data-only
  declarative verify.py;
- existing model contract semantics are preserved; incidental SolidCraft fields
  are not promoted into new expectations;
- every case gets the same four independent reference child items as the staged
  proof cases;
- migrated cases become normal processed CAD-CI items;
- no inactive/unrelated case is accidentally selected;
- durable build/main gains current model/reference evidence for the batch;
- selection and runtime are measured before starting the next batch;
- a batch that unexpectedly selects the whole remaining catalog is treated as a
  selection defect, not normal build time.

## Execution order

1. #12 in docker.cad.solidcraft — release v0.3.1 without embedded
   cad_verification.
2. #538 — add the separate verification-wheel CAD-CI dependency and prove the
   existing staged five model/reference paths against v0.3.1.
3. #537 — migrate the first ten Qualification cases and measure
   selection/runtime.
4. Migrate the next approximately ten remaining cases.
5. Migrate the final remaining catalog cases.
6. #497 — rebuild stable Pages from current source + complete authoritative
   build/main, comparing against
   backup/gh-pages-before-f11-2026-11-20.
7. #366 — finish remaining Pages preview/cleanup/cut-over lifecycle.
8. Continue independent Forge API/product backlog.
9. #484 runtime/image-distribution optimization may continue independently.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #538 Supply released CAD verification as a CI dependency wheel | now | Correct verification/runtime dependency boundary before expanding the catalog. |
| #537 Migrate first post-proof Qualification batch to declarative verification | blocked | Batch contract audit is complete; waits for #538 and runtime v0.3.1. |
| #432 Use released declarative CAD verification in model verification | now | Parent migration issue; execute through ~10-case batch issues beginning with #537. |
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

`runtime v0.3.1 -> #538 verification-wheel dependency -> #537 first 10-case batch -> remaining ~10-case batches -> #497 stable 32-case Pages -> #366 final Pages lifecycle`.
