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

Repeated clean one-file measurements show that the remaining PR latency is
dominated by external SolidCraft runtime acquisition rather than CAD-CI or model
work:

| tool.cad.ci | run | end-to-end | image pull | container start | in-runtime |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.14.0 | 44766489422 | 41 s | 7.515 s | 8.079 s | 0.564 s |
| 0.14.1 | 44768874847 | 46 s | 13.307 s | 7.480 s | 0.747 s |
| 0.14.1 | 44769675996 | 80 s | 54.123 s | 3.365 s | 0.855 s |

Every run selected exactly forge-package + simple-box contract/model verification.
No Forge unit/release/reference work participated.

The non-image-download path is roughly in the 26-33 s engineering range. The
<=30 s end-to-end target is therefore not reliable yet because cold GHCR image
acquisition is highly variable. #484 remains open as a runtime/distribution
performance follow-up, but it no longer blocks verification-chain migration.

## Current goal

Resume the functional verification chain with #430 / #378 on simple-box while
preserving the current measured performance evidence.

No verification semantics may be weakened for performance.

## Required proof

- Forge PR workflow pins exact accepted 0.14.1;
- main/push workflow remains unchanged;
- the PR workflow contract test pins the same PR tool commit;
- a disposable model.yml-only PR selects exactly forge-package + simple-box;
- record event start, job duration, bootstrap timing, image pull, container
  start and publication timing;
- if still above 30 s, optimize only the newly measured remaining bottleneck.

## Execution order

1. #430 — complete simple-box visual render/regression/expected-shape proof.
2. #378 — continue explicit verification stages from the proven simple-box path.
3. #366 / #497 — continue durable output and Pages after verification is stable.
4. #484 — continue runtime/image-distribution optimization independently from
   the functional chain, using the retained timing evidence.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | now | Next functional proof; keep generic visual mechanics in released lib.py.cad.verification. |
| #378 Use explicit Forge verification stages instead of integration/native gates | next | Continue from the proven simple-box visual path. |
| #484 Reduce cold SolidCraft runtime overhead without changing model verification semantics | later, non-blocking | CAD-CI/model work is small; remaining latency is dominated by highly variable GHCR image acquisition. Preserve measurements and optimize runtime distribution separately. |
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

`#430 simple-box visual proof -> #378 staged verification -> #366/#497 durable output; #484 continues independently`.
