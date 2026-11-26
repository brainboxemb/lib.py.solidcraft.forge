# Forge NEW manual

## Working branches

Permanent `workflow_dispatch` runs explicitly qualify the current checked-out permanent branch head instead of trusting an event SHA that can lag immediately after a policy merge. Durable publication remains fail-closed if the branch moves again during the run.


Create normal work from `dev`. Long-running experimental work uses permanent `exp`; temporary work branches squash into the integration line they belong to. Synchronize `dev -> exp` and integrate a completed experiment with `exp -> dev` through merge commits. `exp -> main` and releases from `exp` are forbidden. Set the exact temporary branch in `build.yml` and select the smallest useful owners. Promote `dev -> main` only with a full-green promotion run.

## Library

The public package is under `cadlib/` and imports as `scpf`. A library-only work branch can use:

```yaml
schema: 1
branch: issue/123-change
modules: [ci]
library: true
models: []
tasks: [test]
```

CI tests source directly and builds a qualification wheel. That wheel is not a release.

## Models

`models/<id>/` is the physical owner. One owner contains its `model.yml`, `ci.yml`, implementation sources and model-specific verification expectations.

`model.yml.purpose` may contain one or more purposes:

```yaml
purpose: [example, verification]
```

`example` makes the owner public in Pages; `verification` marks it as qualification material. Both are valid together.

Engine implementations are local to the owner. Never create sibling model directories just to represent SCPF, CadQuery, build123d, PythonSCAD, pyBOSL2 or SolidCraft.

During migration, preserve provenance back to the historical Forge source and behavior until the slice is accepted.

## Runtime roles

Reference engines and generic mesh verification use `cad-reference:v0.3.5`. SolidCraft native execution uses `cad-solidcraft:v0.3.5`. The scheduler derives role ordering from capabilities and starts each required role once.

SCPF compilation is consumer-owned: `builder-scpf` compiles local `scpf` source and delegates the resulting command document to the generic SolidCraft builder.

## Generated output

Permanent successful builds publish to:

```text
build/<source-branch>/models/<owner>/
  result.json
  source.json
  <implementation>/...
```

`main`, `dev` and optional `exp` each own an isolated durable scope. The owner root exposes canonical artifacts from its configured primary implementation. Pages reads durable build evidence and does not rebuild CAD. For implementations with named verification stages, the model page renders each stage status and links its stage-local durable report while retaining the aggregate verification status.

Stable Pages is published at `/`, normal development at `/dev/`, and an existing experimental line at `/exp/` with an explicit experimental banner.

## Pages homepage

Homepage content is declared in `site/home.yml` and generated before Hugo
renders the site. Use `route` for Forge-local destinations so Hugo applies the
active base URL, and `url` for absolute HTTPS destinations such as the
SolidCraft model website. Forge version badges use generated values from
`landing_metadata()`; placeholders such as `${package_version}` are resolved
by Pages before `data/home.json` reaches Hugo.

Do not add Forge labels, copy or destinations directly to
`site/layouts/home.html`. That layout may remain Forge-specific for visual
structure and CSS classes, but it must render the generated manifest.

## Migration checks

For every expansion slice:
1. run the historical Forge reference for the selected physical owners;
2. run NEW with the same intent and expectations;
3. compare generated commands and geometry where applicable;
4. compare native/saved-design semantics where the old case claims them;
5. retain both results long enough to diagnose drift;
6. only then expand the selected owner set.


## Releases

Promote product changes from `dev -> main` separately and only after full
qualification. Prepare `release/vX.Y.Z` from qualified stable `main`; that
branch may change only `CHANGELOG.md` and
`cadlib/pyproject.toml:project.version`, then targets `main` directly
through the normal `/merge` policy.

A metadata-only stable release commit is classified from its single-parent
source delta. This is deliberately identical whether the permanent stable run
arrives as a normal `push` or as merge-policy `workflow_dispatch`. A valid
release-only stable run selects the library plus `modules/release`, selects
zero model owners, records `release_only: true` / `full: false`, and keeps
the previous full `build/main` product scope unchanged. Product paths or a
merge commit fail closed to full qualification.

Publication remains explicit:

```text
/release vX.Y.Z <exact-40-character-main-sha>
```

After publication, synchronize `main -> dev` through merge policy; never
rebase the shared permanent branch.
