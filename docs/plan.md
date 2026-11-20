# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

The generic CAD-CI stack currently accepted for Forge PR migration is:

- `lib.py.cad.ci` 0.8.3 at
  `e8e951ed7e50c4fa754cc158729faf2927cccb31`;
- `tool.cad.ci` 0.14.0 at
  `5bca68eb109a69e3a05e7711daf394926ee0e7d4`;
- external `tool.cad.ci.test` acceptance is green for the one-runner
  `reusable-pr.yml` contract.

`docker.cad.solidcraft` v0.2.0 remains the immutable runtime split:

- `ghcr.io/brainboxemb/cad-solidcraft:v0.2.0`;
- `ghcr.io/brainboxemb/cad-reference:v0.2.0`.

Only `simple-box` remains `process: true` as a model-verification item.

Representative PR #517 on the old split PR architecture took about 55 seconds
end-to-end:

- first CAD-CI runner: about 38 seconds;
- second publication runner: about 15 seconds.

Inside `simple-box:model_verify`, model/verification work itself is small; the
cold path is dominated by SolidCraft image acquisition/container startup.

## Current goal

Complete #518 by replacing Forge's split PR path with the externally accepted
single-runner `reusable-pr.yml` flow.

After that architecture is merged, create one disposable simple-box-only PR and
measure the complete PR event from start to green against the <=30 second goal.

## Required proof

- one Forge PR job calls exact tool.cad.ci 0.14.0 `reusable-pr.yml`;
- no Forge-owned PR artifact handoff remains;
- no Forge-owned second PR publication runner remains;
- close-only PR events use the same reusable workflow cleanup path;
- the main/push flow is unchanged by #518;
- a disposable simple-box-only PR selects exactly the expected one-model graph;
- end-to-end PR timing is recorded from GitHub Actions;
- no verification semantics are weakened for timing.

## Execution order

1. #518 — migrate the Forge PR workflow to one runner.
2. Merge #518 after the new PR workflow itself is green.
3. Create one disposable simple-box-only measurement PR.
4. Compare end-to-end time with the <=30 second target.
5. Update/close #484 only after that measured result is recorded.
6. #430 / #378 — continue visual and staged verification on simple-box.
7. #366 / #497 — continue main/Pages work after the PR path is stable.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #518 Use tool.cad.ci 0.14.0 single-runner PR workflow | now | Removes the known second-runner/artifact overhead and establishes the production PR architecture before the next timing proof. |
| #484 Reduce cold SolidCraft runtime overhead without changing model verification semantics | blocked | Runtime split is proven; final status depends on the one-runner simple-box end-to-end measurement after #518. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | next | Continue after the PR performance path is stable. |
| #378 Use explicit Forge verification stages instead of integration/native gates | next | Continue through simple-box only after the timing proof. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Main/Pages continuation waits for the PR path measurement. |
| #497 Publish stable Pages from the generic build/main baseline | blocked | Depends on stable durable generated output. |
| #432 Use released declarative CAD verification in model verification | blocked | Broader catalog migration waits for simple-box stability. |
| #391 Extract reusable CAD verification library from Forge | blocked | Complete only after procedural verification is migrated. |
| #481 Remove stale Forge development branches | blocked | Current connected tooling cannot delete the stale refs. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by docker.cad.solidcraft v0.2.0 and #484/#518. |
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

`#518 single-runner PR -> disposable simple-box timing -> #484 decision -> #430/#378`.
