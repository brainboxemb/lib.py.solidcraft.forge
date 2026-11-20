# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

The staged F1-F11 verification migration is complete. PR #530 restored the
existing schema-5 qualification semantics from distributed evidence without
reintroducing the retired qualification runner.

The authoritative durable main output is already generic CAD-CI build-store
schema 1 on the `build` branch. PR and main publication use released generic
prepare/update/publish commands.

Four staged models now expose four independent nested reference items:

- `simple-box`;
- `anchor-topology-mutation`;
- `attach-angle`;
- `four-corner-l`.

The temporary `verification/references` aggregate now contains only
`xz-anchor`.

The current public Pages state is preserved exactly on
`backup/gh-pages-before-f11-2026-11-20` at
`127adb3900cdc9ca6194edb1102ea7d505316295` for later presentation comparison.

## Current goal

Complete #532 by migrating `xz-anchor` from the temporary aggregate to four
independent nested reference items and then removing the empty aggregate from
Forge configuration.

This is the final staged reference-structure migration. It applies the already
accepted root templates and adds no new verification, CI-selection, runtime or
publication behavior.

## Required proof

- `xz-anchor/build123d` uses `forge-reference-build123d`;
- `xz-anchor/cadquery`, `pythonscad` and `pybosl2` use
  `forge-reference`;
- all four reference items remain model-local and independently represented;
- `verification/references/ci.yml` is removed rather than retained empty;
- root `cad-ci.yml` no longer discovers `verification/references`;
- selected execution contains the four xz-anchor reference children and no
  aggregate reference item;
- durable PR/main publication retains the four nested source paths;
- no generic Forge-local planner, verifier or publisher is added.

## Execution order

1. #532 — migrate `xz-anchor` reference children and remove the aggregate.
2. #497 — rebuild stable Pages from current source + authoritative
   `build/main`, preserving the existing site in broad outline.
3. #366 — finish remaining Pages preview/cleanup/cut-over work after stable
   Pages is proven.
4. #432 — resume broader declarative model migration.
5. #484 — continue runtime/image-distribution optimization independently.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #484 Reduce cold SolidCraft runtime overhead without changing model verification semantics | later, non-blocking | CAD-CI/model work is small; remaining latency is dominated by highly variable GHCR image acquisition. Preserve measurements and optimize runtime distribution separately. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Generic durable PR/main build publication is already active; remaining work is the Pages cut-over/preview lifecycle after stable Pages. |
| #532 Migrate xz-anchor references to isolated CAD-CI items and remove temporary aggregate | now | Final staged reference migration; after this no active proof case depends on the aggregate. |
| #497 Publish stable Pages from the generic build/main baseline | blocked | Durable build/main is ready; wait only for #532 to remove the final temporary reference aggregate. |
| #432 Use released declarative CAD verification in model verification | blocked | Broader model migration waits for completion of the staged five-model verification chain through F11. |
| #391 Extract reusable CAD verification library from Forge | effectively complete but still open | The reusable library exists and owns generic geometry, visual, SolidCraft and semantic verification; remaining procedural model migration is tracked by #432 rather than requiring more extraction architecture. |
| #481 Remove stale Forge development branches | blocked | Current connected tooling cannot delete the stale refs. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by runtime v0.2.0 and current #484 measurements. |
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

`#532 xz-anchor references -> #497 stable Pages -> #366 final Pages lifecycle -> #432 broader model migration; #484 continues independently`.
