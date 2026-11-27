# Agent guidance

Read `docs/README.md`, the current `main` version of `docs/plan.md`, `docs/architecture.md`, `docs/requirements.md` and `docs/handoff.md` before making repository changes. Ignore `docs/legacy/` as current guidance.

## Plan ownership

`docs/plan.md` is repository governance and is canonical on **main**.
Always read the current main version before choosing work, even when working on
`dev` or `exp` and their local copy is behind.

- reconcile plan state on a short-lived docs branch created from `main`;
- merge that governance PR back to `main` only through `/merge`;
- do not author competing normal or experimental plan state directly on
  `dev` or `exp`;
- accepted governance reaches permanent development lanes through their normal
  merge-policy synchronization checkpoints.

## Branch policy

- `main`: stable integration only.
- `dev`: normal integration branch.
- `exp`: optional permanent experimental integration branch; never a release source.
- normal short-lived product work branches use `issue/`, `fix/`, `feature/`, `docs/` or `chore/` and squash into `dev` or `exp` according to their intended integration line; the canonical `docs/plan.md` reconciliation exception is a short-lived docs branch from `main` back to `main`.
- `dev -> exp` synchronization and completed `exp -> dev` integration use merge commits; `exp -> main` is forbidden.
- explicit product promotion `dev -> main` uses a merge commit.
- release preparation uses `release/vX.Y.Z` created from stable `main`; only `CHANGELOG.md` and `cadlib/pyproject.toml:project.version` may change.
- `release/* -> main` uses squash through the merge policy.
- after a stable-only release commit, synchronize `main -> dev` with a merge commit; never rebase the shared permanent branch.
- never delete `main`, `dev`, `exp`, `build` or `gh-pages`.

### Mandatory merge execution rule

This repository deliberately does **not** let an agent choose the merge method.

For every source-branch integration:

- normal short-lived branch -> `dev` or `exp`;
- canonical governance docs branch -> `main`;
- `dev` -> `exp` and `exp` -> `dev`;
- `release/*` -> `main`;
- explicit product promotion `dev` -> `main`;
- stable synchronization `main` -> `dev`;

an agent MUST post `/merge` on the pull request and let
`.github/workflows/merge-policy.yml` choose and execute the merge.

An agent MUST NOT:

- call GitHub's direct merge API;
- enable or use auto-merge;
- use a UI/manual merge fallback;
- manually choose squash, merge or rebase.

If `/merge` fails, stop the integration and repair the merge-policy path.
Never bypass the policy.

A genuinely conflicted **direct permanent-branch** PR may use the policy-owned
reviewed `/merge-resolved` recovery only after a separate same-repository
`resolve/*` PR has exposed the exact combined tree and passed central CI.
The resolution PR is review-only and must never be merged normally. Do not use
this path for temporary, release or main-governance PRs.

Matching work-branch `build.yml` controls explicit library/module/model selection. `dev` and `exp` use incremental selection since the last successful run on their own branch. Product-changing `main` commits and `dev -> main` promotions run full. Validated release-only PRs/pushes run library + release only and preserve the previous full stable CAD evidence.

## Ownership

`cadlib/` owns the public `scpf` package. Do not rename the import, distribution or public API merely to fit the template.

`models/<id>/` is the physical CAD owner, matching `template.cad.model-project`. One owner may contain multiple engine implementations. Never create sibling owners merely to represent CadQuery, build123d, PythonSCAD, pyBOSL2, SolidCraft or SCPF.

`model.yml.purpose` may contain `example`, `verification`, or both. `[example, verification]` is valid.

Keep generic mechanics in their owning modules:
- builders build one explicit implementation source;
- verification checks explicit artifacts against owner-local expectations;
- preview renders already-built artifacts;
- Pages reads durable evidence and never executes CAD.

Central CI schedules model owners, implementations and runtime roles but must not contain engine-specific branches.

Pull requests run central `ci` only. Permanent `dev`/`main`/`exp` events run one `build` job that performs qualification and durable publication, then dispatches the independent Pages workflow without waiting for it. Do not reintroduce separate permanent-branch `publish-build` or `dispatch-pages` jobs inside CI.

## Release policy

A release is an explicit repository-owner action on a normal issue. Do not
create tags or GitHub Releases directly.

Release preparation is not product promotion:

1. create `release/vX.Y.Z` from current stable `main`;
2. change only `CHANGELOG.md` and the `project.version` value in
   `cadlib/pyproject.toml`;
3. open `release/vX.Y.Z -> main`;
4. CI must select only `modules/release` plus the library owner and no model
   owners;
5. merge only through `/merge`;
6. the stable release-only push must not replace the previous full
   `build/main` product evidence;
7. comment `/release vX.Y.Z <exact-40-character-main-sha>` on the release
   issue;
8. after publication synchronize `main -> dev` through `/merge`.

The generic release validator proves that the retained full stable product
baseline is an ancestor of the exact release SHA and that every first-parent
commit since it is linear release metadata only. Forge-specific metadata
validation remains in `cadlib/release.py`: package version, dated changelog,
active blockers and `TESTED_SOLIDCRAFT_VERSION`.

Released `tool.py.lib.ci` still owns current-main validation, annotated tags,
GitHub Releases, idempotency and issue reporting. Pages is never release
evidence. The migrated package version `0.15.0` remains a historical baseline
and must not be published as a canonical Forge release.

## Runtime policy

Preserve exactly two released CAD runtime roles:
- `reference`;
- `solidcraft`.

SolidCraft builds in the lightweight SolidCraft role; generic mesh verification runs in the reference role. Do not add a third verification image.

## Historical migration evidence

The archived `brainboxemb/lib.py.solidcraft.forge.OLD` repository is a
read-only A/B and provenance reference. It is not an active integration target.

The completed migration established the current owner/module architecture. New
work must preserve the accepted boundaries rather than reviving historical
Forge-local CI/scripts/site machinery.

Reference-engine implementations belong inside the same model owner as the
SCPF/SolidCraft path.

Generated CAD artifacts remain owned by `build/<scope>/models/...`. Pages
links them; it must not duplicate generated STL/PNG/SC/command evidence into
`gh-pages`.
