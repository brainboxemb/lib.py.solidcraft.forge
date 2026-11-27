# Forge NEW release boundary

Forge NEW has release mechanics, but **no NEW release has been published yet**.

The checked-in package version is currently `0.15.0`. That value preserves the
historical Forge source baseline that was migrated into this repository; it is
not a release claim for Forge NEW. The Forge NEW validator rejects release
requests for `0.15.0` or any older version.

## Ownership

The release path deliberately has three owners.

### Durable qualification — this repository

Normal permanent-branch build publication writes
`build/<scope>/build-plan.json` plus owner evidence. A releasable stable
`build/main` must prove:

- the exact requested source SHA;
- `full: true`;
- `library: true`;
- every active model owner is selected;
- every active model has a passing durable `result.json`;
- every active model's `source.json` points to the exact release source.

`modules/release` checks that evidence. It does not publish anything.

### Forge-specific metadata — `cadlib/release.py`

Forge owns only:

- the package version in `cadlib/pyproject.toml`;
- a dated matching section in `CHANGELOG.md`;
- active blockers in `docs/background/design/release-blockers.txt`;
- `cadlib/src/scpf/version.py::TESTED_SOLIDCRAFT_VERSION`;
- the release notes emitted from the matching changelog section;
- the rule that a Forge NEW release version must be newer than `0.15.0`.

### Publication — released `tool.py.lib.ci`

`.github/workflows/release.yml` delegates publication to released
`tool.py.lib.ci v0.2.1` at exact commit
`58ead6897a4ac8cafef22a3c1f834491bf61568d`.

That shared flow owns:

- strict `/release vX.Y.Z <40-character-sha>` parsing;
- repository-owner enforcement;
- stable-`main` head verification;
- annotated tag creation/verification;
- GitHub Release creation/verification;
- idempotent repeated publication;
- reporting the published release back on the triggering issue.

Forge does not reimplement those mechanics.

## Publishing a future NEW release

A future release starts with an explicit source change:

1. choose a version **newer than 0.15.0**;
2. update `cadlib/pyproject.toml` to that version;
3. move the release content from `[Unreleased]` into a dated
   `## [X.Y.Z] - YYYY-MM-DD` section in `CHANGELOG.md`;
4. make sure `docs/background/design/release-blockers.txt` contains no active
   blocker;
5. merge and promote normally until the exact release commit is stable on
   `main`;
6. require the full stable `build/main` evidence described above;
7. on a normal release-tracking issue, the repository owner comments:

```text
/release vX.Y.Z <exact-40-character-main-sha>
```

Only then may the released shared flow create or verify the annotated tag and
GitHub Release.

## What is not release evidence

Pages is presentation output. `gh-pages`, screenshot jobs and a successful
Hugo build do not qualify a package release.

A normal CI/build run never publishes a package release automatically.
