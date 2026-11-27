# Forge release procedure

Forge releases are published only from qualified stable `main`. Product
stabilization and release metadata are separate operations.

## Product stabilization

Product changes normally integrate through `dev`. A release candidate product
state reaches `main` through the repository merge policy with the required
stable build evidence.

`exp` is never a release source.

## Release preparation

Create `release/vX.Y.Z` from the exact qualified `main` head. The release
branch may change only:

- `CHANGELOG.md`;
- `cadlib/pyproject.toml:project.version`.

Open that branch directly against `main` and integrate only through
`/merge`.

A valid release-only run selects the library plus the release capability and
zero model owners. It preserves the previous full `build/main` product
baseline rather than rebuilding unchanged CAD owners.

## Forge metadata validation

`cadlib/release.py` validates:

- requested package version;
- matching dated changelog section;
- active blockers from `cadlib/release-blockers.txt`;
- `cadlib/src/scpf/version.py::TESTED_SOLIDCRAFT_VERSION`;
- release notes extracted from the changelog.

The old migrated `0.15.0` baseline is only a lower-bound guard in the
validator; it is not the current release.

## Publication

Publication is explicit from a normal release-tracking issue:

```text
/release vX.Y.Z <exact-40-character-main-sha>
```

The released shared Python-library CI owns tag/release creation, idempotency and
issue reporting. Forge does not duplicate that machinery.

After publication, synchronize `main -> dev` through the merge policy. Never
rebase the shared permanent development branch.

Pages is presentation only and is never package-release evidence.
