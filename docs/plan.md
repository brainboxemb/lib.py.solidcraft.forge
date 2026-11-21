# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

The 32-case historical model-verification baseline is declarative, active and
durable. #559 restores four cases removed during the replay-safety transition
giving 36 current full Verification cases. `model_authoring` remains outside
native Verification because #213 explicitly accepted it as Q1/Q2-only.

- every current model item declares `process: true`;
- every current model uses local declarative `verification/verify.py`;
- every current model has four independent reference child items;
- the four restored historical native cases must pass the same model and
  reference paths before #559 closes;
- `model_authoring` must remain directly executed by the ordinary unit suite
  at its accepted Q1/Q2 boundary;
- the six current CADCraft diagrams are durable;
- per-example engineering documentation is local to each verified example
  README and presentation metadata remains local to `model.yml`.

#497 is complete. PR #557 merged as
`f8bf0b01228b23407d9ab67462cc2afd44fe83be`; the corresponding main run
successfully updated durable `build/main` and published replacement output to
the `gh-pages` branch.

The public GitHub Pages source is still deliberately pointed at the preserved
pre-cut-over backup branch
`backup/gh-pages-before-f11-2026-11-20`. The new `gh-pages` output exists,
but no live cut-over is performed while the remaining main/publication workflow
architecture is being corrected.

The example-history audit found that `examples/` contains more than the
current 32 verified model cases. The complete lineage is recorded in
`docs/background/example-history.md`.

Important findings:

- four former Qualification cases
  (`as-built-attach`, `parametric-move`,
  `parametric-placement-pair`, `rotated-copy-placement`) were removed for a
  replay-safety limitation that has since been technically resolved, but those
  cases were never explicitly reconsidered for full Verification;
- `custom-anchor` remains an intentional expected-rejection release fixture
  and is still limited by open #81;
- `model_authoring` was requested as a qualification fixture in #213 but was
  never carried into the current model-verification catalog;
- `attached-through-all` is a focused regression fixture rather than a
  historical catalog case;
- `plate` is a pre-Qualification sample with stale documentation and no
  current verification owner.

Current primary documentation has been corrected so it no longer presents the
old five-model staged proof as the current state.

## Current goal

Complete #559 by proving the five restored/completed Verification cases through
the normal CAD-CI model/reference paths, keeping `custom-anchor` as the
intentional blocked release fixture, keeping both `attached-through-all` and `plate` as explicitly owned focused
regression fixtures.

## Required proof for #559

The history model and structural role guard are complete in #560. A non-model
example directory now requires local `role.yml`, validated by the source-only
site CI item.

The remaining #559 work is to execute the recorded decisions. For every
top-level directory below `examples/`:

- establish its historical origin and current purpose;
- identify its current executing owner (model verification, Forge release
  verification, unit/regression test, maintained documentation sample, or
  none);
- for former Qualification cases, record why they left the catalog and whether
  the original blocker still exists;
- make an explicit keep/promote/retire decision;
- do not infer current validity from directory age, branch existence or
  `model.yml` presence alone;
- add a structural guard so future example directories cannot silently exist
  outside every declared role;
- keep full model Verification membership distributed through per-example
  configuration rather than recreating a central executable case registry.

The history document itself is descriptive evidence, not an execution catalog.

## Next publication work

After #559 is resolved, continue #558 and #366.

#558 owns the Forge use-case for the corrected main workflow:

- one high-level main workflow and one hosted runner;
- one exact CAD-CI bootstrap;
- no CAD execution when selection contains no CAD work;
- no artifact handoff to a second runner for durable-main publication;
- Pages generation/publication follows on the same runner when required;
- documentation/site-only changes reuse authoritative `build/main`;
- the site generator remains Forge-owned while generated-branch safety stays
  generic CAD-CI behavior.

Any missing generic behavior must be implemented/released through the normal
`lib.py.cad.ci -> tool.cad.ci -> tool.cad.ci.test -> Forge` chain rather than
as a Forge workaround.

#366 remains the umbrella for the final durable-build/Pages lifecycle,
including the remaining live cut-over and later preview/cleanup behavior.

## Execution order

1. [complete in #560] Freeze the complete example-history model.
2. [complete in #560] Give every non-catalog directory an explicit local role.
3. [complete in #560] Add the source-only structural role guard and correct
   stale primary architecture documentation.
4. [this change] Restore the four historical native Verification cases, return
   `model_authoring` to its accepted Q1/Q2-only role, keep `plate` under its
   actual live-protocol owner and make `attached-through-all` execute from its
   declared unit-test owner.
5. [#559] Require the four restored model/reference paths and complete
   stable-site generation to pass; then close #559.
6. [#558] Implement any required generic single-runner main/publication support
   in the owning CAD-CI repositories and release/accept it.
7. [#558] Migrate Forge main publication to that released workflow without
   duplicate runner/bootstrap/artifact phases.
8. [#366] Re-enable the intended live Pages source only after the corrected
   main/publication path is green.
9. [#366] Complete remaining preview/cleanup lifecycle work.

## Open issue assessment — 2026-11-21

| Issue | Status | Assessment |
| --- | --- | --- |
| #559 Reconcile Forge example history, verification catalog and orphaned fixtures | now | History audit found four formerly-qualified cases whose replay blocker is gone, one unfinished model-authoring lineage, one focused regression fixture, one intentional blocked release fixture and one stale sample. |
| #558 Run main verification and Pages publication as one selective workflow | next / generic dependency | Current main/Pages path still pays duplicate runner/bootstrap/artifact overhead. Must use the same selective/single-runner architecture as the accepted PR direction; missing generic support belongs upstream first. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked by #558 | Durable build and gh-pages publication exist; final live source cut-over and preview/cleanup lifecycle wait for the corrected main workflow. |
| #391 Extract reusable CAD verification library from Forge | effectively complete but still open | Generic verification ownership and consumer migration are complete; remaining cleanup/closure should be reviewed separately. |
| #481 Remove stale Forge development branches | later | Many issue branches belong to closed issues. Branch refs are cleanup debt, not active-work truth. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by v0.3.2 runtime batching and #484 measurements. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to superseded Qualification architecture. |
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
| #81 Support inline AnchorFrame references for rotated occurrences | later / blocks custom-anchor | The current `custom-anchor` release fixture intentionally proves this unsupported case rejects clearly. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Major Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:

`#559 example reconciliation -> #558 single-runner main/Pages -> #366 final live Pages lifecycle`.
