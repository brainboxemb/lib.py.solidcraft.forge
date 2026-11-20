# Forge release

This document describes the repository's current package-release contract.

## Version sources

The SCPF package version is defined in `scpf/pyproject.toml`.

SolidCraft compatibility is defined separately in
`scpf/scpf/version.py::TESTED_SOLIDCRAFT_VERSION`.

A package version change and a tested-SolidCraft-version change are different
decisions and must not be coupled accidentally.

## Current release state

The active Forge workflow is `.github/workflows/scpf.yml`, delegated through
released `tool.cad.ci`.

That workflow currently verifies source and model items; it does not by itself
create a Git tag or GitHub Release for SCPF.

Build/Pages/release publication migration remains tracked by issue #366. Until
that work is complete, a version bump on main is source release preparation,
not proof that a GitHub Release was published.

## Development changelog

User-visible changes are recorded under `## [Unreleased]` in `CHANGELOG.md`.

Do not bump the package version for ordinary development commits merely to make
CI move forward.

## Preparing a package release

When a package release is intentionally prepared:

1. choose the next semantic package version;
2. update `scpf/pyproject.toml`;
3. move the relevant `CHANGELOG.md` entries from `[Unreleased]` into a
   dated version section;
4. create a fresh `[Unreleased]` section;
5. change `TESTED_SOLIDCRAFT_VERSION` only when SolidCraft compatibility
   intentionally changes;
6. run the current Forge/CAD-CI verification path against the exact release
   source.

When automated publication is restored, this document must describe the
implemented release path rather than a planned one.

## Related primary documents

- [API](api.md)
- [Design](design.md)
- [Development](development.md)
- [Plan](plan.md)
- [Requirements](requirements.md)
