# Development

## Branches

Work from `dev` on a short-lived issue/fix/feature/docs/chore branch for normal product development. Long-running research uses permanent `exp`; temporary work targeting that line uses the same prefixes and targets `exp`. Keep `build.yml.branch` exact and select the smallest library/modules/models required.

After green checks, use the repository merge policy to squash temporary work into `dev` or `exp`. Synchronization `dev -> exp` and completed-experiment integration `exp -> dev` use merge commits and full PR qualification. `exp -> main` is forbidden. Promotion from `dev` to `main` remains the only product stabilization path and uses a merge commit.

Release preparation is separate. Create `release/vX.Y.Z` from stable `main`,
change only `CHANGELOG.md` plus `cadlib/pyproject.toml:project.version`, and
open that branch directly against `main`. The release lane runs the library
and release capability only, preserves the prior full stable CAD evidence, and
publishes from exact current `main`. After publication synchronize
`main -> dev` through `/merge`; do not rebase `dev`.

## Tests

`cadlib/tests` contains package-owner tests only. Tests that require a physical model fixture belong with that model migration; see `docs/migration-tests.md`.

Generic module tests execute from module-local source. Real CAD work is qualified in the two immutable runtime roles.

## Model migration

For each migrated physical model:
1. identify historical SCPF source and expectations;
2. classify package vs model vs generic capability ownership;
3. place reference implementations inside the same model owner where required;
4. migrate the smallest coherent slice;
5. compare OLD and NEW command/geometry/native/verification evidence;
6. only expand after acceptance.

Do not copy historical Forge scripts/CI/site code unless behavior remains Forge-specific after comparison with the corrected template capability.
