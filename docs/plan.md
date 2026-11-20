# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history; this plan states what is
current and what follows.

## Current goal

Complete #473: reorganize Forge documentation so the primary documents are
obvious and current.

Primary documents:

- `docs/api.md`
- `docs/design.md`
- `docs/plan.md`
- `docs/requirements.md`
- `docs/release.md`

Secondary documentation:

- `docs/manual/` — current task-oriented usage/developer guidance;
- `docs/background/` — historical design records, audits, change records,
  research, migration notes and vendor/reference background;
- `docs/agent/` — generated/machine-oriented information.

The existing `docs/05-cad-api-design.md` is not current enough to rename
unchanged. It must be reconciled with the current exported API and implemented
change records before becoming `docs/api.md`.

## Execution order

1. Update the API contract to current Forge behavior, including signed Sketch
   extrusion, native Slot constructors, circular feature patterns and the
   explicit native Hole family.
2. Rename the release-process document to `docs/release.md` and make its
   current-state wording match the active CI/publication architecture.
3. Move current task-oriented documents to `docs/manual/`.
4. Move historical/narrow design, change, migration and vendor material to
   `docs/background/` while preserving history.
5. Update README, AGENTS and all internal Markdown references.
6. Verify no active references point at the old numbered/root paths.
7. Make no Forge API/compiler/verification/CI behavior changes in this issue.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #473 Reorganize Forge documentation around primary docs, manual and background | now | Current documentation-maintenance task. |
| #472 Make model verification depend only on the Forge package build | next | Resume after documentation maintenance; no new CAD-CI feature appears necessary. |
| #432 Use released declarative CAD verification in model verification | next | Continue the five-model verification migration after #472. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Resume after the dependency/runtime structure is corrected. |
| #391 Extract reusable CAD verification library from Forge | blocked | Close only after remaining shared checker ownership has left Forge through #432. |
| #378 Use explicit Forge verification stages instead of integration/native gates | next | Umbrella migration after #472/#432. |
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

`#473 -> #472 -> five-model #432/#430/#378 -> #366`.
