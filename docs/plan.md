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

`simple-box` is the first completed visual proof. The next staged step restores the remaining four proof models only; the rest of the catalog remains `process: false`.

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

Continue #378 by applying the proven simple-box visual path to exactly four
remaining staged proof models:

- `anchor-topology-mutation`;
- `attach-angle`;
- `four-corner-l`;
- `xz-anchor`.

Together with `simple-box`, this restores the five-model proof set. No other
catalog model is enabled in this change.

## Required proof

- each of the four models owns visual policy, approved baseline provenance and
  expected-shape data under its own `verification/` directory;
- historical approved regression pixels are preserved exactly as model-local
  encoded baseline payloads and decoded by released
  `lib.py.cad.verification`;
- front/right/iso views produce actual, camera, diff, goal and overlay evidence;
- `four-corner-l` preserves the historical L-arm visual decomposition rather
  than reducing expected shape to outer body bounds;
- the common Forge adapter contains no generic image comparison/projection
  implementation;
- exactly these four items change from `process: false` to `process: true`;
- the five-model staged set is green before any broader catalog expansion.

## Execution order

1. #378 — enable and prove visual evidence for the remaining four staged models.
2. #378 — continue the next explicit verification stages/summary from the
   five-model proof set.
3. #366 / #497 — continue durable output and Pages after verification is stable.
4. #484 — continue runtime/image-distribution optimization independently using
   the retained timing evidence.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Simple-box visual proof is complete; apply the proven path to the remaining four staged proof models only. |
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

`#378 five-model staged proof -> next #378 verification stage -> #366/#497 durable output; #484 continues independently`.
