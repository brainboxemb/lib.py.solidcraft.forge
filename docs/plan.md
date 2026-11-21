# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep implementation detail and history.

## Current status — long-lived lanes are live

The #572 source/build/Pages lane topology is implemented on `main` commit
`69a1e18acc9d6b2074e3b4f4ee5e4393c761e196`.

The exact accepted generic stack is:

- `lib.py.cad.ci 0.9.2` @
  `3f688243f4ee65b1fa42f82adde5344fe5101775`;
- `tool.cad.ci 0.16.1` @
  `4c6bb8b35009ef5008bd99134cf84b59fddc0b8a`;
- external named-scope acceptance: `tool.cad.ci.test` PR #61.

Forge now has three long-lived source branches:

```text
main
dev_cad
dev_ci
```

All three currently point to `69a1e18acc9d6b2074e3b4f4ee5e4393c761e196`.

Normal PRs are verification-only. PR #577 proved the new review path: the
`cad_ci_pr` job passed and the durable push/publication job was skipped.

The first `main` push through the new workflow is green. It updated only
`build/main` and stable Pages while preserving the development-subtree keep
set.

Both development branches were then created from that exact proven main head.
Their first push events automatically bootstrapped complete named scopes with
`full_run=true`; both runs are green.

Current durable build scopes:

| Scope | Manifest | Source commit | Items |
| --- | --- | --- | ---: |
| `main` | `scope: main` | `69a1e18…` | complete baseline |
| `dev_cad` | `scope: named, name: dev_cad` | `69a1e18…` | 188 |
| `dev_ci` | `scope: named, name: dev_ci` | `69a1e18…` | 188 |

Current generated Pages provenance records the matching scope for all three
sites: stable root = `main`, `/dev_cad/` = `dev_cad`, and
`/dev_ci/` = `dev_ci`.

Isolation was checked at Git-tree level. When `dev_cad` published after
`dev_ci`:

- the captured `build/dev_ci` tree SHA remained
  `6401626fbb2b0a2e6f2b66de0364077ea3278c21`;
- the captured `gh-pages/dev_ci` tree SHA remained
  `c2e5ca4471c38a6fc597550f723f9ca06e4a5d20`;
- the `build/main` tree SHA remained
  `490b6897ce10287454591093953fe7a5826fdecd`;
- stable Pages provenance remained on scope `main`.

Two #572 proofs remain before the migration is closed:

1. exercise a real short-lived feature PR into `dev_cad`, then promote
   `dev_cad -> main` through a normal merge commit and synchronize the lanes;
2. remove obsolete generated `build/pr/*` state through the released CAD-CI
   cleanup surface, then perform stale source-branch cleanup under #481.

The live public GitHub Pages source is still intentionally on
`backup/gh-pages-before-f11-2026-11-20`. Issue #366 owns that separate
operational cut-over and requires an explicit decision; #572 does not switch it.

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
consumes it through `dev_ci`.

## Workstreams

### WS0 — Repository, CI and publication

Primary lane: `dev_ci`.

Owns source-branch topology, generated-state lifecycle, CI cost/reliability,
runtime/tooling simplification and operational Pages publication.

Immediate order:

1. finish #572 promotion/synchronization and generated-PR cleanup;
2. #481 stale source-branch cleanup using the final keep-set;
3. #576 cheap docs-only PR classification;
4. make an explicit go/no-go decision for #366 live Pages cut-over;
5. simplify the remaining verification toolchain under #570;
6. rewrite the still-useful performance goal from #261 against the current
   released CAD-CI/runtime architecture.

### WS1 — Active CAD blockers and developer UX

Primary lane: `dev_cad`.

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

Primary lane: `dev_cad` for presentation/reference truth; infrastructure
changes discovered here may move to `dev_ci`.

- #574 is P1: restore structured Raw test files on all Verification case pages.
- #335 is P2: make the sheet-fold build123d reference use real sheet-metal
  semantics and rewrite remaining historical Qualification wording.

### WS3 — API coverage and modelling roadmap

Primary lane: `dev_cad`.

- #347 generalize native pattern seeds beyond Sketch extrusions — P2.
- #9 first-class Sketch/constraints/face workplanes — P2 strategic epic;
  focused blocker #567 may land first without waiting for the entire epic.
- #349 remaining SOLID › CREATE coverage after the focused Revolve slice — P2.
- #8 Tube/RectTube/OvalTube — P3; coordinate with native `solid.pipe`
  coverage rather than inventing a parallel geometry engine.

### WS4 — AnchorFrame research and interaction polish

