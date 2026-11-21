# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

#559 is complete.

The current native Verification catalog contains 36 active declarative cases:
the final historical 32-case baseline plus the four replay-safe historical
cases restored by #559. Every full model case has four independent reference
children, giving 144 current reference items.

The current durable baseline is green:

- Forge source: `ad36b062203b7de2b20c7fa2d11c99dfc50a1340`;
- generated build commit:
  `7c1bffacbc3369d998a85cac1121672d5110b2ff`;
- `build/main`: 36 model scopes + 144 reference scopes;
- current `gh-pages` output:
  `3ef0f1e5327e2eea1367d5fbf86e7061e1a8f769`;
- stable site manifest: 36 Verification cases.

`model_authoring` remains deliberately Q1/Q2-only. `custom-anchor` remains
the expected-rejection release fixture blocked by #81.
`attached-through-all` and `plate` are explicit regression fixtures with
current executing owners.

The public GitHub Pages source is still deliberately pointed at
`backup/gh-pages-before-f11-2026-11-20`. Generated `gh-pages` is not the
live source yet.

## Current goal

Complete #558 by migrating Forge main verification + durable build publication
+ stable Pages publication to the externally accepted same-runner surface.

The required generic chain is complete:

- `tool.cad.ci 0.15.0` release:
  `9f37be0af5c4076f676b6407857c5905e11a47d6`;
- pinned `lib.py.cad.ci 0.8.4`:
  `4e033fd17e911b3feb92b1a34433b884ca788ab6`;
- external acceptance:
  `tool.cad.ci.test` PR #59 / merge
  `2fcfbc7bcd2f80a3e629d2846fe79fb8001d3029`.

## Required proof for #558

The Forge main workflow must use one job and one runner:

```text
released same-runner action
  -> one selected CAD-CI graph
  -> build fetch
  -> update-main
  -> publish build/main
  -> Forge site generation from prepared-main
  -> publish gh-pages
```

Acceptance requires:

- no main-path Actions upload/download artifact;
- no second or third main publication job;
- no second tool/library checkout/install;
- no Forge-owned item-selection or build-store logic;
- documentation/site-only changes do not start CAD runtimes merely because
  Pages is published;
- deletion-only durable updates remain supported;
- site generation consumes the exact prepared main tree that was published;
- the returned immutable build commit is stored in site provenance;
- `build/main` and `gh-pages` remain freshness-safe generated output;
- representative main CI is green after merge.

PR verification remains on released `reusable-pr.yml`. The separate
read-only stable-site PR validation is not a reason to duplicate the generic PR
lifecycle in Forge.

## Next publication work

After #558 is green on main, #366 owns the remaining live lifecycle.

The live Pages source must **not** be repointed from
`backup/gh-pages-before-f11-2026-11-20` merely because #558 succeeds.
That cut-over is a separate explicit action under #366.

## Execution order

1. [#558] Migrate Forge main to exact released tool.cad.ci 0.15.0.
2. [#558] Prove the PR/source regression tests.
3. [#558] Merge and observe one-runner main publication end to end.
4. Close #558 only after durable `build/main` and generated `gh-pages`
   provenance are verified.
5. [#366] Review the generated replacement site.
6. [#366] Repoint the live Pages source only with explicit cut-over approval.
7. [#366] Complete remaining preview/cleanup lifecycle work.

## Open issue assessment — 2026-11-21

| Issue | Status | Assessment |
| --- | --- | --- |
| #558 Run main verification and Pages publication as one selective workflow | now | Generic 0.15.0 same-runner support is released and externally accepted; Forge migration and main proof remain. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked by #558 | Durable build and generated gh-pages exist; live source cut-over waits for the corrected main flow. |
| #391 Extract reusable CAD verification library from Forge | effectively complete but still open | Generic verification ownership and consumer migration are complete; remaining closure review is separate. |
| #481 Remove stale Forge development branches | later | Stale refs from closed work remain cleanup debt. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by released runtime batching and later timing work. |
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
| #81 Support inline AnchorFrame references for rotated occurrences | later / blocks custom-anchor | Current `custom-anchor` intentionally proves the unsupported case rejects clearly. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Major Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:

`#558 single-runner main/Pages -> #366 explicit live Pages lifecycle`.
