# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

The procedural-to-declarative Qualification migration is complete.

- all 32 Qualification cases use data-only `verification/verify.py`;
- no procedural `examples/*/verification/verify_model.py` remains;
- released `lib.py.cad.verification 0.14.0` owns all reusable verification
  mechanics needed by the current catalog;
- runtime `v0.3.2` is immutable and green;
- shared SolidCraft/reference runtime batching is proven;
- #432 is complete.

Twenty-six cases are currently `process: true`. Six already-declarative cases
remain staged out:

1. assembly-owned-anchor;
2. corner-anchor;
3. eight-corner-brackets;
4. parametric-anchor;
5. parametric-attach;
6. parametric-offset.

Their declarative model contracts and all four reference `model.py` sources
already exist. They only need activation plus the standard nested reference
child configs.

The current public Pages state remains preserved on
`backup/gh-pages-before-f11-2026-11-20`. Pages must not be cut over until the
complete current 32-case catalog has durable accepted evidence on
`build/main`.

## Current goal

Complete #546: activate the final six already-declarative Qualification cases.

## Required proof for #546

- all 32 model items declare `process: true`;
- all 32 use `template: forge-model-declarative`;
- all 32 have build123d, CadQuery, pyBOSL2 and PythonSCAD child configs;
- the shared SolidCraft/reference runtime batches remain unchanged;
- all 32 model verifications pass in one PR run;
- all 128 independent references pass;
- all CADCraft diagrams pass;
- main publication writes current durable evidence for the complete 32-case
  catalog;
- no Pages cut-over is included.

## Execution order

1. Replace the six staged expanded model configs with the standard declarative
   model template and `process: true`.
2. Add the 24 standard reference child configs.
3. Update process-selection tests to require all 32 cases.
4. Run one complete 32-case PR proof.
5. Merge and prove durable main output for all 32 cases.
6. Audit `build/main` as the authoritative complete catalog input.
7. Continue #497 stable Pages generation/publication.
8. Finish the generic Pages lifecycle in #366.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #546 Activate final six declarative Qualification cases | now | Final step required for complete 32-case durable verification coverage. |
| #497 Publish stable Pages from the generic build/main baseline | blocked | Unblock after #546 proves current durable evidence for all 32 cases. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Final Pages lifecycle follows #497. |
| #391 Extract reusable CAD verification library from Forge | effectively complete but still open | Generic verification ownership and consumer migration are complete; close/clean up separately. |
| #481 Remove stale Forge development branches | blocked | Current connected tooling cannot safely delete stale refs. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by released runtime batching and measured #484 work. |
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

`#546 complete 32-case build/main -> #497 stable Pages -> #366 final Pages lifecycle`.