Primary lane: `dev_cad`.

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
| #578 Reorganize Forge backlog into development-lane workstreams and priorities | `dev_cad` | planning/governance | **P0** | This change: establish the new source of truth, then use it as the first feature/promotion proof. |
| #572 Introduce long-lived dev_cad/dev_ci integration lanes | `dev_ci` | WS0 | **P0** | Prove feature→dev→main promotion/sync and remove obsolete generated PR scopes; then close. |
| #481 Remove stale Forge development branches | `dev_ci` | WS0 | **P0 after #572** | Re-audit branches against final keep-set; delete stale issue/change branches after generated PR cleanup. |
| #576 Skip expensive CAD-CI and stable-site jobs for docs-only pull requests | `dev_ci` | WS0 | **P1** | Design cheap pre-bootstrap classification without copying the generic item planner. |
| #366 Make verified output durable, then cut Pages over | `dev_ci` | WS0 | **P1 decision gate** | Durable/generated side is complete; request explicit approval before changing the live Pages source, then verify public/legacy routes. |
| #570 Remove CADCraft from Forge verification diagrams | `dev_ci` | WS0 | **P2** | Replace the six explanatory diagram sources with deterministic Forge-owned SVG/static sources and remove the runtime dependency. |
| #261 Reduce full qualification from minutes to seconds | `dev_ci` | WS0 | **Retire/rewrite → P2** | Original Qualification/image plan is obsolete; retain measured-performance goal and rewrite against current runtime images, batching and SCons execution. |
| #340 Reuse full release qualification after identical squash merge | `dev_ci` | WS0 | **Retire** | Old Qualification + squash-to-main model is superseded by long-lived lanes and normal promotion merges; close with historical note. |
| #357 Fix Sketch.add() default handling for native Slot profiles | `dev_cad` | WS1 | **P1** | Small regression fix first; align `Sketch.add()` with native Slot coordinate semantics and cover all variants. |
| #356 Improve CLI errors and expose --version | `dev_cad` | WS1 | **P1** | Implement concise model/compiler errors, package version command and explicit debug traceback path. |
| #355 Support current SolidCraft parametric Slot API in Forge | `dev_cad` | WS1 | **P1** | Qualify current SolidCraft 0.42 dimensioned Slot contract and restore parameter/expression support. |
| #354 Support standalone sketch extrusions as boolean operands | `dev_cad` | WS1 | **P1** | Generalize boolean operand lowering for `sketch_base_extrusion`. |
| #567 Mixed line/arc closed Sketch profiles for sheet-metal blanks | `dev_cad` | WS1 | **P1** | Deliver focused connected-curve profile API; do not wait for all of #9. |
| #568 Native sheet-metal flange and contour features | `dev_cad` | WS1 | **P1** | Pin SolidCraft 0.42 command contracts and expose generic fabrication-intent APIs. |
| #349 Remaining SolidCraft SOLID › CREATE coverage | `dev_cad` | WS1/WS3 | **P1 Revolve; P2 remainder** | Split focused Revolve child for latch; retain parent as truthful coverage inventory. |
| #574 Restore structured Raw test files presentation | `dev_cad` | WS2 | **P1** | Fix generic Verification template/writer and add regression tests for representative cases. |
| #335 Use build123d Sheet Metal for sheet-fold reference | `dev_cad` | WS2 | **P2** | Replace solid approximation with current build123d Sheet Metal workflow and update historical terminology/tests. |
| #347 Patterns accept any applied Shape feature | `dev_cad` | WS3 | **P2** | Base source validation on native history-feature identity; qualify Hole + sketch-extrude seeds. |
| #9 First-class Sketch objects, constraints and face workplanes | `dev_cad` | WS3 | **P2 epic** | Refresh scope against current Sketch/attachment capabilities; use focused child issues for deliverable slices. |
| #8 Generic hollow primitives Tube/RectTube/OvalTube | `dev_cad` | WS3 | **P3** | Reconcile public shape intent with native `solid.pipe`/shell/boolean histories before implementation. |
| #325 HUB75 AnchorFrame regression root-cause research | `dev_cad` | WS4 | **P3 research** | Rebuild diagnostic from current foundation only when AnchorFrame work becomes active again. |
| #175 HUB75-like AnchorFrame orientation diagnostic | `dev_cad` | WS4 | **Retire/consolidate** | Move still-useful historical evidence to #325/background docs, then close or rewrite. |
| #81 Inline AnchorFrame references for rotated occurrences | `dev_cad` | WS4 | **P3** | Investigate native occurrence-local inline frames without adding a generic matrix engine. |
| #82 Reconsider automatic hiding of SolidCraft Joints folder | `dev_cad` | WS4 | **P3** | Decide interactive/export visibility policy after higher-impact modelling defects. |
| #5 Generic anchors and parametric constraints | `dev_cad` | WS3/WS4 | **Retire/rewrite** | Separate already-delivered anchor behavior from remaining constraint/associativity work; consolidate overlap with #9. |

Every open issue has one primary lane and disposition. New issues should be
added to this table when they become active planning inputs; issue history is
not a substitute for this plan.

## Merge and promotion policy

- Short-lived feature/fix PRs target `dev_cad` or `dev_ci` and are
  **squash-merged**.
- Promotion PRs from `dev_cad` or `dev_ci` target `main`, require a
  complete processed validation run, and use a **normal merge commit**.
- After promotion, synchronize the promoted lane to the resulting main head.
- The other development lane should incorporate the new main head before work
  that assumes the promoted state.
- A PR never publishes durable build or Pages state; the destination
  development-branch push performs the durable integration update.

## Immediate execution order

1. [#578, now] Merge this plan through a short-lived PR into `dev_cad`.
2. Prove the resulting `dev_cad` push is incremental and changes only
   `build/dev_cad` + `gh-pages/dev_cad`.
3. Open the first promotion PR `dev_cad -> main`; require full validation and
   merge with a normal merge commit.
4. Verify the main push preserves both dev scopes/previews, then synchronize
   `dev_cad` and `dev_ci` to the resulting main head.
5. [#572] Remove old `build/pr/*` state using released CAD-CI cleanup and
   close the lane migration.
6. [#481] Remove stale source branches against the final keep-set.
7. Start P1 work in parallel by lane:
   - `dev_ci`: #576;
   - `dev_cad`: #357 / #356, then the current model blockers.
8. Treat #366 as a separate explicit live-publication decision, not as a
   hidden prerequisite for CAD development.
