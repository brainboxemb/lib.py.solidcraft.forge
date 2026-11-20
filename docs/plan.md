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

## Current goal

Complete #472: make model verification depend only on the Forge package build
rather than the complete Forge tool-verification item.

The existing CAD-CI item dependency/output model appears sufficient. Do not add
a new generic CAD-CI feature unless implementation proves that current
primitives cannot express the required package artifact dependency.

## Execution order

1. Re-audit the current Forge package/test/release-verification item boundary.
2. Split package build, Forge unit tests and Forge release verification into
   semantically separate CAD-CI items using existing dependency outputs.
3. Make migrated model verification depend only on the exact Forge package
   artifact it consumes.
4. Preserve Forge unit tests and release verification as independent active
   checks.
5. Measure the resulting five-model run with the new CAD-CI timing evidence.
6. Only then decide whether the remaining repeated Docker/SolidCraft model
   runtime needs a separate performance change.
7. Continue the five-model declarative/visual verification chain under
   #432/#430/#378.
8. Continue durable build/Pages publication under #366 after the verification
   stages are stable.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #472 Make model verification depend only on the Forge package build | now | Next architecture/performance correction; existing CAD-CI primitives should be tried first. |
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

`#472 -> five-model #432/#430/#378 -> #366`.
