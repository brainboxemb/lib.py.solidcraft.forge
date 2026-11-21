# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep implementation detail and history.

## Current status — long-lived lanes are live

The final long-lived source lanes are:

```text
main
dev-cad
dev-ci
```

The exact accepted generic stack remains:

- `lib.py.cad.ci 0.9.2` @
  `3f688243f4ee65b1fa42f82adde5344fe5101775`;
- `tool.cad.ci 0.16.1` @
  `4c6bb8b35009ef5008bd99134cf84b59fddc0b8a`;
- external named-scope acceptance: `tool.cad.ci.test` PR #61.

The hyphenated lane bootstrap is proven:

- `dev-cad` bootstrap run `44900066106`: green, 188-item complete scope;
- `dev-ci` bootstrap run `44900069488`: green, 188-item complete scope;
- stable root and both named Pages subtrees record their matching build scope;
- the temporary underscore Pages subtrees are gone.

The first normal feature flow is also proven:

- #581 targeted `dev-cad`, changed only `docs/plan.md`, passed the review-only
  PR path and skipped durable publication;
- #581 was squash-merged to `dev-cad`;
- dev-cad push run `44900683589` was green;
- exact Git-tree comparison proved only `build/dev-cad` and
  `gh-pages/dev-cad` changed while `build/main`, `build/dev-ci`, stable
  Pages and `gh-pages/dev-ci` remained byte-for-byte at the same Git objects.

The first promotion proof is complete enough to expose one final synchronization
edge case:

1. promotion PR #583 ran complete validation and passed;
2. #583 was merged to main with a **normal merge commit** as
   `b13d772aa9388c21f1362d990ae94e875a93a7c1`;
3. main push run `44901399321` was green;
4. main publication changed only `build/main` and stable Pages; both dev
   build/Page tree SHAs were preserved;
5. `dev-ci` fast-forwarded to the new main head and run `44901462770` was
   green;
6. GitHub automatically deleted `dev-cad` because it was the direct PR head;
7. `dev-cad` was recreated at the main merge commit, but branch-create run
   `44901501059` failed before CAD execution because GitHub supplied
   `github.event.before = 0000000000000000000000000000000000000000`.

The failure is a workflow-base bug, not a CAD or generated-state failure.
`build/dev-cad/build.json` already contains the correct previous accepted
`source_commit`; named lanes must use that durable source commit as their
incremental base.

The first dev-ci integration push of that fix, run `44901868170`, failed in
the lane-resolution shell before CAD execution because the embedded Python
heredoc terminator was indented inside command substitution.

The follow-up on `issue/572-manifest-base-shell-fix` keeps the same manifest
base design but uses a single-line Python manifest reader that is valid inside
the YAML shell block.

The #572 synchronization fix therefore does two things:

- named dev pushes derive their incremental base from their own durable
  `build.json.source_commit`, making branch recreation/synchronization safe;
- future promotions use temporary `promote/dev-cad` or `promote/dev-ci`
  branches. GitHub may auto-delete that temporary head after merge without
  deleting the long-lived lane.

The live public GitHub Pages source is still intentionally on
`backup/gh-pages-before-f11-2026-11-20`. Issue #366 owns that separate
operational cut-over and requires explicit approval.

The generated `build` branch still contains obsolete migration/history state:

```text
pr/515/
pr/549/
dev_cad/
dev_ci/
```

Those entries are cleanup work after the synchronization fix is proven. The
permanent generated keep-set is exactly:

```text
main/
dev-cad/
dev-ci/
```

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

1. finish #572 promotion/synchronization and generated-PR cleanup;
2. #481 stale source-branch cleanup using the final keep-set;
3. #576 cheap docs-only PR classification;
4. make an explicit go/no-go decision for #366 live Pages cut-over;
5. rewrite the still-useful performance goal from #261 against the current
   released CAD-CI/runtime architecture.

### WS1 — Active CAD blockers and developer UX

