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

Complete #537: migrate the first post-proof Qualification batch of ten existing
cases to the released declarative verification path.

The runtime/package boundary is already proven by #538:

- docker.cad.solidcraft v0.3.1 contains no cad_verification package;
- cad-verification-package supplies released lib.py.cad.verification 0.12.0 at
  exact commit 1254eca6681faaff62b9605fbb5a25178ab71f9a;
- model/reference consumers receive that wheel through normal CAD-CI needs
  edges.

Batch 1 contains exactly:

1. anchored-holes;
2. hole-family;
3. sheet-fold;
4. top-sketch-after-chamfer;
5. parameter-scope;
6. parent-derived-child-size;
7. components;
8. repeated-parent-attachments;
9. assembly-decorator;
10. group-hierarchy.

Migration preserves each existing procedural VerificationCheck contract. Shared
helper functions in verify_model.py are not requirements unless a listed check
uses them.

Saved-design mutation remains model-specific:

- required: parameter-scope, parent-derived-child-size,
  repeated-parent-attachments;
- not required: the other seven batch cases.

## Required proof for #537

- all ten cases use data-only verification/verify.py;
- no verification/verify_model.py remains for those ten;
- existing expected geometry/parameters/timeline/sketch/inspection semantics are
  preserved without promoting incidental SolidCraft fields into policy;
- all ten model items use the proven declarative model template/path;
- all ten have four independent nested reference child items;
- the batch selects only these ten cases plus true dependencies, not the
  remaining catalog;
- every model/reference result is PASS;
- durable build/main gains current evidence for exactly this batch;
- selection and timing are recorded before the next batch;
- Pages remains unchanged.

## Execution order

1. Read and map all ten current procedural contracts.
2. Replace each with the smallest equivalent declarative definition.
3. Add four reference child configs per case and enable normal processing.
4. Run one PR proof for the complete ten-case batch.
5. Correct only demonstrated contract/mapping errors; do not add broad policy.
6. Merge and prove durable main output for the batch.
7. Record selection/runtime and define the next approximately ten-case batch.
8. Continue remaining catalog batches before #497 Pages.
## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #537 Migrate first post-proof Qualification batch to declarative verification | now | Runtime/wheel boundary is proven; migrate exactly the first ten current Qualification cases while preserving procedural semantics. |
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

`#537 first 10-case batch -> remaining ~10-case batches -> #497 stable 32-case Pages -> #366 final Pages lifecycle`.
