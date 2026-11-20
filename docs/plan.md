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

The package-dependency split from #472 and the reusable chat handoff from #476
are merged.

The staged proof currently keeps exactly five model verification items active:

- `simple-box`
- `anchor-topology-mutation`
- `attach-angle`
- `four-corner-l`
- `xz-anchor`

All five already use the declarative CAD-verification path.

The current Forge workflow still pins `tool.cad.ci` v0.11.0, which carries
`lib.py.cad.ci` 0.6.0. The externally accepted current stack is
`tool.cad.ci` v0.12.1 with `lib.py.cad.ci` 0.7.1.

The current five-model run also executes the repository-wide reference target
with `all` models, so its roughly 156 second runtime is not a five-model timing
measurement. Historical evidence shows the old full 32-model reference
verification alone cost roughly two minutes.

Performance optimization is deliberately parked until the selected graph and
its evidence are trustworthy. The immediate problem is CI correctness and
explainability, not proving that Docker or SolidCraft is slow.

## Current goal

First complete #481 and remove stale development branches so repository state is readable again.

Then complete #479: move Forge to exact released `tool.cad.ci` v0.12.1.

Then complete #478 before any further model-verification feature work:

- prove exactly which CAD-CI items are selected and why;
- prove which models each selected item processes;
- remove unintended all-catalog work from the five-model proof where necessary;
- produce trustworthy per-item/per-model timing evidence;
- compare the new verification coverage with the historical Q1-Q6 coverage;
- record Docker/container/SolidCraft process counts as evidence, without
  optimizing them unless measurement shows a real problem.

## Execution order

1. #481: remove stale inactive development branches; keep only active work plus generated branches.
2. #479: pin exact accepted CAD-CI v0.12.1 and prove Forge CI on that stack.
3. #478: establish a correct, explainable selected graph and trustworthy
   evidence/timing baseline.
4. Correct staged selection if the five-model proof performs unrelated
   all-catalog work.
5. Park runtime/process optimization unless the reliable baseline proves it is
   needed.
6. Resume #430 only after #478 is proven.
7. Continue the remaining five-model #378 verification stages.
8. Complete #366 durable build/Pages publication.
9. Only then resume #432 for broader catalog migration.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #481 Remove stale Forge development branches | now | Repository hygiene: remove inactive branches from closed/superseded work and blocked issues; only create a branch when work actually starts. |
| #479 Update Forge to the externally accepted tool.cad.ci 0.12.1 stack | next | Prerequisite for trustworthy timing evidence and #478. |
| #478 Make the SolidCraft CI execution lifecycle measurable and reliable | blocked | Starts immediately after #479; first prove selection, coverage and evidence. Performance optimization is parked unless reliable measurements justify it. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Feature work paused until #478 establishes a controlled execution lifecycle. |
| #378 Use explicit Forge verification stages instead of integration/native gates | blocked | Parent migration resumes after #478, still limited to the five proof models. |
| #432 Use released declarative CAD verification in model verification | blocked | Five proof models are already declarative; broader catalog migration waits for the full five-model proof/publication path. |
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
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded in form by the released runtime; any remaining performance problem is handled from measured #478 evidence. |
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

`#481 -> #479 -> #478 -> #430/#378 five-model proof -> #366 -> resume #432`.
