# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

The current 32-case Qualification catalog is fully declarative, active and
durable.

- all 32 examples use data-only `verification/verify.py`;
- all 32 are `process: true`;
- all 32 have four independent reference child items;
- #548 is complete on main commit `21c10dea1b7a274e132615d3e032e1d67f6555cd`;
- the corresponding main CAD-CI run and durable `build/main` publication are
  green;
- durable `build/main` contains 32/32 current `model_verify` outputs;
- example/page source ownership is now local to `model.yml`, `README.md`,
  `verification/verify.py` and external site templates.

One source-quality defect remains before stable Pages cut-over:
`examples/bracket/README.md` still contains stale prose for an older bracket
implementation above the current Minimal L-profile documentation.

The current public Pages state remains preserved on
`backup/gh-pages-before-f11-2026-11-20`.

## Current goal

Complete #554: make the bracket README describe only the current Minimal
L-profile while preserving the canonical engineering statements migrated by
#548.

## Required proof for #554

- no stale claim remains about fillets, mounting holes or the older bracket
  implementation;
- title, parameters and stages agree with the current `model.yml`;
- Goal / Forge API / Forge model / lowering / SolidCraft result / saved-design
  text / geometry rationale / reference notes remain unchanged from the
  canonical pre-removal qualification sources;
- model geometry and verification behavior do not change;
- site-source tests remain green.

## Execution order

1. Fix #554 as a source-content correction only.
2. Re-read the plan after merge.
3. Continue #497: generate stable Pages from current source + durable
   `build/main`, preserving content parity and durable evidence links.
4. Finish generic Pages publication/lifecycle in #366.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #554 Fix stale pre-migration content in bracket example README | now | Current bracket README contradicts the active Minimal L-profile model; fix source content before Pages consumes it. |
| #497 Publish stable Pages from the generic build/main baseline | blocked | #548 is complete; wait only for #554 source correction, then generate stable Pages from current source + 32-case build/main. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Final generic Pages publication lifecycle follows #497. |
| #391 Extract reusable CAD verification library from Forge | effectively complete but still open | Generic verification ownership and consumer migration are complete; cleanup/close separately. |
| #481 Remove stale Forge development branches | blocked | Current connected tooling cannot safely delete stale refs. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by v0.3.2 runtime batching and measured #484 work. |
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

`#554 bracket README correction -> #497 stable Pages -> #366 final Pages lifecycle`.
