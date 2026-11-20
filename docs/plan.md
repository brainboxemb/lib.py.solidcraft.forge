# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history; this plan states what is
current and what follows.

## Current status

The CI reliability baseline from #478 is complete.

Forge currently pins externally accepted `tool.cad.ci` v0.12.1 with
`lib.py.cad.ci` 0.7.1.

Released and externally accepted `tool.cad.ci` v0.12.2 at
`8bab91eaf8554533e5f63620421ed9554f66eb91` fixes only reusable workflow
artifact transport when a successful run materializes no `build/` output.

The verified CI baseline report is prepared in #485 / PR #486 but its docs-only
run exposes exactly that v0.12.1 transport defect.

## Current goal

Complete #487:

1. pin exact accepted `tool.cad.ci` v0.12.2;
2. update the exact-pin contract test;
3. prove normal Forge CI;
4. prove docs-only/no-output Forge CI.

Then rerun/merge #486 and continue #366:

```text
main
  -> accepted verified item output
  -> durable build branch
  -> gh-pages
```

## Execution order

1. #487 — adopt exact tool.cad.ci v0.12.2.
2. #485 / PR #486 — land the permanent CI baseline report.
3. #366 — prove one model end to end from verified output to `build`.
4. Extend durable output to migrated Forge/model items.
5. Cut Pages over to the generic CAD-CI publisher.
6. Resume #430/#378 verification-feature work.
7. Resume #432 broader declarative model migration after generated output is stable.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #487 Pin externally accepted tool.cad.ci 0.12.2 artifact transport fix | now | Required to make valid no-output Forge runs succeed without a local workaround. |
| #485 Record the verified Forge CI baseline and parked findings | next | PR #486 is ready after #487 lands and reruns green. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Main CI-development path after the baseline report. |
| #484 Reduce cold SolidCraft runtime overhead without changing model verification semantics | later | Measured and parked; runtime/image follow-up is recorded separately. |
| #481 Remove stale Forge development branches | blocked | Branch rule is merged; physical stale-ref deletion is unavailable through current connected tooling. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | later | Q6 work resumes after durable generated output is stable. |
| #378 Use explicit Forge verification stages instead of integration/native gates | later | Continue the five-model verification stages after #366. |
| #432 Use released declarative CAD verification in model verification | blocked | 21 procedural verifiers remain; broader migration waits for the five-model/generated-output proof. |
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

`#487 -> #485 -> #366 main/build/gh-pages`.
