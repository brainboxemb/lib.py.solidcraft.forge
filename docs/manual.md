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
examples: []
tasks: [test]
```

CI tests source directly and builds a qualification wheel. That wheel is not a release.

## Examples

Each example owns `ci.yml`, `model.yml`, authoring source and verification expectations. Use `purpose: verification` for non-public fixtures. Public examples include `example` in purpose.

During migration, preserve provenance back to the old Forge source/behavior in the issue or example background material until the slice is accepted.

## Runtime roles

Reference engines and generic mesh verification use `cad-reference:v0.3.5`. SolidCraft native execution uses `cad-solidcraft:v0.3.5`. The scheduler derives role ordering from capabilities and starts each required role once.

## Generated output

Permanent successful builds publish to `build/<source-branch>/examples/<id>/`. Pages reads that evidence and publishes stable at `/` and development at `/dev/`.

## Migration checks

For every expansion slice:
1. run the old Forge reference for the selected cases;
2. run NEW with the same intent/expectations;
3. compare generated commands and geometry where applicable;
4. retain both results long enough to diagnose drift;
5. only then expand the selected set.
