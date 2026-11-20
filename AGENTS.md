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
- `ci/forge-tests/ci.yml`
- `ci/forge-release/ci.yml`
- migrated `examples/<model>/ci.yml` files
- `scripts/tool_ci.py`
- `scripts/tool_verify.py`
- `scripts/forge_example.py`
- `scripts/model_verify.py`

The generic planner/executor is `tool.cad.ci`.

During staged model verification, Forge may declare item-level `process` state in
`examples/<model>/ci.yml`. Forge does not interpret that field; released
`tool.cad.ci` / `lib.py.cad.ci` own its selection and execution semantics.

## Current verification steps

Forge package CI is split into independent items:

```text
forge-package
  -> forge-tests
  -> forge-release
  -> selected model verification items
```

The arrows mean package-artifact dependency, not one serial release chain.

- `forge-package` builds the exact SCPF wheel once.
- `forge-tests` installs that wheel and runs the reusable Forge unit suite.
- `forge-release` release-verifies that wheel with the fixed representative
  examples.
- each model item depends only on `forge-package` and compiles/verifies with
  that exact wheel.

Model verification must not depend on `forge-tests` or `forge-release`.
Those are independent checks.

Migrated model items use `model_verify`. That step compiles the model with the
exact built Forge wheel, produces the initial native SolidCraft model and then
delegates verification to released `lib.py.cad.verfication`.

A declaratively migrated model keeps only model-specific verification data in
`verification/verify.py`; it does not own a procedural verification CLI.
During staged migration it uses `scripts/model_verify_declarative.py`; older
models retain `scripts/model_verify.py` until their own migration change.

All 32 historical model items have native `model_verify` coverage and
model-local independent-reference geometry contracts. The shared reference item
runs PythonSCAD, pyBOSL2, CadQuery and build123d for the complete catalog.
Issue #378 continues with visual, diagram and summary verification.

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

The reusable SolidCraft CAD runtime is owned, built and released by
`brainboxemb/docker.cad.solidcraft`.

Forge is a consumer only. Root `cad-ci.yml` selects the immutable released
runtime role images:

```text
FORGE_RUNTIME_IMAGE=ghcr.io/brainboxemb/cad-solidcraft:v0.2.0
REFERENCE_RUNTIME_IMAGE=ghcr.io/brainboxemb/cad-reference:v0.2.0
```

Normal SolidCraft model/visual verification uses only
`FORGE_RUNTIME_IMAGE`. Independent PythonSCAD/pyBOSL2/CadQuery/build123d
reference verification uses only `REFERENCE_RUNTIME_IMAGE`.

Forge must not duplicate the runtime Dockerfile, dependency/version pins or
release workflow. Runtime package composition, role boundaries and release
management belong in `docker.cad.solidcraft`.

Libraries used on nearly every verification run, including released
`lib.py.cad.verfication`, may be preinstalled in that runtime for efficiency.
Their implementation ownership remains with their own repositories.

`scpf/scpf/version.py::TESTED_SOLIDCRAFT_VERSION` remains Forge's package-level
compatibility guard. Root `cad-ci.yml` keeps the explicit SolidCraft version
expected by Forge CI.

Version-pinned SolidCraft engineering references live under
`docs/reference/solidcraft/<version>/`. Before targeting a newer SolidCraft
release, add a new sibling version directory with exact upstream provenance and
capture the version-specific reference material before compatibility changes.
Never overwrite an already qualified version directory. The procedure is in
`docs/development.md`.

## Test ownership

- `scpf/tests/` — reusable Forge API/compiler tests.
- the fixed release examples — Forge `tool_verify`.
- `examples/<model>/verification/` — native SolidCraft model checks.

`docs/background/design/test-architecture.md` contains the detailed test split.

## Public API documentation

The primary API contract is `docs/api.md`.

Exact public names, signatures, defaults and enum values come from the Python
implementation and its docstrings. Cross-object semantic rules live in
`docs/api.md`; documentation-generation/development rules live in
`docs/development.md`.

`docs/agent/forge-api.json` is generated from the same public API sources.
Do not maintain a second handwritten API manual in `scpf/README.md`, AGENTS,
or the agent directory.

Historical documentation-architecture discussion is preserved under
`docs/background/documentation-architecture.md`.

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

`docs/background/changes/` and several older audit/remediation documents under
`docs/background/design/` describe earlier development states. Their old terminology is
historical rather than an active CI contract.

## Documentation structure

The primary human documents are:

- `docs/api.md`;
- `docs/design.md`;
- `docs/development.md`;
- `docs/plan.md`;
- `docs/requirements.md`;
- `docs/release.md`.

Current task guidance belongs under `docs/manual/`. Current version-pinned
external engineering references belong under `docs/reference/`. Historical or
narrow design, change, audit, migration and superseded research records belong
under `docs/background/`. Generated machine-oriented API data remains under
`docs/agent/`.

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

