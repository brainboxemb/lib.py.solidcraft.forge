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

F7-F10 are complete for the staged verification proof. `simple-box` remains only the representative pipeline/example fixture used to prove the infrastructure. The staged verification models are `anchor-topology-mutation`, `attach-angle`, `four-corner-l` and `xz-anchor`. The rest of the model catalog remains `process: false` while F11 summary composition is completed.

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

Continue #378 with F11: compose semantic verification summaries from already-produced evidence without adding a second verification engine or rerunning CAD inside the summary code.

Released `lib.py.cad.verification` already owns generic semantic status composition through `SemanticCheck`, `compose_semantic_result()` and `compose_item_results()`. Forge owns only the semantic check names, required/optional policy, model-to-evidence mapping and the thin summary consumer.

## Required proof

- Forge defines the F11 semantic policy before implementation in `docs/requirements.md` and `docs/design.md`;
- the summary code executes no Forge compilation, SolidCraft, reference CAD or image comparison;
- model summaries use the semantic checks `native_model`, `geometry`, `saved_design`, `visual` and `reference`;
- `saved_design` is `not-required` when a model has no saved-design mutation;
- required failed/missing/review/blocked evidence remains distinguishable;
- evidence references are preserved;
- the staged verification aggregate contains each of the four active verification models exactly once and excludes `simple-box` as a presentation/verification result;
- CAD-CI fan-in selection must not accidentally turn an incremental model change into a cold rerun of every sibling model/reference item.

## Execution order

1. #378 — define F11 evidence inputs, semantic mapping and CAD-CI selection behavior.
2. #378 — implement/test the thin summary consumer against existing evidence.
3. #378 — run the staged five-model F11 proof.
4. #366 / #497 — continue durable output and Pages after F11 is green.
5. #432 — resume broader declarative model migration after the five-model proof chain is complete.
6. #484 — continue runtime/image-distribution optimization independently.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | F7-F10 are green for the staged proof; `simple-box` is infrastructure/example proof only. Define F11 for the four staged verification models without re-running sibling CAD work. |
| #484 Reduce cold SolidCraft runtime overhead without changing model verification semantics | later, non-blocking | CAD-CI/model work is small; remaining latency is dominated by highly variable GHCR image acquisition. Preserve measurements and optimize runtime distribution separately. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Continue after #378 F11 is green so durable presentation consumes the completed verification evidence model. |
| #497 Publish stable Pages from the generic build/main baseline | blocked | Depends on stable durable generated output. |
| #432 Use released declarative CAD verification in model verification | blocked | Broader model migration waits for completion of the staged five-model verification chain through F11. |
| #391 Extract reusable CAD verification library from Forge | effectively complete but still open | The reusable library exists and owns generic geometry, visual, SolidCraft and semantic verification; remaining procedural model migration is tracked by #432 rather than requiring more extraction architecture. |
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

`#378 F11 semantic summary -> #366/#497 durable output -> #432 broader model migration; #484 continues independently`.
