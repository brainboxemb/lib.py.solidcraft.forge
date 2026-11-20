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
- `.github/workflows/solidcraft-runtime.yml`
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
exact built Forge wheel, produces the initial native SolidCraft model and then
delegates model verification to released `lib.py.cad.verfication`.

A declaratively migrated model keeps only model-specific verification data in
`verification/verify.py`; it does not own a procedural verification CLI.
During staged migration it uses `scripts/model_verify_declarative.py`; older
models retain `scripts/model_verify.py` until their own migration change.

All 32 historical model items have native `model_verify` coverage and
model-local independent-reference geometry contracts. The shared reference item
runs PythonSCAD, pyBOSL2, CadQuery and build123d for the complete catalog.
Issue #378 now continues with visual, diagram and summary verification.

## Model ownership

A declaratively migrated model may contain:

```text
examples/<model>/
  ci.yml
  model.yml
  scpf/
    model.py
  verification/
    verify.py
    <model-specific command/data files>
```

Older models may temporarily retain `verification/verify_model.py` until their
individual migration PR. Do not add new shared verification mechanics to those
files.

Presentation metadata in `model.yml` uses:

```text
section
title
tagline
description
parameters
stages
```

Native-model expectations and mutation definitions live as model-specific data
in the model verification definition.
Example-owned command-contract tests remain under `examples/<example>/tests/`
where they are used by Forge release verification or other focused tests.

## SolidCraft runtime

The active native runtime is built and published only by the separate
`.github/workflows/solidcraft-runtime.yml` workflow.

The runtime build definition is:

```text
docker/
  solidcraft_runtime/
    Dockerfile
    runtime.json
```

Normal Forge CI does not derive its runtime from those files. Root
`cad-ci.yml` declares `FORGE_RUNTIME_IMAGE` and `SOLIDCRAFT_VERSION`; the
released CAD-CI library injects them into consumer commands.

`scpf/scpf/version.py::TESTED_SOLIDCRAFT_VERSION` remains the package-level
compatibility guard. Forge tests require the explicit CI version and runtime
reference to remain compatible with the current runtime build definition.

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

## Repository plan

`docs/plan.md` is the current source of truth for unfinished repository work.

Keep it as a current snapshot, not as historical documentation:

- state the current goal and execution order;
- include every open issue in an issue assessment snapshot;
- give each open issue an explicit status such as `now`, `later`, `blocked`, `probably obsolete`, or `effectively complete but still open`;
- explain briefly why that status applies;
- identify dependencies or blockers between issues;
- remove completed work from the active execution sections after merge/release, while keeping the issue assessment current.

Issues contain detail and history. README and design/requirements documents describe stable purpose and behavior. The plan tells an agent what work is actually current and what should happen next.

