# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history; this plan states what is
current and what follows.

## Current status

The CI reliability baseline from #478 is complete and recorded in
`docs/background/ci-baseline-2026-11-20.md`.

Forge uses externally accepted `tool.cad.ci` v0.12.2 at exact commit
`8bab91eaf8554533e5f63620421ed9554f66eb91`, with released
`lib.py.cad.ci` 0.7.1 underneath it.

Exactly five model verification items are active in the staged proof.
Structured CAD-CI output/evidence is retained as the reusable workflow build
artifact when materialized output exists.

The performance/runtime and stale-branch findings remain parked and do not
block generated-output migration.

## Current goal

Complete #489 as the first concrete part of #366.

Prove one sparse PR durable-build scope:

```text
simple-box verification
  -> reusable CAD-CI build artifact
  -> cad-ci build prepare-pr
  -> cad-ci publish build
  -> build/pr/<PR>/examples/simple-box/
```

This issue does not publish stable `build/main` and does not touch
`gh-pages`.

## Execution order

1. #489 — prove `simple-box` as one durable PR scope on `build`.
2. #366 — extend the proven mechanism to stable/main build output.
3. Extend durable build publication to the migrated active items.
4. Cut Pages publication over to `cad-ci publish pages`.
5. Remove superseded Forge-owned publication code.
6. Resume #430/#378 verification-feature work.
7. Resume #432 broader declarative model migration after generated output is
   stable.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #489 Prove simple-box verified output as a durable build PR scope | now | First #366 proof. Publish only accepted simple-box output to one sparse PR scope on `build`. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Umbrella generated-output migration; stable/main and Pages follow the #489 proof. |
| #484 Reduce cold SolidCraft runtime overhead without changing model verification semantics | later | Measured and parked; runtime/image follow-up is separate. |
| #481 Remove stale Forge development branches | blocked | Branch rule is merged; physical deletion of stale refs remains unavailable through current connected tooling. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | later | Q6 work resumes after durable generated output is stable. |
| #378 Use explicit Forge verification stages instead of integration/native gates | later | Continue five-model verification stages after #366. |
| #432 Use released declarative CAD verification in model verification | blocked | Eleven models are declarative; 21 retain legacy `verify_model.py`. Broader migration waits for stable generated output. |
| #391 Extract reusable CAD verification library from Forge | blocked | Close only after remaining procedural verification has migrated through #432. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by measured #484/runtime-repository work. |
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

## Branch hygiene

Development branches should exist only while their issue is actively worked on.
Generated `build` and `gh-pages` are exceptions.

Immediate chain:

`#489 simple-box PR build -> #366 build/main -> gh-pages`.
