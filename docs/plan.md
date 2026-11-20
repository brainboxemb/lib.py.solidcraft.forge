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

Issue #472 is implemented in PR #475.

At this snapshot:

- PR #475 is open, mergeable and its Forge workflow is green;
- the package/test/release split uses existing CAD-CI dependency outputs;
- `forge-package` builds the wheel once;
- `forge-tests`, `forge-release` and model verification consume that package
  independently;
- the staged proof still processes exactly five model verification items:
  `simple-box`, `anchor-topology-mutation`, `attach-angle`,
  `four-corner-l` and `xz-anchor`.

Issue #476 is a documentation-only task to keep one ready-to-copy central-CI
chat handoff under `docs/manual/`. That handoff is not a second source of
truth and must always direct a new chat back to the live repository state and
this plan.

## Current goal

1. Finish #476 as a small documentation-only PR.
2. Merge #475 when its current green state is still valid.
3. Measure the resulting five-model run before opening or implementing any
   further performance change.
4. Continue the staged declarative/visual verification chain under
   #432/#430/#378.
5. Continue durable build/Pages publication under #366 after the verification
   stages are stable.

## Execution order

1. Keep #476 limited to the copyable chat handoff and manual index.
2. Recheck PR #475 before merge; do not treat this plan snapshot as a substitute
   for current PR status.
3. After #475 lands, update this plan and close #472.
4. Compare timing evidence for the five-model run. If repeated Docker/SolidCraft
   startup is still the dominant cost, create a separate issue before changing
   execution behavior.
5. Continue #432 with the released `lib.py.cad.verification` boundary.
6. Use #430/#378 for the remaining simple-box visual/verification-stage proof.
7. Complete #366 only after the verification path is stable.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #476 Add reusable central CI handoff bootstrap document | now | Documentation-only task requested for copy/paste into future chats; must stay subordinate to live repository state and `docs/plan.md`. |
| #472 Make model verification depend only on the Forge package build | effectively complete but still open | Implemented by green PR #475; merge and post-merge plan update remain. |
| #432 Use released declarative CAD verification in model verification | next | Continue the five-model verification migration after #472 is merged. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Resume after #472 is merged and the package/model dependency structure is stable. |
| #391 Extract reusable CAD verification library from Forge | blocked | Close only after remaining shared checker ownership has left Forge through #432. |
| #378 Use explicit Forge verification stages instead of integration/native gates | next | Umbrella migration after #472/#432; continue with the staged five-model proof. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Publication follows the remaining five-model verification stages. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Independent Forge API defect. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | Independent CLI quality work. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Independent product/API work. |
| #354 Support standalone sketch extrusions as boolean operands | later | Independent product/API work. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to superseded qualification architecture. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Independent model/API investigation. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Predates the released Docker runtime and current CAD-CI architecture. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Independent product behavior. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Major Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:

`#476 documentation -> merge #475/#472 -> five-model #432/#430/#378 -> #366`.
