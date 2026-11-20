# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Complete #470: adopt the exact released `tool.cad.ci 0.11.0` stack and use
released item-level `process` participation to run a controlled five-model
verification proof.

The prerequisite chain is complete and externally accepted:

- `lib.py.cad.ci` v0.6.0 at
  `dac8c5b5e1147a401730fda31f9bf9de2278c4ee`;
- `tool.cad.ci` v0.11.0 at
  `96d4c9d6076b7452933c048ace65cf2b0a159d64`;
- `tool.cad.ci.test` main is green against that exact released stack.

Forge must consume this behavior, not reimplement it.

## Five-model proof set

Exactly these model verification items remain processed:

- simple-box;
- anchor-topology-mutation;
- attach-angle;
- four-corner-l;
- xz-anchor.

Every other model verification item is explicitly non-processed for this phase.

The Forge `scpf` item remains processed. Shared/reference work remains
processed where required by the existing graph.

## Execution order

1. Pin Forge's reusable workflow to exact `tool.cad.ci` commit
   `96d4c9d6076b7452933c048ace65cf2b0a159d64`.
2. Add only declarative item participation state:
   - the five proof models stay `process: true`;
   - every other model verification item becomes `process: false`;
   - do not add Forge-local selection code.
3. Prove the resulting Forge CAD-CI graph is green with the `scpf` tool/library
   checks still active.
4. After #470 is green, continue the five-model vertical chain:
   - #432 declarative verification ownership;
   - #430 visual verification;
   - #378 remaining verification stages;
   - #366 durable output/publication.
5. Only after the complete five-model chain is stable, enable remaining model
   verification items one at a time.
6. Run the final ownership/publication audit after the full catalog is enabled.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #470 Adopt tool.cad.ci 0.11.0 and run five-model process proof | now | Current implementation step; released prerequisite is satisfied. |
| #432 Use released declarative CAD verification in model verification | next | Umbrella verification-ownership work continues on the five processed models after #470. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Continue after the five-model process graph is established. |
| #391 Extract reusable CAD verification library from Forge | blocked | Close only after remaining shared checker ownership has left Forge through #432. |
| #378 Use explicit Forge verification stages instead of integration/native gates | next | Umbrella migration; continue through the five-model vertical chain after #470. |
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

`#470 -> five-model #432/#430/#378 -> #366 -> enable remaining models one by one`.
