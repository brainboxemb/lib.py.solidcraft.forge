# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

The central CAD-CI, durable `build/main` store and generated `gh-pages`
publication path are implemented and green.

The Verification recovery is complete:

- #378 was completed by PR #571;
- all 36 active Verification models own required model-local visual policies;
- all 36 visual reports pass;
- the stable Pages validation passes;
- main commit `45c6213ad6b6c02a230a95f936ca2c65f4c56da2` produced durable
  build commit `550cad35ed18504af164bc0c6467fb3eb492fad6`;
- generated `gh-pages` commit
  `a11437cef70341d543a3ff8a713e59098dfbd0ee` passed a complete 36-page
  content audit.

The live Pages source remains intentionally on
`backup/gh-pages-before-f11-2026-11-20`. Issue #366 still owns the explicit
public cut-over and live-route verification, but it is no longer a prerequisite
for the development-lane migration.

The generic lane primitives are now released and externally accepted:

- `lib.py.cad.ci 0.9.2` at
  `3f688243f4ee65b1fa42f82adde5344fe5101775`;
- `tool.cad.ci 0.16.1` at
  `4c6bb8b35009ef5008bd99134cf84b59fddc0b8a`;
- `tool.cad.ci.test` PR #61 proved independent complete named build scopes,
  named Pages subtrees, sibling preservation and stable-root preservation
  through the released stack.

Forge still uses the old topology: pull requests target `main`, the reusable
PR workflow may publish `build/pr/<number>`, and only pushes to `main`
produce durable build/Pages output.

## Immediate goal

Implement #572 in Forge now:

1. adopt exact accepted `tool.cad.ci 0.16.1`;
2. make pull requests verification-only, with no durable PR build/Pages write;
3. make pushes to `main`, `dev-cad` and `dev-ci` publish only their own
   complete build scope;
4. publish dev Pages below `/dev-cad/` and `/dev-ci/`, while stable main
   preserves both subtrees;
5. create both long-lived dev branches only after that workflow is merged;
6. bootstrap and prove both lanes;
7. immediately after the lane proof, refresh this plan against every open issue
   and assign the new workstream/priority structure.

Keep #366 separate from this migration. Do not switch the live Pages source as
part of #572.

## Next architecture — long-lived development lanes

Forge should use three long-lived source branches:

```text
main
dev-cad
dev-ci
```

Their responsibilities are:

- `main` — stable/production integration only. A merge to `main` may update
  the durable main build and the stable Pages root.
- `dev-cad` — integration lane for Forge API, compiler, model, verification
  data and other CAD/product work.
- `dev-ci` — integration lane for Forge-side CI/infrastructure integration.

`dev-ci` does not change repository ownership boundaries. Generic CAD-CI
functionality still belongs in `lib.py.cad.ci` and `tool.cad.ci`, is tested
and released there, and is then consumed/qualified through Forge's `dev-ci`
lane.

### Pull-request rule

Normal feature/fix pull requests target one development lane and perform
verification only.

They must not create durable per-PR build or Pages publication.

Target model:

```text
feature/fix branch
  -> PR to dev-cad or dev-ci
  -> changed-path-selected verification
  -> no durable build/pr/<number>
  -> no durable Pages PR scope
  -> merge to development lane
```

The development branch push, not the PR, becomes the durable integration event.

### Durable build layout

The generated `build` branch should converge on exactly three long-lived
Forge scopes:

```text
main/
dev-cad/
dev-ci/
```

Each scope is a complete reconciled durable baseline for that source lane.

Required behavior:

- a `dev-cad` push updates/replaces only `build/dev-cad`;
- a `dev-ci` push updates/replaces only `build/dev-ci`;
- a `main` push updates/replaces only `build/main`;
- every publication preserves the two unrelated sibling scopes;
- no lane derives membership by hand in Forge;
- source freshness, deletion reconciliation and generated-branch race handling
  remain generic CAD-CI responsibilities;
- development scopes are replace/reconcile scopes, not append-only history.

Once this model is proven, Forge no longer needs durable `build/pr/*` scopes.

### Pages layout

Keep one generated `gh-pages` branch.

The stable site stays at the branch root. Development previews are sibling
subtrees:

```text
/                 <- main stable site
/dev-cad/         <- dev-cad preview
/dev-ci/          <- dev-ci preview
```

Required behavior:

- a `dev-cad` publication replaces only `/dev-cad/`;
- a `dev-ci` publication replaces only `/dev-ci/`;
- a `main` publication replaces the stable root while preserving both dev
  previews;
- a dev publication must never alter the stable root;
- one dev lane must never alter the other dev preview;
- the live GitHub Pages source remains the single generated `gh-pages` branch
  after #366.

Development previews are convenience/integration views. They are not stable
verification truth and must not be used as the source for `build/main`.

### Development-lane update flow

For either development lane:

