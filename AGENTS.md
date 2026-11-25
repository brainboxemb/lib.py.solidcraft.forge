# Agent guidance

Read `docs/requirements.md`, `docs/design.md`, `docs/plan.md` and `docs/handoff.md` before making repository changes.

## Branch policy

- `main`: stable integration only.
- `dev`: normal integration branch.
- short-lived work branches use `issue/`, `fix/`, `feature/`, `docs/` or `chore/`.
- squash short-lived branches into `dev`.
- promote `dev -> main` with a merge commit.
- do not back-merge `main -> dev` unless there is a real stable-only change.
- never delete `main`, `dev`, `build` or `gh-pages`.

### Mandatory merge execution rule

This repository deliberately does **not** let an agent choose the merge method.

For every source-branch integration:

- short-lived branch -> `dev`;
- `dev` -> `main`;
- exceptional `main` -> `dev`;

an agent MUST post `/merge` on the pull request and let
`.github/workflows/merge-policy.yml` choose and execute the merge.

An agent MUST NOT:

- call GitHub's direct merge API;
- enable or use auto-merge;
- use a UI/manual merge fallback;
- manually choose squash, merge or rebase.

If `/merge` fails, stop the integration and repair the merge-policy path.
Never bypass the policy.

Matching work-branch `build.yml` controls explicit library/module/model selection. `dev` uses incremental selection since the last successful integration run. `main` and promotion PRs run full.

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

Pull requests run central `ci` only. Permanent `dev`/`main` events run one `build` job that performs qualification and durable publication, then dispatches the independent Pages workflow without waiting for it. Do not reintroduce separate permanent-branch `publish-build` or `dispatch-pages` jobs inside CI.

## Release policy

A release is an explicit repository-owner action on a normal issue. Do not create tags or GitHub Releases directly.

The release path is:

- stable `main` already has exact durable `build/main` evidence;
- comment `/release vX.Y.Z <exact-40-character-main-sha>` on the release issue;
- `.github/workflows/release.yml` checks the durable library/model evidence;
- Forge-specific metadata validation runs from `cadlib/release.py`;
- released `tool.py.lib.ci` owns stable-head validation, annotated tags, GitHub Releases, idempotency and issue reporting.

Pages is never release evidence. The migrated package version `0.15.0` is a historical baseline and must not be published as a NEW release.

## Runtime policy

Preserve exactly two released CAD runtime roles:
- `reference`;
- `solidcraft`.

SolidCraft builds in the lightweight SolidCraft role; generic mesh verification runs in the reference role. Do not add a third verification image.

## Migration discipline

The old `lib.py.solidcraft.forge` repository is a read-only migration reference during this work.

Migrate physical models in controlled slices: one, then five, then ten, then the remaining graph. At each slice compare SCPF behavior, generated commands, native/STL output, verification evidence and presentation before expanding.

Reference-engine implementations belong inside the same model owner as the SCPF/SolidCraft path.

Do not bulk-copy old Forge CI/scripts/site machinery. First determine whether a corrected template capability replaces it.

Generated CAD artifacts remain owned by `build/<scope>/models/...`. Pages links them; it must not duplicate generated STL/PNG/SC/command evidence into `gh-pages`.
