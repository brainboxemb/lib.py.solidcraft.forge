# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history; this plan states what is
current and what follows.

## Current status

The CI reliability baseline from #478 is complete.

Forge now pins externally accepted `tool.cad.ci` v0.12.2 at exact commit
`8bab91eaf8554533e5f63620421ed9554f66eb91`, with released
`lib.py.cad.ci` 0.7.1 underneath it.

The verified baseline, timing comparison and parked findings are recorded in
`docs/background/ci-baseline-2026-11-20.md`.

Key state:

- exactly five model items are active in the staged proof;
- Q1, Q2 and declarative Q4/Q5 coverage are proven;
- Q6 visual verification remains pending;
- structured CAD-CI evidence is retained;
- valid no-output runs no longer fail artifact transport;
- cold runtime performance is measured and parked in #484 and
  `docker.cad.solidcraft` #4;
- stale branch deletion remains parked in #481.

These parked findings do not block durable generated-output work.

## Current goal

Complete #485 by landing the permanent CI baseline report, then continue #366:

```text
main
  -> accepted verified item output
  -> durable build branch
  -> gh-pages
```

For #366, first prove one model end to end before broadening the cut-over.

## Execution order

1. #485 — merge the permanent CI baseline report.
2. #366 — prove one verified model's accepted output on `build`.
3. Extend the same durable-output mechanism to the migrated Forge/model items.
4. Cut Pages publication over to `tool.cad.ci publish pages`.
5. Remove superseded Forge-owned generated-output/publication code.
6. Resume #430/#378 verification-feature work.
7. Resume #432 broader declarative model migration only after generated output
   is stable.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #485 Record the verified Forge CI baseline and parked findings | now | Documentation-only consolidation of already proven evidence; merge before continuing #366. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Main CI-development path after #485: prove main -> build -> gh-pages with one model first. |
| #484 Reduce cold SolidCraft runtime overhead without changing model verification semantics | later | Measured and parked; runtime/image diagnosis is preserved in the baseline report and docker.cad.solidcraft#4. |
| #481 Remove stale Forge development branches | blocked | Branch rule is merged; physical deletion of stale refs remains unavailable through current connected tooling. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | later | Q6 work resumes after the durable generated-output path is stable. |
| #378 Use explicit Forge verification stages instead of integration/native gates | later | Continue five-model verification stages after #366. |
| #432 Use released declarative CAD verification in model verification | blocked | Eleven models are declarative; 21 retain legacy `verify_model.py`. Broader migration waits for the five-model/generated-output proof. |
| #391 Extract reusable CAD verification library from Forge | blocked | Close only after remaining procedural model verification has migrated through #432. |
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

A development branch exists only while its issue is actively being worked on.
After merge, closure or parking/blocking, remove the branch. Open issues remain
recorded in the issue tracker and this plan; they do not need dormant branches.
Generated `build` and `gh-pages` branches are exceptions.

Immediate chain:

`#485 -> #366 main/build/gh-pages -> #430/#378 -> #432`.
