# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep implementation detail and history.

## Current status

The development-lane migration (#572) and backlog reorganization (#578) are
complete.

Permanent source lanes:

```text
main
dev-cad
dev-ci
```

The current clean fully synchronized three-lane baseline is main commit
`e0274f5422bf196e057f889ead14d2513a85bf30`. Active work may temporarily
advance one development lane until its next promotion; use GitHub branch heads
and durable scope manifests for live commit identity.

The exact accepted generic stack remains:

- `lib.py.cad.ci 0.9.2` @
  `3f688243f4ee65b1fa42f82adde5344fe5101775`;
- `tool.cad.ci 0.16.1` @
  `4c6bb8b35009ef5008bd99134cf84b59fddc0b8a`;
- external named-scope acceptance: `tool.cad.ci.test` PR #61.

The generated `build` branch is now clean and contains exactly:

```text
main/
dev-cad/
dev-ci/
```

At that synchronization point each scope was a complete 188-item baseline.
During active development, each named scope records its own accepted
`source_commit` and may legitimately be ahead of `main` until promotion.

Generated Pages records the matching scope at the stable root, `/dev-cad/`
and `/dev-ci/`.

Normal short-lived PRs target one dev lane, verify only and are squash-merged.
The destination dev push is the durable integration event.

Promotion is direct from the long-lived lane:

```text
dev-cad -> main
dev-ci  -> main
```

Promotion PRs run complete validation and are merged through the repository
merge-policy workflow. The merge method is selected mechanically:

- base `main` + head exactly `dev-cad` or `dev-ci` -> normal merge commit;
- every other PR -> squash merge.

Temporary `promote/*` heads are no longer part of the supported promotion
flow. After a direct lane promotion, the merge-policy workflow ensures that the
long-lived lane ref still exists and points at the resulting main merge commit,
even when GitHub's repository setting auto-deletes merged head branches.
Named-lane incremental selection uses the previous durable
`build/<lane>/build.json.source_commit`, not `github.event.before`.

The public GitHub Pages source still intentionally uses
`backup/gh-pages-before-f11-2026-11-20`. #366 owns the explicit live cut-over.

The remaining repository-maintenance task is #481: delete obsolete **source
branches**. Generated PR/underscore scopes are already removed. The available
GitHub connector does not expose branch deletion, so source refs must not be
claimed as removed until a supported deletion path is available.

Docs-only pull-request classification (#576) is accepted on `dev-ci`.
Acceptance run `44904510041` kept the normal `cad_ci_pr` check green while
skipping the released CAD-CI action entirely for a `docs/plan.md`-only PR.
Promotion PRs to `main` still bypass that shortcut and require complete
validation.

## Priority model

The backlog uses five dispositions:

- **P0 — now:** finish the active architecture/migration or an immediate
  repository-governance task before ordinary feature work.
- **P1 — next:** concrete current blocker, regression or user-facing defect
  with a known downstream need.
- **P2 — planned:** valuable bounded improvement or roadmap item that should
  follow the P1 blockers.
- **P3 — later/research:** strategic, exploratory or polish work without a
  current delivery blocker.
- **Retire/rewrite:** issue framing is materially superseded, duplicated or
  based on the retired Qualification/CI architecture. Preserve useful evidence,
  then close, consolidate or rewrite before implementation.

The lane column below is the **Forge integration lane**. Generic CAD-CI work
still belongs in `lib.py.cad.ci` / `tool.cad.ci` first, even when Forge
consumes it through `dev-ci`.

## Workstreams

### WS0 — Repository, CI and publication

Primary lane: `dev-ci`.

Owns source-branch topology, generated-state lifecycle, CI cost/reliability,
runtime/tooling simplification and operational Pages publication.

Immediate order:

1. #598 policy-controlled merge method and selective branch lifecycle;
2. #481 stale source-branch cleanup using `/cleanup-branches` on #481 after
   #598 is live on `main`; delete only integrated temporary-prefix refs and
   report open/unmerged branches without touching them;
3. make an explicit go/no-go decision for #366 live Pages cut-over;
4. rewrite the still-useful performance goal from #261 against the current
   released CAD-CI/runtime architecture.

### WS1 — Active CAD blockers and developer UX

Primary lane: `dev-cad`.

These are concrete blockers found in current HUB75/latch work and should be
handled before broad coverage expansion:

1. #357 Slot default-coordinate regression — active now;
2. #356 concise CLI errors plus `python -m scpf --version`;
3. #355 parametric native Slot support;
4. #354 standalone sketch extrusion as a boolean operand;
5. #567 connected line/arc Sketch profiles for sheet-metal blanks;
6. #568 native sheet-metal flange/contour features;
7. #349: split out **Revolve** as the first focused child because the latch
   needs it; keep the rest of the broad SOLID › CREATE inventory in WS3.

This order may be adjusted when one downstream model proves a harder direct
dependency, but broad API expansion must not displace known blockers.

### WS2 — Verification and public-site quality

Primary lane: `dev-cad`. Presentation, reference truth and Forge-owned
Verification content belong here; only generic CI/runtime mechanics discovered
during the work move to `dev-ci` or the central CAD-CI repositories.

- #574 is P1: restore structured Raw test files on all Verification case pages.
- #570 is P2: remove the remaining CADCraft dependency from the six explanatory
  Verification diagrams without moving generic verification rendering into Forge.
- #335 is P2: make the sheet-fold build123d reference use real sheet-metal
  semantics and rewrite remaining historical Qualification wording.

### WS3 — API coverage and modelling roadmap

Primary lane: `dev-cad`.

- #347 generalize native pattern seeds beyond Sketch extrusions — P2.
- #9 first-class Sketch/constraints/face workplanes — P2 strategic epic;
  focused blocker #567 may land first without waiting for the entire epic.
- #349 remaining SOLID › CREATE coverage after the focused Revolve slice — P2.
- #8 Tube/RectTube/OvalTube — P3; coordinate with native `solid.pipe`
  coverage rather than inventing a parallel geometry engine.

### WS4 — AnchorFrame research and interaction polish

Primary lane: `dev-cad`.

This work is intentionally behind the current blockers because production
HUB75 uses explicit Placement today.

- #325 AnchorFrame regression root-cause research — P3.
- #81 inline rotated-occurrence AnchorFrame references — P3.
- #82 Joints-folder visibility policy — P3.
- #175 contains useful historical diagnostic evidence but overlaps #325 and
  the completed change-0005 history; consolidate that evidence, then close or
  rewrite #175.
- #5 predates much of the current Anchor/Placement/AnchorFrame implementation
  and substantially overlaps #9; rewrite it to the remaining unsolved
  constraint/associativity gap or consolidate it into #9.

## Complete open-issue assignment — 2026-11-21

| Issue | Lane | Workstream | Priority | Next action |
| --- | --- | --- | --- | --- |
| #598 Enforce PR merge method through one policy-controlled merge path | `dev-ci` | WS0 | **P0 now** | Merge method, green-check gate and lane restoration are proven. Final gap: merges made with `GITHUB_TOKEN` do not emit a follow-up push workflow, so dispatch Forge integration explicitly for every durable destination ref. |
| #481 Remove stale Forge development branches | `dev-ci` | WS0 | **P0 now** | First cleanup removed ancestry-integrated refs. Extend cleanup so a temporary head is also safe when GitHub records it as a merged PR head; open PR heads and truly unique refs remain protected. |
| #366 Make verified output durable, then cut Pages over | `dev-ci` | WS0 | **P1 decision gate** | Durable/generated side is complete; request explicit approval before changing the live Pages source, then verify public/legacy routes. |
| #570 Remove CADCraft from Forge verification diagrams | `dev-cad` | WS2 | **P2** | Replace the six explanatory diagram sources with deterministic Forge-owned SVG/static sources; remove its CI/runtime input only after the content path no longer needs it. |
| #261 Reduce full qualification from minutes to seconds | `dev-ci` | WS0 | **Retire/rewrite → P2** | Original Qualification/image plan is obsolete; retain measured-performance goal and rewrite against current runtime images, batching and SCons execution. |
| #340 Reuse full release qualification after identical squash merge | `dev-ci` | WS0 | **Retire** | Old Qualification + squash-to-main model is superseded by long-lived lanes and normal promotion merges; close with historical note. |
| #357 Fix Sketch.add() default handling for native Slot profiles | `dev-cad` | WS1 | **P1 now** | Align `Sketch.add()` with the existing auto-registration rule: all five native Slot kinds preserve authored coordinates by default; add all-variant regressions and explicit-anchor rejection. |
| #356 Improve CLI errors and expose --version | `dev-cad` | WS1 | **P1** | Implement concise model/compiler errors, package version command and explicit debug traceback path. |
| #355 Support current SolidCraft parametric Slot API in Forge | `dev-cad` | WS1 | **P1** | Qualify current SolidCraft 0.42 dimensioned Slot contract and restore parameter/expression support. |
| #354 Support standalone sketch extrusions as boolean operands | `dev-cad` | WS1 | **P1** | Generalize boolean operand lowering for `sketch_base_extrusion`. |
| #567 Mixed line/arc closed Sketch profiles for sheet-metal blanks | `dev-cad` | WS1 | **P1** | Deliver focused connected-curve profile API; do not wait for all of #9. |
| #568 Native sheet-metal flange and contour features | `dev-cad` | WS1 | **P1** | Pin SolidCraft 0.42 command contracts and expose generic fabrication-intent APIs. |
| #349 Remaining SolidCraft SOLID › CREATE coverage | `dev-cad` | WS1/WS3 | **P1 Revolve; P2 remainder** | Split focused Revolve child for latch; retain parent as truthful coverage inventory. |
| #574 Restore structured Raw test files presentation | `dev-cad` | WS2 | **P1** | Fix generic Verification template/writer and add regression tests for representative cases. |
| #335 Use build123d Sheet Metal for sheet-fold reference | `dev-cad` | WS2 | **P2** | Replace solid approximation with current build123d Sheet Metal workflow and update historical terminology/tests. |
| #347 Patterns accept any applied Shape feature | `dev-cad` | WS3 | **P2** | Base source validation on native history-feature identity; qualify Hole + sketch-extrude seeds. |
| #9 First-class Sketch objects, constraints and face workplanes | `dev-cad` | WS3 | **P2 epic** | Refresh scope against current Sketch/attachment capabilities; use focused child issues for deliverable slices. |
| #8 Generic hollow primitives Tube/RectTube/OvalTube | `dev-cad` | WS3 | **P3** | Reconcile public shape intent with native `solid.pipe`/shell/boolean histories before implementation. |
| #325 HUB75 AnchorFrame regression root-cause research | `dev-cad` | WS4 | **P3 research** | Rebuild diagnostic from current foundation only when AnchorFrame work becomes active again. |
| #175 HUB75-like AnchorFrame orientation diagnostic | `dev-cad` | WS4 | **Retire/consolidate** | Move still-useful historical evidence to #325/background docs, then close or rewrite. |
| #81 Inline AnchorFrame references for rotated occurrences | `dev-cad` | WS4 | **P3** | Investigate native occurrence-local inline frames without adding a generic matrix engine. |
| #82 Reconsider automatic hiding of SolidCraft Joints folder | `dev-cad` | WS4 | **P3** | Decide interactive/export visibility policy after higher-impact modelling defects. |
| #5 Generic anchors and parametric constraints | `dev-cad` | WS3/WS4 | **Retire/rewrite** | Separate already-delivered anchor behavior from remaining constraint/associativity work; consolidate overlap with #9. |

Every open issue has one primary lane and disposition. New issues should be
added to this table when they become active planning inputs; issue history is
not a substitute for this plan.

## Parallel execution policy

The two long-lived development lanes are independent execution tracks.

- `dev-cad` and `dev-ci` may progress in parallel.
- A running workflow blocks only work whose next step depends on its result.
  Do not idle the other lane merely because one lane is validating or
  publishing.
- Shared dependency releases, owner-repository handoffs and true architecture
  synchronization points remain dependency gates.
- Repository-wide governance that applies equally to both lanes may use a
  short-lived branch directly against `main`.
- Governance-only PRs to `main` are squash-merged.
- Do not choose a merge method manually. Repository automation must use the
  policy-controlled merge workflow from #598.

## Merge and promotion policy

- Short-lived feature/fix PRs target `dev-cad` or `dev-ci` and are
  **squash-merged**.
- PRs to `main` are **squash-merged by default**.
- The only normal-merge exception is a PR whose head is literally the
  long-lived `dev-cad` or `dev-ci` branch and whose base is `main`.
- Temporary heads such as `promote/dev-cad`, `promote/dev-ci`, governance
  branches and all other short-lived heads are squash-merged.
- Promotion PRs require complete processed validation.
- Merge method selection is not a human/assistant choice. Once #598 lands,
  repository automation must merge through the policy-controlled `/merge`
  path; direct merge calls are unsupported.
- After a direct lane promotion, the policy workflow restores/synchronizes the
  promoted long-lived branch to the resulting main merge commit if GitHub's
  automatic head-branch deletion removed it.
- The other long-lived lane incorporates main separately; it is never reset
  over unpromoted work.
- Named lane incremental selection uses the prior durable
  `build/<lane>/build.json.source_commit` as base, not
  `github.event.before`.
- A PR never publishes durable build or Pages state; the destination
  development-branch push performs the durable integration update.

## Immediate execution order

1. [#598, now dev-ci] Finish durable-integration acceptance: after a
   policy-controlled merge, explicitly dispatch Forge integration on the
   destination long-lived ref; direct dev-lane promotion dispatches both
   `main` and the restored promoted lane.
2. [#481, now] Merge squash-aware cleanup, rerun `/cleanup-branches` on #481,
   then review only the truly unique/unmerged retained refs.
3. [#366, decision gate] Decide whether to cut the live Pages source over to
   generated `gh-pages`; do not change it without explicit approval.
4. [dev-cad P1] Fix #357 and #356, then continue the current model blockers
   #355, #354, #567 and #568.
5. [#574, dev-cad P1] Restore the generic structured Raw test files block on
   Verification case pages.
6. [#349] Split the latch-required Revolve work into a focused P1 child; keep
   the remaining SOLID › CREATE inventory at P2.
7. [#366] Keep the live Pages-source cut-over as an explicit decision gate; do
   not mix it into ordinary CAD or CI development.
8. Rewrite/retire the superseded issues identified in the table (#261, #340,
   #175, #5) before treating them as implementation work.
