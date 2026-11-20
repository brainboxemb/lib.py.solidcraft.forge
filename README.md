# SCPF — SolidCraft Python Forge

`lib.py.solidcraft.forge` is the Python authoring library for the SolidCraft CAD engine.
The Python package and command are both named `scpf`.

Forge models are ordinary Python classes with a `build()` method. Forge lowers their
modelling intent to native SolidCraft command JSON; SolidCraft creates the editable
CAD geometry and feature history.

## Current versions

- SCPF package: **0.11.0**
- Tested SolidCraft runtime: **0.42.0**
- CAD verification library: **0.1.0** (`187f486f4d7bca85fd708f1c61d175c44ff34128`)

The package version is defined in `scpf/pyproject.toml`.
The tested SolidCraft version is defined in
`scpf/scpf/version.py::TESTED_SOLIDCRAFT_VERSION`.

## Repository responsibilities

This repository contains:

- the reusable Forge Python API under `scpf/scpf/`;
- command lowering and runners;
- Forge unit tests and release-verification examples;
- historical model-verification fixtures under `examples/`;
- the immutable verification runtime used by model, reference, visual and diagram verification.

Product CAD models live in the separate
[2026-011-02.cad.solidcraft](https://github.com/brainboxemb/2026-011-02.cad.solidcraft)
repository.

## Install and test

From the repository root:

```powershell
python -m pip install -e ./scpf
python -m unittest discover -s scpf/tests -v
```

Check one model without starting SolidCraft:

```powershell
python -m scpf check examples/simple-box/scpf/model.py
```

Compile it to native SolidCraft command JSON:

```powershell
python -m scpf examples/simple-box/scpf/model.py --out output/simple-box.json
```

The detailed API-oriented developer documentation is in `scpf/README.md`.

## Current CI architecture

GitHub uses two separate workflows:

- `.github/workflows/scpf.yml` (**Forge**) for Forge/model CI;
- `.github/workflows/solidcraft-runtime.yml` (**SolidCraft runtime**) for the immutable Docker runtime.

Planning and execution are delegated to the pinned reusable workflows from
`brainboxemb/tool.cad.ci`. Repository-specific work is declared in
`cad-ci.yml`, `scpf/ci.yml` and migrated model `ci.yml` files.

The Forge release chain is:

```text
tool_build -> tool_test -> tool_verify
```

- `tool_build` builds the Forge package;
- `tool_test` runs Forge unit tests;
- `tool_verify` release-verifies that built package with the fixed
  representative example set.

Per-model SolidCraft checking is separate:

- `model_verify` compiles one migrated model with the exact built Forge
  package and verifies the resulting native model in SolidCraft.

All 32 historical model cases now have native `model_verify` coverage. Issue #378 tracks the remaining reference, visual, diagram and summary verification layers.

## Verification runtime

Forge verification uses one immutable runtime definition:

```text
docker/
  solidcraft_runtime/
    Dockerfile
    runtime.json
```

`scripts/solidcraft_runtime.py` resolves and checks the immutable image reference. The runtime pins the released `lib.py.cad.verfication` 0.1.0 commit and verifies the installed package version while building the image. It also contains the versioned reference/visual/diagram toolchain: CADCraft 0.20.1, PythonSCAD 1.1.2, the pinned pyBOSL2 commit, CadQuery 2.8.0 and build123d 0.12.0.
The normal Forge workflow only requires that image to exist; it never builds or
publishes it. The separate SolidCraft runtime workflow owns image build/publish
and can be started explicitly with `workflow_dispatch`.

`scripts/model_verify.py` compiles the selected model and runs its
`verification/verify_model.py` inside that image.

Model-specific dimensions, mutations and expectations stay under
`examples/<model>/verification/`.

The former repository-wide qualification package and qualification Docker image
are no longer part of the active architecture.

## Example metadata

Presentation metadata may be stored in `model.yml` with these generic fields:

```text
section
title
tagline
description
parameters
stages
```

Technical assertions and mutation logic are executable verification code rather
than presentation metadata.

## Release status

Release notes are maintained in `CHANGELOG.md`.

The former automatic release-validation/publication path was removed during the
CAD-CI cut-over because it no longer matched the active workflow. The current
Forge workflow does not automatically create a Git tag or GitHub Release.

Build, Pages and release publication migration is tracked in issue #366.
`docs/release.md` describes the current state.

## Build and Pages status

The existing `build` and `gh-pages` branches contain generated output from
the earlier publication architecture. The current CAD-CI workflow has not yet
completed its publication cut-over.

Issue #366 tracks migration to the generic `tool.cad.ci` publisher.
Until then, current source plus current CAD-CI results are authoritative for
development status.

## Documentation map

- `docs/plan.md` — current unfinished repository work only.
- `docs/05-cad-api-design.md` — cross-object Forge API rules.
- `docs/06-verification.md` — current verification layers.
- `docs/09-documentation-architecture.md` — documentation sources of truth.
- `docs/release.md` — current release state.
- `docs/11-generated-output.md` — generated-output migration boundary.
- `docs/design/test-architecture.md` — current test ownership.
- `docs/agent/forge-api.json` — generated machine-readable Forge API index.
- `docs/agent/reference-libraries.md` — notes for external comparison libraries.

`docs/changes/` and older design/audit records are historical records and may
use terminology from earlier architectures.

## Companion repositories

- [lib.py.solidcraft.cmd](https://github.com/brainboxemb/lib.py.solidcraft.cmd)
- [2026-011-02.cad.solidcraft](https://github.com/brainboxemb/2026-011-02.cad.solidcraft)
- [tool.cad.ci](https://github.com/brainboxemb/tool.cad.ci)

## License

Forge exposes SolidCraft's native command interface. SolidCraft itself is an
independent open-source project; consult the respective repositories for their
license information.
