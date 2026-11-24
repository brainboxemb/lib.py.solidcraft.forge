# Development

## Branches

Work from `dev` on a short-lived issue/fix/feature/docs/chore branch. Keep `build.yml.branch` exact and select the smallest owners required by the work.

After green checks, comment `/merge` on the PR to squash into `dev`. Promotion from `dev` to `main` is a full qualification and uses a merge commit.

## Tests

`cadlib/tests` contains package-owner tests only. Tests that require a repository example belong with that example migration; see `docs/migration-tests.md`.

Generic module tests execute from module-local source. Real CAD work is qualified in the two immutable runtime roles. Do not install a second editable SCPF copy to make tests pass.

## Migration work

For each migrated example:
1. identify historical source and expectations;
2. classify package vs example vs generic capability ownership;
3. migrate the smallest coherent slice;
4. compare OLD and NEW evidence;
5. only expand after acceptance.

Do not copy historical Forge scripts/CI/site code unless there is still Forge-specific behavior after comparison with the template capability.
