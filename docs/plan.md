# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history; this plan states what is
current and what follows.

## Current status

Forge uses externally accepted `tool.cad.ci` v0.12.3 at exact commit
`ad7099b4712af13067c1c42ad50e89bf6a8306dd`, with released
`lib.py.cad.ci` 0.7.1.

The durable build migration has now proven:

- sparse PR publication through #489;
- a complete generic `build/main` bootstrap through #493.

The authoritative `build/main` is generic build-store schema 1 and contains
exactly the current processed item set. Existing PR scopes are preserved.

The remaining temporary behavior is:

- PR publication is hard-coded to `simple-box`;
- main pushes use `full_run: true` and replace the complete main scope.

## Current goal

Complete #495 and move durable build publication to steady-state affected-item
updates.

PRs:

```text
incremental CAD-CI
  -> prepare-pr --base/--head
  -> publish sparse PR scope
```

Main:

```text
incremental CAD-CI
  -> fetch current build branch
  -> update-main --base/--head
  -> publish updated main scope
```

No publication happens when the reusable run produces no build artifact.

## Execution order

1. #495 — switch PR and main durable build publication to affected-item updates.
2. #366 — cut Pages over to `cad-ci publish pages`.
3. Add generic PR build/Page cleanup for closed PR scopes.
4. Remove superseded Forge-owned publication code.
5. Resume #430/#378 verification-feature work.
6. Resume #432 broader declarative model migration after generated output is
   stable.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #495 Switch durable build publication to affected-item PR and main updates | now | Replace bootstrap/simple-box-specific publication with generic steady-state selection and partial main updates. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Build PR/main is nearly complete; Pages follows #495. |
| #484 Reduce cold SolidCraft runtime overhead without changing model verification semantics | later | Measured and parked; runtime/image follow-up remains separate. |
| #481 Remove stale Forge development branches | blocked | Branch rule is merged; physical deletion of stale refs remains unavailable through current connected tooling. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | later | Q6 resumes after generated output is stable. |
| #378 Use explicit Forge verification stages instead of integration/native gates | later | Continue five-model verification stages after #366. |
| #432 Use released declarative CAD verification in model verification | blocked | Eleven models are declarative; 21 retain legacy `verify_model.py`. Broader migration waits for stable generated output. |
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

Immediate chain:

`#495 affected build updates -> #366 gh-pages`.
