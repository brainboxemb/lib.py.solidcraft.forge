# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

The released declarative verification path and runtime batching are proven.

- #537 and #542 migrated the procedural Qualification catalog in two batches;
- #484/#541 removed per-case CAD runtime startup;
- runtime `v0.3.2` is immutable and green;
- `lib.py.cad.verification 0.14.0` is released at
  `96b25a6bb76e488f3167abc7c1335a9948a18a51`;
- 31 of 32 Qualification cases use declarative `verification/verify.py`;
- `sketch-pattern-mirror` is the sole remaining procedural case.

The current public Pages state remains preserved on
`backup/gh-pages-before-f11-2026-11-20`. Pages must not be cut over until the
current 32-case catalog has durable accepted evidence.

## Current goal

Complete #544: migrate the final procedural Qualification case,
`sketch-pattern-mirror`.

The existing contract includes one baseline-to-saved-design relation:
`abs(mutated center_of_mass.x - baseline center_of_mass.x) > 0.01`.
Released verification 0.14.0 owns that generic comparison through
`SolidCraftMeasurementChangeExpectation`.

## Required proof for #544

- `sketch-pattern-mirror/verification/verify_model.py` is removed;
- its replacement `verify.py` is data-only and preserves baseline, mutation,
  sketch, timeline and numeric-change semantics;
- the model uses `template: forge-model-declarative` and `process: true`;
- all four independent reference child configs exist;
- no procedural `verification/verify_model.py` remains anywhere in the
  32-case Qualification catalog;
- shared SolidCraft/reference runtime batches remain unchanged;
- the full currently processed model/reference set is green;
- durable main receives current evidence for the final migrated case;
- Pages remains unchanged.

## Execution order

1. Pin released `lib.py.cad.verification 0.14.0`.
2. Replace the final procedural verifier with declarative data and four
   reference child configs.
3. Prove the complete current verification graph in PR.
4. Merge and prove main.
5. Close #432 once the procedural-to-declarative migration is complete.
6. Audit the remaining `process: false` declarative cases and current
   `build/main` coverage before #497 Pages publication.
7. Enable/prove any missing durable catalog evidence before #497/#366.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #544 Migrate final sketch-pattern-mirror Qualification case | now | Final procedural consumer; verification 0.14.0 provides its saved-design numeric-change relation. |
| #432 Use released declarative CAD verification in model verification | now | Parent migration issue; closes after #544 main proof. |
| #497 Publish stable Pages from the generic build/main baseline | blocked | First audit/complete current durable evidence for all 32 Qualification cases. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Final Pages lifecycle follows #497. |
| #391 Extract reusable CAD verification library from Forge | effectively complete but still open | Generic verification ownership is external; consumer migration finishes with #544. |
| #481 Remove stale Forge development branches | blocked | Current connected tooling cannot safely delete stale refs. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by released runtime batching and measured #484 work. |
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

`#544 -> durable 32-case coverage audit -> #497 stable Pages -> #366 final Pages lifecycle`.
