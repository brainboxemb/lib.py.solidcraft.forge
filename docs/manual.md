# Forge NEW manual

## Working branches

Create work from `dev`, set the exact branch in `build.yml`, select the smallest useful owners, and squash to `dev` after qualification. Promote `dev -> main` only with a full-green promotion run.

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

The owner root exposes canonical artifacts from its configured primary implementation. Pages reads durable build evidence and does not rebuild CAD. For implementations with named verification stages, the model page renders each stage status and links its stage-local durable report while retaining the aggregate verification status.

## Migration checks

For every expansion slice:
1. run the historical Forge reference for the selected physical owners;
2. run NEW with the same intent and expectations;
3. compare generated commands and geometry where applicable;
4. compare native/saved-design semantics where the old case claims them;
5. retain both results long enough to diagnose drift;
6. only then expand the selected owner set.
