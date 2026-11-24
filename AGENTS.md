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

Matching work-branch `build.yml` controls explicit selection. `dev` uses incremental selection since the last successful integration run. `main` and promotion PRs run full.

## Ownership

`cadlib/` owns the public `scpf` package. Do not rename the import, distribution or public API merely to fit the template.

Keep generic mechanics in their owning modules:
- builders build one explicit source;
- verification checks explicit artifacts against explicit expectations;
- preview renders already-built artifacts;
- Pages reads durable evidence and never executes CAD.

Central CI schedules capabilities and runtime roles but must not contain engine-specific CadQuery/build123d/PythonSCAD/pyBOSL2/SolidCraft branches.

## Runtime policy

Preserve exactly two released CAD runtime roles:
- `reference`;
- `solidcraft`.

SolidCraft builds in the lightweight SolidCraft role; generic mesh verification runs in the reference role. Do not add a third verification image.

## Migration discipline

The old `lib.py.solidcraft.forge` repository is a read-only migration reference during this work. Do not make compensating changes there from this repository task.

Migrate examples in controlled slices: one, then five, then ten, then the remaining graph. At each slice compare source behavior, generated commands, native/STL output, verification evidence and presentation before expanding.

Do not bulk-copy old Forge CI/scripts/site machinery. First determine whether the new template capability replaces it. Preserve only Forge-specific behavior that still has an owner after that comparison.
