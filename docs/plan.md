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
`backup/gh-pages-before-f11-2026-11-20` until #366 performs the explicit
public cut-over and live-route verification.

The current source workflow is still intentionally simple: pull requests are
normally opened against `main`, PR evidence may be published under
`build/pr/<number>`, and a merged main change immediately participates in the
stable build/Pages flow.

That topology is now proven, but it is not the intended long-term development
model. It couples ordinary development too closely to the stable branch and
creates durable per-PR scopes that can remain behind after interrupted work.

Issue #572 defines the next architecture after #366: keep `main` stable and
introduce two long-lived integration lanes, `dev_cad` and `dev_ci`.

## Immediate goal

Finish #366 without changing the now-proven publication architecture:

1. switch the live GitHub Pages source from the backup branch to generated
   `gh-pages`;
2. verify the public root, all required Verification routes and representative
   case pages;
3. verify legacy Qualification redirects;
4. keep the rollback branch until the live cut-over is proven.

Do not combine the live cut-over with the development-lane migration.

## Next architecture — long-lived development lanes

After #366 is proven live, Forge should use three long-lived source branches:

```text
main
dev_cad
dev_ci
```

Their responsibilities are:

- `main` — stable/production integration only. A merge to `main` may update
  the durable main build and the stable Pages root.
- `dev_cad` — integration lane for Forge API, compiler, model, verification
  data and other CAD/product work.
- `dev_ci` — integration lane for Forge-side CI/infrastructure integration.

`dev_ci` does not change repository ownership boundaries. Generic CAD-CI
functionality still belongs in `lib.py.cad.ci` and `tool.cad.ci`, is tested
and released there, and is then consumed/qualified through Forge's `dev_ci`
lane.

### Pull-request rule

Normal feature/fix pull requests target one development lane and perform
verification only.

They must not create durable per-PR build or Pages publication.

Target model:

```text
feature/fix branch
  -> PR to dev_cad or dev_ci
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
dev_cad/
dev_ci/
```

Each scope is a complete reconciled durable baseline for that source lane.

Required behavior:

- a `dev_cad` push updates/replaces only `build/dev_cad`;
- a `dev_ci` push updates/replaces only `build/dev_ci`;
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
/dev_cad/         <- dev_cad preview
/dev_ci/          <- dev_ci preview
```

Required behavior:

- a `dev_cad` publication replaces only `/dev_cad/`;
- a `dev_ci` publication replaces only `/dev_ci/`;
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
dev_cad or dev_ci
  -> promotion PR to main
  -> complete validation against the accepted development state
  -> merge to main
  -> main push updates build/main
  -> main push updates stable Pages root
  -> synchronize development lane back to main
```

Promotion from a long-lived dev branch should use a normal merge commit rather
than squash merge. The purpose is to keep the dev branch in main ancestry so it
can be cleanly fast-forwarded/synchronized to the resulting main head.

Normal short-lived feature PRs into `dev_cad` or `dev_ci` may still use
squash merge.

After a promotion, the promoted dev branch must be synchronized to the new main
head before accepting work that assumes the promoted state. The other dev lane
must also regularly incorporate main so the two integration lanes do not drift
indefinitely from stable.

### Isolation invariants

The new architecture is accepted only when all of these are proven:

1. a PR cannot write durable build or Pages state;
2. `dev_cad` cannot modify `build/main`, `build/dev_ci` or stable Pages;
3. `dev_ci` cannot modify `build/main`, `build/dev_cad` or stable Pages;
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

1. [#366] Finish and prove the current live Pages cut-over first.
2. [#572] Specify generic named durable-scope behavior in
   `lib.py.cad.ci`.
3. [#572] Implement/test named-scope fetch, reconcile and publication in
   `lib.py.cad.ci`.
4. [#572] Expose the released behavior through `tool.cad.ci`; qualify it in
   the external CAD-CI acceptance repository.
5. [#572] Release the accepted generic stack.
6. [#572] Change Forge event wiring so pushes on `main`, `dev_cad` and
   `dev_ci` publish only their corresponding named scope.
7. [#572] Remove durable PR publication from the Forge PR path; PRs become
   verification-only.
8. [#572] Add scoped Pages publication preserving stable root and unrelated dev
   previews.
9. [#572] Create `dev_cad` and `dev_ci` from one known-good main commit only
   after the workflow supports them.
10. [#572] Bootstrap and verify both development scopes.
11. [#572] Prove dev-to-main promotion and post-promotion branch
    synchronization.
12. [#572/#481] Remove obsolete `build/pr/*` state and then clean stale source
    branches using the new keep-set.

The intended permanent branch keep-set after the migration is at least:

```text
main
dev_cad
dev_ci
build
gh-pages
```

The temporary rollback branch remains outside that permanent set until #366 has
been live and stable long enough to make an explicit retention decision.

## Open issue assessment — 2026-11-21

| Issue | Status | Assessment |
| --- | --- | --- |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | now | Generated main/build/Pages output is fully repaired and audited. Remaining work is the explicit live Pages-source cut-over and public verification. |
| #572 Introduce long-lived dev_cad/dev_ci integration lanes | next | Planned post-#366 architecture. Replace direct-to-main daily development and durable per-PR scopes with two isolated development lanes and named durable build/Pages scopes. |
| #481 Remove stale Forge development branches | after #572 | Cleanup should use the final branch keep-set, so perform it after the two new long-lived dev branches are proven. |
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

`#366 live cut-over -> #572 development lanes -> #481 stale-branch cleanup`.
