# Release process

## Version sources

The SCPF package version is defined in `scpf/pyproject.toml`.

SolidCraft compatibility is defined separately in
`scpf/scpf/version.py::TESTED_SOLIDCRAFT_VERSION`.

## Current release state

The previous automatic release-validation/publication path was removed during
the CAD-CI cut-over because it no longer matched the active workflow.

The current `.github/workflows/scpf.yml` runs Forge through `tool.cad.ci`.
It does not currently create Git tags or GitHub Releases.

Build, Pages and release publication migration is tracked in issue #366.

## Normal development

User-visible changes are recorded under `## [Unreleased]` in
`CHANGELOG.md`.

Package-version changes are intentional release-preparation changes rather than
ordinary feature changes.

A change to `TESTED_SOLIDCRAFT_VERSION` represents a SolidCraft compatibility
change and requires native model verification in the current architecture.

## Preparing a future release

Until publication automation is restored, release preparation consists of the
source changes only:

1. choose the next semantic package version;
2. update `scpf/pyproject.toml`;
3. move accumulated changelog entries into a dated version section;
4. create a new `[Unreleased]` section;
5. change the tested SolidCraft version only when compatibility intentionally changes.

A merged version bump by itself does not currently publish a GitHub Release.

When automated publication is restored through issue #366, this document should
be updated from the implemented workflow.
