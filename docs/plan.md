# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep implementation detail and history.

## Current status — long-lived lanes are live

The #572 source/build/Pages lane topology is implemented on `main` commit
`4c408be0f34b8bec4f694a7873313279f0e67997`.

The exact accepted generic stack is:

- `lib.py.cad.ci 0.9.2` @
  `3f688243f4ee65b1fa42f82adde5344fe5101775`;
- `tool.cad.ci 0.16.1` @
  `4c6bb8b35009ef5008bd99134cf84b59fddc0b8a`;
- external named-scope acceptance: `tool.cad.ci.test` PR #61.

Forge now has three long-lived source branches:

```text
main
dev-cad
dev-ci
```

`main` and `dev-ci` currently point to `4c408be0f34b8bec4f694a7873313279f0e67997`; `dev-cad` is now ahead at `eb99203c273396fc1b55ff8cabdcd9415ac82536` after the first normal feature merge (#581).

Normal PRs are verification-only. PR #577 proved the new review path: the
`cad_ci_pr` job passed and the durable push/publication job was skipped.

The first `main` push through the new workflow is green. It updated only
`build/main` and stable Pages while preserving the development-subtree keep
set.

The final lane names are `dev-cad` and `dev-ci`. Main commit
`4c408be0f34b8bec4f694a7873313279f0e67997` contains the hyphenated workflow
and documentation.

Both branches were created from that exact main head and completed their first
full bootstrap successfully:

- `dev-cad`: Actions run `44900066106`, 188-item complete scope;
- `dev-ci`: Actions run `44900069488`, 188-item complete scope.

Durable state now proves the final naming end to end:

| Source lane | Build manifest | Pages provenance | Source commit |
| --- | --- | --- | --- |
| `main` | `scope: main` | stable root, `build_scope: main` | `4c408be0…` |
| `dev-cad` | `scope: named, name: dev-cad` | `/dev-cad/`, `build_scope: dev-cad` | `4c408be0…` |
| `dev-ci` | `scope: named, name: dev-ci` | `/dev-ci/`, `build_scope: dev-ci` | `4c408be0…` |

Current Pages build commits are:

- stable root: `ac8be31cfdbe289d456116bf88707aee6f823193`;
- `dev-cad`: `b98f00092b755005908167563e6d832f199c5e70`;
- `dev-ci`: `351ce4c60e602f74f7771ab44a3985440d277086`.

The earlier underscore scopes/branches were temporary migration proof only.
They are obsolete and belong to #481 / generated-state cleanup; they are not
part of the permanent keep-set.

The first normal feature-lane proof is complete:

- #581 targeted `dev-cad` and changed only `docs/plan.md`;
- PR run `44900595100` passed `cad_ci_pr` and skipped `cad_ci_push`;
- #581 was squash-merged to `dev-cad` as
  `eb99203c273396fc1b55ff8cabdcd9415ac82536`;
- dev-cad push run `44900683589` completed successfully.

The durable isolation proof after that push is exact:

| Generated object | Before #581 push | After #581 push | Expected |
| --- | --- | --- | --- |
| `build/main` tree | `74b223c1e4b09a27e322cdcd9f48661ab7d399b9` | same | preserved |
| `build/dev-ci` tree | `6438ce9f4a9bed7d674dedf9f407be7ee50d6653` | same | preserved |
| `gh-pages/dev-ci` tree | `811a7be3ca9703a104f2f3c2c24b3a46fa8c306c` | same | preserved |
| stable Pages provenance blob | `0c8fd545c20d7133ca398587934189e13eb4be86` | same | preserved |
| `build/dev-cad` tree | `34444c1fecfb554eea60d5bf827255f670e7eef6` | `76ab2ec9371f711fdc25899bbba297dae55a4db0` | changed |
| `gh-pages/dev-cad` tree | `c59779fb5455bcc96ad91e903bd194af5e36acf3` | `1095a77a29d76f42c535e8b14dc6c930b848c1ff` | changed |

The temporary underscore Pages subtrees are already absent. Old underscore
source branches/build scopes and any old `build/pr/*` state remain cleanup
work.

Two #572 proofs remain before the migration is closed:

1. promote `dev-cad -> main` through a normal merge commit, verify stable
   publication preserves both dev scopes/previews, then synchronize both lanes;
2. remove obsolete generated `build/pr/*` and underscore scopes where
   supported, then perform stale source-branch cleanup under #481.

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
- Promotion PRs from `dev-cad` or `dev-ci` target `main`, require a
  complete processed validation run, and use a **normal merge commit**.
- After promotion, synchronize the promoted lane to the resulting main head.
- The other development lane should incorporate the new main head before work
  that assumes the promoted state.
- A PR never publishes durable build or Pages state; the destination
  development-branch push performs the durable integration update.

## Immediate execution order

1. [complete] #581 proved short-lived PR -> `dev-cad` review-only flow.
2. [complete] The resulting `dev-cad` push changed only its own durable
   build/Page scope.
3. [#578/#572, now] Open the first promotion PR `dev-cad -> main`; require
   full validation and merge with a normal merge commit.
4. Verify the main push preserves both dev scopes/previews, then synchronize
   `dev-cad` and `dev-ci` to the resulting main head.
5. [#572] Remove old `build/pr/*` and obsolete underscore generated state
   where supported, then close the lane migration.
6. [#481] Remove stale source branches against the final keep-set.
7. Start P1 work in parallel by lane:
   - `dev-ci`: #576;
   - `dev-cad`: #357 / #356, then the current model blockers.
8. Treat #366 as a separate explicit live-publication decision, not as a
   hidden prerequisite for CAD development.
