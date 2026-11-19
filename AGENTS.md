# Forge repository architecture

This file summarizes the current repository structure. Historical documents may
describe earlier architecture.

## Repository role

`lib.py.solidcraft.forge` contains the reusable Python Forge API, command
compiler/runners, unit tests and small behaviour examples.

Product CAD models are maintained in `2026-011-02.cad.solidcraft`.

## Current CI files

The active CI structure is defined by:

- `.github/workflows/scpf.yml`
- `cad-ci.yml`
- `scpf/ci.yml`
- `examples/<example>/ci.yml`
- `scripts/tool_ci.py`
- `scripts/tool_verify.py`
- `scripts/model_verify.py`
- `scripts/solidcraft_runtime.py`
- `docker/solidcraft_runtime/`

The generic planner/executor is `tool.cad.ci`.

## Current verification steps

The local CAD-CI step vocabulary is:

- `tool_build`
- `tool_test`
- `tool_verify`
- `model_verify`

`tool_verify` checks an example's Forge execution and generated SolidCraft
command contract. `model_verify` checks the resulting model in SolidCraft.

At the current migration point, `simple-box` includes `model_verify`.
Issue #395 tracks the next ten examples.

## Example ownership

A migrated example may contain:

```text
examples/<example>/
  ci.yml
  model.yml
  scpf/
    model.py
  tests/
    test_contract.py
  verification/
    verify_model.py
```

Presentation metadata in `model.yml` uses:

```text
section
title
tagline
description
parameters
stages
```

Command expectations live in the example tests. Native-model expectations and
mutations live in the example verification code.

## SolidCraft runtime

The active native runtime is:

```text
docker/
  solidcraft_runtime/
    Dockerfile
    runtime.json
```

The tested SolidCraft version comes from
`scpf/scpf/version.py::TESTED_SOLIDCRAFT_VERSION`.

The old generated SolidCraft command snapshot and old qualification runtime are
historical and are not part of the current runtime path.

## Test ownership

- `scpf/tests/` — reusable Forge API/compiler tests.
- `examples/<example>/tests/` — example-specific command-contract tests.
- `examples/<example>/verification/` — native SolidCraft model checks.

`docs/design/test-architecture.md` contains the detailed test split.

## Public API documentation

The public API source split is documented in
`docs/09-documentation-architecture.md`.

Exact public names, signatures, defaults and enum values come from the Python
implementation and its docstrings. Cross-object rules are documented in
`docs/05-cad-api-design.md`.

`docs/agent/forge-api.json` is generated from the public API.

## Generated output and Pages

Build and Pages publication are currently being migrated in issue #366.

The existing `build` and `gh-pages` branches are generated output from the
earlier publication system. Current development status is determined from source
and the current CAD-CI run.

## Release state

The package version is stored in `scpf/pyproject.toml`.

The previous automatic release-validation/publication path is no longer active.
Issue #366 tracks publication integration with the current CAD-CI architecture.

## Historical documents

`docs/changes/` and several older audit/remediation documents under
`docs/design/` describe earlier development states. Their old terminology is
historical rather than an active CI contract.