```text
feature branch
  -> PR to dev_<lane>
  -> verification only
  -> merge
  -> push dev_<lane>
       -> selected CAD-CI run
       -> fetch current build/dev_<lane>
       -> reconcile affected items
       -> publish build/dev_<lane>
       -> build site from that exact prepared scope
       -> publish gh-pages/dev_<lane>
```

This keeps the durable preview representative of the branch head while avoiding
per-PR generated-state accumulation.

### Promotion to main

A development lane reaches stable `main` through an explicit promotion PR:

```text
dev-cad or dev-ci
  -> promotion PR to main
  -> complete validation against the accepted development state
  -> merge to main
  -> main push updates build/main
  -> main push updates stable Pages root
  -> synchronize development lane back to main
```

Merge policy is fixed by branch role:

- short-lived feature/fix PRs into `dev-cad` or `dev-ci` are squash-merged;
- promotion PRs from `dev-cad` or `dev-ci` into `main` use a normal merge
  commit and are never squash-merged.

The squash on the development lane keeps each individual work item compact.
The normal merge into `main` preserves the ancestry of the long-lived
development branch, so the promoted lane is genuinely contained by main and
can be cleanly synchronized/fast-forwarded to the resulting main head.

After a promotion, the promoted dev branch must be synchronized to the new main
head before accepting work that assumes the promoted state. The other dev lane
must also regularly incorporate main so the two integration lanes do not drift
indefinitely from stable.

### Isolation invariants

The new architecture is accepted only when all of these are proven:

1. a PR cannot write durable build or Pages state;
2. `dev-cad` cannot modify `build/main`, `build/dev-ci` or stable Pages;
3. `dev-ci` cannot modify `build/main`, `build/dev-cad` or stable Pages;
4. `main` publication preserves both development scopes/previews;
5. each lane has its own concurrency group so one lane cannot cancel another;
6. generated publication retries remain safe when two lanes publish close
   together;
7. development-scope deletion/reconciliation uses the same released generic
   planner semantics as main;
8. a promotion to main is validated before stable publication;
9. old per-PR scopes can be removed without losing accepted lane evidence.

## Ownership and implementation order for #572

Do not implement named development scopes as Forge-local Git-tree logic.

The implementation sequence is:

1. [complete] Generic named complete build/Page scopes are released in
   `lib.py.cad.ci 0.9.2`.
2. [complete] The thin public surface is released in
   `tool.cad.ci 0.16.1`.
3. [complete] External black-box acceptance is green in
   `tool.cad.ci.test` PR #61.
4. [#572, now] Change Forge event wiring so pushes on `main`, `dev-cad` and
   `dev-ci` publish only their corresponding complete scope.
5. [#572] Remove durable PR publication; PRs become verification-only.
6. [#572] Make Forge site generation consume either `main` or one named
   complete scope and record the actual evidence scope.
7. [#572] Publish dev Pages to their named subtree and make stable publication
   preserve both dev subtrees.
8. [#572] Create `dev-cad` and `dev-ci` from one known-good main commit only
   after the workflow supports them.
9. [#572] Bootstrap and verify both development scopes.
10. [#572] Prove dev-to-main promotion and post-promotion synchronization.
11. [post-#572] Reassess every open issue, assign workstream + priority, and
    update this plan from the new branch topology.
12. [#572/#481] Remove obsolete `build/pr/*` state and then clean stale source
    branches using the final keep-set.

The intended permanent branch keep-set after the migration is at least:

```text
main
dev-cad
dev-ci
build
gh-pages
```

The temporary rollback branch remains outside that permanent set until #366 has
been live and stable long enough to make an explicit retention decision.

## Open issue assessment — 2026-11-21

| Issue | Status | Assessment |
| --- | --- | --- |
| #572 Introduce long-lived dev-cad/dev-ci integration lanes | now | Generic named-scope stack is released and externally accepted. Implement and bootstrap the two Forge lanes now. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | separate after lane bootstrap | Generated output is ready, but the public Pages cut-over stays independent from #572 and is not performed during the migration. |
| #481 Remove stale Forge development branches | after #572 | Cleanup should use the final branch keep-set, so perform it after the two new long-lived dev branches are proven. |
| #574 Restore structured Raw test files presentation on all Verification case pages | post-migration triage | Generic site-template regression discovered during review; assign final workstream/priority after the lane proof. |
| #576 Skip expensive CAD-CI and stable-site jobs for docs-only pull requests | post-migration triage (dev-ci candidate) | Docs-only PR #575 proved avoidable bootstrap/runner overhead; classify under the new CI lane after #572 is live. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by released runtime images, batching and later one-runner timing work. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to the superseded Qualification architecture and old reuse strategy. |
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
| #81 Support inline AnchorFrame references for rotated occurrences | later | `custom-anchor` remains the expected-rejection fixture until this capability exists. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Major Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:

`#572 development lanes -> post-migration issue/workstream reprioritization -> #366 public cut-over / #481 cleanup as separately scheduled work`.