Primary lane: `dev-cad`.

These are concrete blockers found in current HUB75/latch work and should be
handled before broad coverage expansion:

1. #357 Slot default-coordinate regression;
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
| #578 Reorganize Forge backlog into development-lane workstreams and priorities | `dev-cad` | planning/governance | **P0** | This change: establish the new source of truth, then use it as the first feature/promotion proof. |
| #572 Introduce long-lived dev-cad/dev-ci integration lanes | `dev-ci` | WS0 | **P0** | Prove feature→dev→main promotion/sync and remove obsolete generated PR scopes; then close. |
| #481 Remove stale Forge development branches | `dev-ci` | WS0 | **P0 after #572** | Re-audit branches against final keep-set; delete stale issue/change branches after generated PR cleanup. |
| #576 Skip expensive CAD-CI and stable-site jobs for docs-only pull requests | `dev-ci` | WS0 | **P1** | Design cheap pre-bootstrap classification without copying the generic item planner. |
| #366 Make verified output durable, then cut Pages over | `dev-ci` | WS0 | **P1 decision gate** | Durable/generated side is complete; request explicit approval before changing the live Pages source, then verify public/legacy routes. |
| #570 Remove CADCraft from Forge verification diagrams | `dev-cad` | WS2 | **P2** | Replace the six explanatory diagram sources with deterministic Forge-owned SVG/static sources; remove its CI/runtime input only after the content path no longer needs it. |
| #261 Reduce full qualification from minutes to seconds | `dev-ci` | WS0 | **Retire/rewrite → P2** | Original Qualification/image plan is obsolete; retain measured-performance goal and rewrite against current runtime images, batching and SCons execution. |
| #340 Reuse full release qualification after identical squash merge | `dev-ci` | WS0 | **Retire** | Old Qualification + squash-to-main model is superseded by long-lived lanes and normal promotion merges; close with historical note. |
| #357 Fix Sketch.add() default handling for native Slot profiles | `dev-cad` | WS1 | **P1** | Small regression fix first; align `Sketch.add()` with native Slot coordinate semantics and cover all variants. |
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

## Merge and promotion policy

- Short-lived feature/fix PRs target `dev-cad` or `dev-ci` and are
  **squash-merged**.
- Promotion does **not** use the long-lived dev branch directly as the PR head.
  Create `promote/dev-cad` or `promote/dev-ci` at the current lane head.
- Promotion PRs from that temporary branch target `main`, require a complete
  processed validation run, and use a **normal merge commit**.
- GitHub may auto-delete the temporary promotion head after merge; this is
  desirable and must never delete the long-lived lane.
- After promotion, fast-forward/synchronize both long-lived dev lanes to the
  resulting main head.
- Named lane incremental selection uses the prior durable
  `build/<lane>/build.json.source_commit` as base, not
  `github.event.before`.
- A PR never publishes durable build or Pages state; the destination
  development-branch push performs the durable integration update.

## Immediate execution order

1. [#572, now] Merge the durable-base/promotion-branch fix through `dev-ci`.
2. Prove a recreated/synchronized `dev-cad` can update from its durable
   manifest base without a full bootstrap.
3. Promote the CI fix through temporary `promote/dev-ci -> main`; verify
   complete validation and normal merge while `dev-ci` itself remains present.
4. Synchronize both long-lived lanes to the resulting main head and prove both
   named durable scopes/Pages previews are current.
5. [#572] Atomically remove generated `pr/515`, `pr/549`, `dev_cad` and
   `dev_ci` from the build branch, preserving only main/dev-cad/dev-ci.
6. Close #572 when those generated-state and synchronization proofs are green.
7. [#481] Remove stale source branches against the final keep-set.
8. Start P1 work in parallel by lane:
   - `dev-ci`: #576;
   - `dev-cad`: #357 / #356, then the current model blockers.
9. Treat #366 as a separate explicit live-publication decision, not as a
   prerequisite for CAD development.
