# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history; this plan states what is
current and what follows.

## Current status

Forge uses externally accepted `tool.cad.ci` v0.12.3 at exact commit
`ad7099b4712af13067c1c42ad50e89bf6a8306dd`, with released
`lib.py.cad.ci` 0.7.1 underneath it.

#489 proved sparse PR durable-build publication for `simple-box`.

The generated `build` branch now has a current generic PR scope, while
`build/main` still contains the retired Forge-owned publication format.

The generic tool can now prepare a complete main candidate from exactly the
current `process: true` item set.

## Current goal

Complete #493 as the stable-main bootstrap:

```text
push main
  -> full processed CAD-CI run
  -> complete accepted build artifact
  -> cad-ci build prepare-main
  -> cad-ci publish build --scope main
  -> authoritative generic build/main
```

PR behavior remains incremental and keeps the already proven sparse PR path.

## Execution order

1. #493 — replace retired `build/main` with one generic complete baseline.
2. #366 — switch future main publications from bootstrap/full replacement to
   partial `update-main`.
3. Extend durable publication to all migrated active items as needed.
4. Cut Pages publication over to `cad-ci publish pages`.
5. Remove superseded Forge-owned publication code.
6. Resume #430/#378 verification-feature work.
7. Resume #432 broader declarative model migration after generated output is
   stable.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #493 Bootstrap the authoritative generic build/main baseline | now | Direct #366 step. Replace the incompatible retired main scope atomically from a complete processed run. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | PR scope is proven; partial stable-main updates and Pages follow the bootstrap. |
| #484 Reduce cold SolidCraft runtime overhead without changing model verification semantics | later | Measured and parked; runtime/image follow-up remains separate. |
| #481 Remove stale Forge development branches | blocked | Branch rule is merged; physical deletion of stale refs remains unavailable through current connected tooling. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | later | Q6 resumes after generated output is stable. |
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

Immediate chain:

`#493 build/main bootstrap -> #366 partial main -> gh-pages`.
