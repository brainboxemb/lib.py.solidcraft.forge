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

All three currently point to main merge commit
`76e44c2803468fc39358c275b7c1ccab44a3a89c`.

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

Each scope is a complete 188-item baseline with
`source_commit = 76e44c2803468fc39358c275b7c1ccab44a3a89c`.

Generated Pages records the matching scope at the stable root, `/dev-cad/`
and `/dev-ci/`.

Normal short-lived PRs target one dev lane, verify only and are squash-merged.
The destination dev push is the durable integration event.

Promotion uses a temporary head branch:

```text
dev-cad -> promote/dev-cad -> main
dev-ci  -> promote/dev-ci  -> main
```

Promotion PRs run complete validation and are merged with a normal merge
commit. Both long-lived lanes are then synchronized to the resulting main head.
Named-lane incremental selection uses the previous durable
`build/<lane>/build.json.source_commit`, not `github.event.before`.

The public GitHub Pages source still intentionally uses
`backup/gh-pages-before-f11-2026-11-20`. #366 owns the explicit live cut-over.

The remaining repository-maintenance task is #481: delete obsolete **source
branches**. Generated PR/underscore scopes are already removed. The available
GitHub connector does not expose branch deletion, so source refs must not be
claimed as removed until a supported deletion path is available.

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

1. #481 stale source-branch cleanup using the final keep-set;
2. #576 cheap docs-only PR classification;
3. make an explicit go/no-go decision for #366 live Pages cut-over;
4. rewrite the still-useful performance goal from #261 against the current
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
| #592 Document parallel work policy across dev-cad and dev-ci | direct `main` | repository governance | **P0 now** | Record the cross-lane execution rule in plan/development/handoff; squash-merge the direct-main governance PR. |
| #481 Remove stale Forge development branches | `dev-ci` | WS0 | **P0 now** | Delete obsolete source refs against the final keep-set. Generated build cleanup is already complete; do not claim branch deletion without a supported GitHub operation. |
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

## Parallel execution policy

The two development lanes are intentionally independent execution tracks.

- `dev-cad` work and `dev-ci` work may progress in parallel.
- A running workflow blocks only work that depends on its result; do not idle
  the other lane merely because one lane is still validating or publishing.
- Shared dependency releases, owner-repository handoffs and architecture
  boundaries remain real dependency gates.
- Promotion to `main` is an explicit synchronization point. Ordinary work
  inside the two development lanes is not serialized around promotion checks.
- Repository-wide governance changes that apply equally to both lanes may use
  a short-lived branch directly against `main`; do not force them into one
  development lane merely for convenience.
- Such direct-main governance PRs are still short-lived feature PRs and are
  **squash-merged**. Only `promote/dev-cad` / `promote/dev-ci` promotion
  PRs use a normal merge commit.

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

1. [#481, now] Remove obsolete source branches against the permanent keep-set
   when a supported GitHub branch-deletion operation is available.
2. [#576, next dev-ci] Make docs-only PR validation cheap without copying the
   generic CAD-CI planner into Forge.
3. [dev-cad P1] Fix #357 and #356, then continue the current model blockers
   #355, #354, #567 and #568.
4. [#574, dev-cad P1] Restore the generic structured Raw test files block on
   Verification case pages.
5. [#349] Split the latch-required Revolve work into a focused P1 child; keep
   the remaining SOLID › CREATE inventory at P2.
6. [#366] Keep the live Pages-source cut-over as an explicit decision gate; do
   not mix it into ordinary CAD or CI development.
7. Rewrite/retire the superseded issues identified in the table (#261, #340,
   #175, #5) before treating them as implementation work.
