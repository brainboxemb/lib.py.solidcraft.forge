# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history; this plan states what is
current and what follows.

## Current documentation structure

Primary documents:

- `docs/api.md`
- `docs/design.md`
- `docs/development.md`
- `docs/plan.md`
- `docs/requirements.md`
- `docs/release.md`

Secondary documentation:

- `docs/manual/` — current task-oriented guidance;
- `docs/background/` — historical/narrow design, changes, research and migration records;
- `docs/agent/` — generated machine-oriented API material.

## Current status

Forge now uses the externally accepted CAD-CI stack:

- `tool.cad.ci` v0.12.1 at exact commit
  `0e7d8a876d95484a4c8870356f3b0ca67e5e493b`;
- released `lib.py.cad.ci` 0.7.1 underneath it.

The adoption run is green.

The staged proof currently keeps exactly five model verification items active:

- `simple-box`
- `anchor-topology-mutation`
- `attach-angle`
- `four-corner-l`
- `xz-anchor`

All five use the declarative CAD-verification path.

A normal CAD-CI run for the v0.12.1 adoption selected eight targets:

- `forge-package`
- `forge-tests`
- `forge-release`
- the five active model verification targets

and did not select `reference-verification`.

Therefore the earlier roughly 156 second run must not be treated as a generic
five-model baseline: that particular change also selected repository-wide
reference verification.

Performance optimization remains deliberately parked. The current task is to
make selection, verification coverage and evidence trustworthy and explainable.

## Current goal

Complete #478 before further verification feature work.

Prove:

1. which CAD-CI items are selected for representative change classes and why;
2. which model set every selected item actually processes;
3. that the five-model staged proof remains exactly five model verifications;
4. when repository-wide reference verification is intentionally selected;
5. that structured CAD-CI evidence is present and sufficient to explain each
   run;
6. which historical Q1-Q6 checks are already represented by the new path and
   which remain intentionally missing pending #430/#378.

Do not optimize Docker/SolidCraft process lifecycle unless reliable evidence
later demonstrates a separate problem.

## Execution order

1. #478: prove selection, scope and structured evidence on the accepted CAD-CI
   stack.
2. Correct Forge selection/configuration only where the proof shows unintended
   work or missing evidence.
3. Record the exact remaining functional gap relative to historical Q1-Q6.
4. Resume #430 only after the CI baseline is trustworthy.
5. Continue the remaining five-model #378 verification stages.
6. Complete #366 durable build/Pages publication.
7. Only then resume #432 for the remaining 21 procedural model verifiers and
   broader catalog activation.
8. Treat performance optimization as a separate measured change only if needed.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #478 Make the SolidCraft CI execution lifecycle measurable and reliable | now | Active CI-stabilization task: prove selection, scope, evidence and functional correspondence before more feature work. |
| #481 Remove stale Forge development branches | blocked | Plan/branch rule is merged; physical deletion of stale refs remains, but current connected tooling cannot delete refs. This does not block CI stabilization. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Feature work waits for #478. |
| #378 Use explicit Forge verification stages instead of integration/native gates | blocked | Parent migration resumes after #478, still limited to the five proof models. |
| #432 Use released declarative CAD verification in model verification | blocked | Eleven models are declarative; 21 still have legacy `verify_model.py`. Broader migration waits for a stable five-model proof. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Publication follows stable verification execution. |
| #391 Extract reusable CAD verification library from Forge | blocked | Close only after remaining procedural catalog verification has migrated through later #432 work. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Independent Forge API defect. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | Independent CLI quality work. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Independent product/API work. |
| #354 Support standalone sketch extrusions as boolean operands | later | Independent product/API work. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to superseded qualification architecture. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Independent model/API investigation. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Do not revive without reliable #478 evidence showing a current performance problem. |
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

`#478 -> #430/#378 five-model proof -> #366 -> resume #432`.
