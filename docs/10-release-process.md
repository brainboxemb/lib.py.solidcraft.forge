# Release process

SCPF uses semantic versioning for the Python library and a separate qualified
version for the SolidCraft engine.

## Version sources

There is one package-version source:

- `scpf/pyproject.toml` -> SCPF semantic version, for example `0.1.1`.

SolidCraft compatibility is deliberately separate:

- `scpf/scpf/version.py` -> `TESTED_SOLIDCRAFT_VERSION`, for example
  `0.42.0`.

Do not encode the SolidCraft version into the SCPF semantic version and do not
duplicate either value in another source file.

## During normal development

Keep the package version at the latest released SCPF version.

Record user-visible changes under `## [Unreleased]` in `CHANGELOG.md`.
Do not create ad-hoc tags or releases from feature branches.

## Preparing a release

Create a release PR on a branch matching `qualification/**` so the complete
qualification workflow runs before merge.

The release PR must:

1. choose the next semantic version;
2. change only `scpf/pyproject.toml` for the SCPF package version;
3. move the accumulated changelog items into a dated
   `## [X.Y.Z] - YYYY-MM-DD` section;
4. leave a fresh `[Unreleased]` section above it;
5. keep `TESTED_SOLIDCRAFT_VERSION` unchanged unless SolidCraft compatibility
   has separately been requalified;
6. have no active non-comment lines in
   `docs/design/release-blockers.txt`;
7. pass the full Q1-Q6 qualification on the exact release-PR head.

## Publishing after merge

The release PR already passed full Q1-Q6 before merge. After squash merge, the
release workflow compares the verified release-head tree with the resulting
`main` tree.

When those trees are identical and the qualification toolchain identity still
matches, reuse the successful full qualification. Do not run full Q1-Q6 again
only because squash merge created a different commit SHA. Promote/rebind the
verified evidence to the current `main` commit and publish from that evidence.

Run full Q1-Q6 on `main` only when no valid full qualification exists for the
exact merged source tree/toolchain, or when the merge tree differs from the
qualified release tree.

The generic `Publish SCPF release` workflow then:

1. reads the package version from `scpf/pyproject.toml`;
2. does nothing if that version already has a published GitHub Release;
3. requires its target SHA to be the current `main` HEAD;
4. refuses the release when `docs/design/release-blockers.txt` contains an
   active non-comment blocker;
5. requires a dated matching changelog section;
6. records the currently qualified SolidCraft version and reused/full
   qualification identity;
7. creates an annotated `vX.Y.Z` Git tag on that exact commit;
8. creates the GitHub Release using that changelog section as release notes.

A release therefore cannot publish without a successful full Q1-Q6
qualification for the exact source tree/toolchain being released.

## Downstream pinning

Downstream CAD repositories should record both:

- the semantic SCPF release, such as `SCPF 0.1.1`;
- the exact commit SHA behind that tag in their dependency lock/pin file.

This keeps human-readable release intent and reproducible source checkout
together.

Downstream native CI should additionally verify that
`scpf.version.TESTED_SOLIDCRAFT_VERSION` matches the SolidCraft version used
for that CAD baseline.

## Patch releases

Use a patch release when the public modelling API is unchanged but the release
contains compatible fixes, documentation/tooling corrections, or release
infrastructure changes.

For example, `0.1.1` formalizes the release system after the initial
`v0.1.0` release. The `v0.1.0` tag remains historical and is never moved or
rewritten.
