# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

The production PR architecture is now one runner:

`CAD-CI run -> prepare-pr -> publish`

Released/accepted CAD-CI stack for the next measurement:

- `lib.py.cad.ci` 0.8.3 at
  `e8e951ed7e50c4fa754cc158729faf2927cccb31`;
- `tool.cad.ci` 0.14.1 at
  `18812d38e2390c23fd3c431cfde2ce9367bdfd40`;
- external `tool.cad.ci.test` acceptance is green.

`docker.cad.solidcraft` v0.2.0 remains unchanged:

- `ghcr.io/brainboxemb/cad-solidcraft:v0.2.0`;
- `ghcr.io/brainboxemb/cad-reference:v0.2.0`.

Only `simple-box` is active as a model-verification item.

The clean one-file measurement on tool.cad.ci 0.14.0 was PR #520 / run
44766489422:

- end-to-end workflow: 41 s;
- one real PR job: 38 s;
- exact graph: forge-package, simple-box contract_test, simple-box model_verify;
- image pull: 7.515 s;
- container start to entry shell: 8.079 s;
- actual in-runtime work: 0.564 s;
- publication: about 2.5 s.

Measured fixed bootstrap before CAD-CI included about 3.7 s full caller checkout,
3.1 s external dependency install and 1.8 s docker/login-action.

tool.cad.ci 0.14.1 specifically removes/reduces those fixed bootstrap costs by
using shallow head + exact base fetch, direct Docker CLI GHCR login and a
lighter external dependency install.

## Current goal

Continue #484 by adopting exact tool.cad.ci 0.14.1 for PRs and repeating the
same one-file simple-box measurement against the <=30 second target.

No model verification semantics may change for this measurement.

## Required proof

- Forge PR workflow pins exact accepted 0.14.1;
- main/push workflow remains unchanged;
- the PR workflow contract test pins the same PR tool commit;
- a disposable model.yml-only PR selects exactly forge-package + simple-box;
- record event start, job duration, bootstrap timing, image pull, container
  start and publication timing;
- if still above 30 s, optimize only the newly measured remaining bottleneck.

## Execution order

1. Adopt exact tool.cad.ci 0.14.1 PR pin.
2. Merge after Forge CI is green.
3. Create the same one-line model.yml measurement PR.
4. Record end-to-end result against <=30 s.
5. If still above target, continue #484 with the measured SolidCraft runtime
   critical path.
6. Only after the performance path is stable resume #430/#378 and main/Pages.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #484 Reduce cold SolidCraft runtime overhead without changing model verification semantics | now | 41 s single-runner baseline is proven; adopt accepted 0.14.1 bootstrap optimization and remeasure before changing runtime. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | next | Continue after PR timing reaches/stabilizes near target. |
| #378 Use explicit Forge verification stages instead of integration/native gates | next | Continue through simple-box after performance stabilization. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Main/Pages continuation waits for PR performance path. |
| #497 Publish stable Pages from the generic build/main baseline | blocked | Depends on stable durable generated output. |
| #432 Use released declarative CAD verification in model verification | blocked | Broader model migration waits for simple-box stability. |
| #391 Extract reusable CAD verification library from Forge | blocked | Complete only after procedural verification migration. |
| #481 Remove stale Forge development branches | blocked | Current connected tooling cannot delete the stale refs. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by runtime v0.2.0 and current #484 measurements. |
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

`0.14.1 PR pin -> simple-box timing -> remaining #484 bottleneck`.
