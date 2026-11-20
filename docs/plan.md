# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Complete #465: make Forge a consumer of the released
`docker.cad.solidcraft` runtime and remove runtime packaging/publication from
this repository.

The external runtime repository is preparing its initial release:

```text
ghcr.io/brainboxemb/cad-solidcraft:v0.1.0
```

Do not change Forge's runtime reference until that immutable release exists and
has passed its own build/smoke tests.

## Execution order

1. Complete `docker.cad.solidcraft` v0.1.0 release.
2. In #465:
   - update `cad-ci.yml` to
     `ghcr.io/brainboxemb/cad-solidcraft:v0.1.0`;
   - prove the normal Forge CAD-CI graph against that image;
   - remove `docker/solidcraft_runtime/**`;
   - remove `.github/workflows/solidcraft-runtime.yml`;
   - remove Forge-owned runtime build/publication helper code and tests;
   - keep only consumer-side runtime selection and SolidCraft compatibility
     checks.
3. Merge #465 only after Forge CI is green against the external release.
4. Resume #460: migrate the first ten model verifiers using
   `verification/verify.py`.
5. Continue #432 through reviewable batches.
6. Add/release missing generic verification semantics in
   `lib.py.cad.verfication` before models that need them.
7. Resume #430, then #378 and #366.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #465 Consume released docker.cad.solidcraft runtime | now | Runtime ownership migration; blocked only until external v0.1.0 is published. |
| #460 Migrate first ten model verifiers to declarative SolidCraft verification | blocked | Resume after #465 is merged. |
| #432 Use released declarative CAD verification in model verification | blocked | Umbrella migration; proceeds through #460 and later batches. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Resume after model-verification ownership is stable. |
| #391 Extract reusable CAD verification library from Forge | blocked | Close after remaining shared checker code leaves Forge through staged #432 migration. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Umbrella migration; current infrastructure prerequisite is #465. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Starts after #378 verification output is complete. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Independent Forge API defect. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | Independent CLI quality work. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Product/API work. |
| #354 Support standalone sketch extrusions as boolean operands | later | Product/API work. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to superseded qualification architecture. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Independent model/API investigation. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Predates the released docker.cad.solidcraft runtime. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Independent product behavior. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Major Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:
`docker.cad.solidcraft v0.1.0 -> #465 -> #460 -> later #432 batches -> #430 -> #378 -> #366`.
