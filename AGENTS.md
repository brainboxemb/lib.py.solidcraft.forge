# Forge repository architecture

This file summarizes the current repository structure. Historical documents may
describe earlier architecture.

## Repository role

`lib.py.solidcraft.forge` contains the reusable Python Forge API, command
compiler/runners, unit tests, release-verification examples and model
verification fixtures.

Product CAD models are maintained in `2026-011-02.cad.solidcraft`.

## Current CI files

The active CI structure is defined by:

- `.github/workflows/scpf.yml`
- `cad-ci.yml`
- `scpf/ci.yml`
- migrated `examples/<model>/ci.yml` files
- `scripts/tool_ci.py`
- `scripts/tool_verify.py`
- `scripts/forge_example.py`
- `scripts/model_verify.py`
- `scripts/solidcraft_runtime.py`
- `docker/solidcraft_runtime/`

The generic planner/executor is `tool.cad.ci`.

## Current verification steps

The Forge tool item runs:

```text
tool_build -> tool_test -> tool_verify
```

`tool_verify` is Forge release verification using the fixed representative
example set. It is not a stage that every model item must run.

Migrated model items use `model_verify`. That step compiles the model with the
exact built Forge wheel and verifies the resulting model in SolidCraft.

At the current migration point, `simple-box` is the first model-verification
item. Issue #395 tracks the next ten historical qualification models.

## Model ownership

A migrated model may contain:

```text
examples/<model>/
  ci.yml
  model.yml
  scpf/
    model.py
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

Native-model expectations and mutations live in the model verification code.
Example-owned command-contract tests remain under `examples/<example>/tests/`
where they are used by Forge release verification or other focused tests.

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
- the fixed release examples — Forge `tool_verify`.
- `examples/<model>/verification/` — native SolidCraft model checks.

`docs/design/test-architecture.md` contains the detailed test split.

## Public API documentation

The public API source split is documented in
`docs/09-documentation-architecture.md`.

Exact public names, signatures, defaults and enum values come from the Python
implementation and its docstrings. Cross-object rules are documented in
`docs/05-cad-api-design.md`.

`docs/agent/forge-api.json` is generated from the public API.

## Current work

`docs/plan.md` contains only unfinished repository work. Completed plan
sections are removed after their corresponding change is merged.

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
