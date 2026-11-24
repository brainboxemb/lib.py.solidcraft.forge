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
