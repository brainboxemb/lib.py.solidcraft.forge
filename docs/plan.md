# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

The staged F1-F11 verification migration is complete. PR #530 restored the
existing schema-5 qualification semantics from distributed evidence without
reintroducing the retired qualification runner.

All five staged qualification cases now use independent nested reference items:

- `simple-box`;
- `anchor-topology-mutation`;
- `attach-angle`;
- `four-corner-l`;
- `xz-anchor`.

The transitional `verification/references` source item has been removed.
However, the previous CAD-CI release preserved its old row/owned bytes in the
durable `build/main` baseline.

That generic durable-store gap is fixed and externally accepted in:

- `lib.py.cad.ci 0.8.4` at
  `4e033fd17e911b3feb92b1a34433b884ca788ab6`;
- `tool.cad.ci 0.14.2` at
  `4c1016d594368146fb9c16602f01c158e85d9afb`.

The current public Pages state remains preserved exactly on
`backup/gh-pages-before-f11-2026-11-20` at
`127adb3900cdc9ca6194edb1102ea7d505316295` for later presentation comparison.

## Current goal

Complete #534 by adopting exact accepted tool.cad.ci 0.14.2 and proving the
stale `verification/references` durable item is removed from `build/main`.

In the same small change, correct the real missing test dependency:
`scpf/tests/test_qualification_summary.py` imports
`scripts/qualification_summary.py`, so that script must participate in the
existing `forge-tests` watch/input set.

This must remain a small tool/test-scope update. Do not trigger a broad
model/reference rerun merely to clean generated state.

## Required proof

- every Forge CAD-CI workflow/publication pin uses exact accepted tool 0.14.2;
- `forge-tests` watches and hashes `scripts/qualification_summary.py`;
- PR selection remains limited to the intended tool/test scope rather than all
  staged model/reference items;
- Forge tests stay green;
- after merge, normal main durable publication removes
  `verification/references` from `build/main/build.json` and its owned tree;
- all current model/reference child rows remain present;
- no Forge-local durable-store cleanup logic is added.

## Execution order

1. #534 — adopt tool.cad.ci 0.14.2 and clean the stale durable aggregate.
2. #497 — rebuild stable Pages from current source + authoritative
   `build/main`, preserving the existing site in broad outline.
3. #366 — finish remaining Pages preview/cleanup/cut-over lifecycle after stable
   Pages is proven.
4. #432 — resume broader declarative model migration in batches of
   approximately 10 models, checking selection/runtime after each batch.
5. #484 — continue runtime/image-distribution optimization independently.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #534 Adopt tool.cad.ci 0.14.2 and remove stale durable reference aggregate | now | Exact generic fix is released and externally accepted; Forge only needs thin adoption plus the missing qualification-summary test dependency. |
| #497 Publish stable Pages from the generic build/main baseline | blocked | Unblocks once #534 proves build/main contains only current configured items. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Durable build publication is already generic; finish preview/cleanup/cut-over after #497 stable Pages proof. |
| #432 Use released declarative CAD verification in model verification | blocked | Resume after Pages is stable; migrate the remaining catalog in batches of about 10 rather than one model per PR. |
| #484 Reduce cold SolidCraft runtime overhead without changing model verification semantics | later, non-blocking | Broad 34-target run measured ~2m15 CAD graph largely due to intentionally broad selection plus cold image pulls; optimize runtime distribution separately from correctness. |
| #391 Extract reusable CAD verification library from Forge | effectively complete but still open | Generic geometry, visual, SolidCraft and semantic verification already live in the reusable library; remaining consumer migration is tracked by #432. |
| #481 Remove stale Forge development branches | blocked | Current connected tooling cannot delete the stale refs safely. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by the runtime repository/current #484 measurements. |
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

`#534 tool adoption/cleanup -> #497 stable Pages -> #366 final Pages lifecycle -> #432 ~10-model batches; #484 continues independently`.
