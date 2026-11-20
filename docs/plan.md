# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

Forge is migrating this pilot to the current externally accepted generic stack:

- `lib.py.cad.ci` 0.8.3;
- `tool.cad.ci` 0.13.3 commit
  `bbdd473638d64e01acab69722092b2a12f99b84d`;
- `tool.cad.ci.test` acceptance is green for fresh cacheless Git-diff
  selection, nested item paths, parent-relative shared inputs, nested durable
  parent/child publication and streamed concise execution logging.

Forge durable build publication already uses affected-item PR/main updates.
The remaining reference-verification configuration is still too coarse:
`verification/references` processes all reference implementations together.

## Current goal

Complete #508 by migrating `anchor-topology-mutation` from the temporary
aggregate to four independent nested reference items.

The attach-angle and simple-box migrations are complete. The generic stack and
nested-item behavior are already proven; this change applies that accepted
structure to the next active model.

Target structure:

```text
examples/anchor-topology-mutation/
  build123d/ci.yml
  cadquery/ci.yml
  pythonscad/ci.yml
  pybosl2/ci.yml
```

The temporary aggregate must stop watching and executing
`anchor-topology-mutation` in the same change, leaving only:

- `four-corner-l`;
- `xz-anchor`.

## Required proof

- all four anchor-topology-mutation reference children are represented independently;
- build123d uses `forge-reference-build123d`;
- cadquery, pythonscad and pybosl2 use `forge-reference`;
- reference expectations remain model-local;
- the temporary aggregate covers only the remaining two active models;
- inactive `process: false` references remain excluded;
- selected execution and durable affected-item publication remain green.

## Execution order

1. #508 — migrate anchor-topology-mutation reference children.
2. Migrate `four-corner-l` references in a separate issue/PR.
3. Migrate `xz-anchor` references in a separate issue/PR and remove the
   temporary aggregate.
4. #497 / #366 — resume stable Pages publication from the generic build/main
   baseline.
5. Resume #430/#378 verification-feature work.
6. Resume #432 broader declarative model migration after generated output is
   stable.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #508 Migrate anchor-topology-mutation references to isolated CAD-CI items | now | Next active-model migration after completed attach-angle and simple-box reference splits. |
| #497 Publish stable Pages from the generic build/main baseline | blocked | Resume after the reference-item pilot proves the corrected CI structure. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Durable affected build updates are in place; Pages remains. |
| #484 Reduce cold SolidCraft runtime overhead without changing model verification semantics | later | Performance work stays separate from selection/reference structure. |
| #481 Remove stale Forge development branches | blocked | Current connected tooling cannot delete the stale refs. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | later | Resume after generated output and reference selection are stable. |
| #378 Use explicit Forge verification stages instead of integration/native gates | later | Continue verification-stage work after the CI structure is stable. |
| #432 Use released declarative CAD verification in model verification | blocked | Broader migration follows stable generated output/reference selection. |
| #391 Extract reusable CAD verification library from Forge | blocked | Complete only after procedural verification is migrated. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by runtime repository and #484. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to the superseded qualification architecture. |
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

`#508 anchor-topology-mutation -> four-corner-l -> xz-anchor -> #497/#366 Pages`.
