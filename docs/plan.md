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

Complete #484 by removing per-case CAD runtime startup from verification while
preserving the existing per-case CAD-CI items and durable evidence paths.

#537 is complete and merged. Its ten-case proof exposed the runtime regression:
the correct 10-model/40-reference selection took about 3m28 because each
reference child started a fresh container/runtime.

A controlled build123d experiment using the exact released
`cad-reference:v0.3.1` image measured:

- ten separate runtime starts: 37.686 s;
- one shared runtime for the same ten cases: 3.535 s;
- speedup: 10.66x.

The required execution rule is now explicit: CAD-CI selects logical items, but
Forge verification performs expensive CAD work in shared batches and then
materializes each case's existing result/evidence separately.

## Required proof for #484

- one SolidCraft runtime processes the current declarative model batch;
- one reference runtime processes the current reference batch;
- build123d is imported once for its complete case list;
- CadQuery, PythonSCAD and pyBOSL2 process their complete lists in the shared
  reference process;
- CADCraft runs inside the same released heavy reference runtime and processes
  the complete diagram list without fail-fast behavior;
- a failing case does not prevent later cases in the same batch from running;
- existing per-model and per-reference output/evidence paths remain unchanged;
- no generic scheduling/batching is added to lib.py.cad.ci;
- the current ten-case workload is remeasured before further migration.

## Execution order

1. Add Forge-owned model/reference batch items as dependencies of the existing
   per-case verification items.
2. Make the batch runners continue through all cases and report failures after
   the complete list.
3. Keep per-case items lightweight: copy/materialize only their own batch result.
4. Consume released `cad-reference:v0.3.2`, which owns CADCraft 0.20.1, and
   run diagram rendering inside the same heavy reference container.
5. Run the representative ten-case verification workload and record timing.
6. Continue the remaining Qualification migration only after the batch proof is
   green and materially faster.
## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #432 Use released declarative CAD verification in model verification | blocked | #537 is merged; continue the remaining model batches only after #484 removes the demonstrated runtime-start regression. |
| #497 Publish stable Pages from the generic build/main baseline | blocked | Keep current 32-case site unchanged until current durable evidence again covers the public Qualification catalog. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Durable build storage is already generic; final Pages lifecycle follows #497. |
| #484 Reduce cold SolidCraft runtime overhead without changing model verification semantics | now | The 10-case proof is functionally correct but ~3m28; build123d experiment proves 10.66x runtime-reuse gain. Batch all expensive verification runtimes before further migration. |
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

`#484 verification batching -> remaining ~10-case batches -> #497 stable 32-case Pages -> #366 final Pages lifecycle`.
