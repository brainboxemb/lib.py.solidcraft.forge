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

The normal Forge workflow is `.github/workflows/scpf.yml`. Planning and
execution are delegated to released `tool.cad.ci`.

Repository-specific CI items are declared by `cad-ci.yml` from:

- `scpf/ci.yml` — `forge-package`;
- `ci/forge-tests/ci.yml` — `forge-tests`;
- `ci/forge-release/ci.yml` — `forge-release`;
- `examples/<model>/ci.yml` — model verification;
- `verification/references/ci.yml` — independent reference verification.

The Forge package graph is:

```text
forge-package
  dist/scpf-*.whl
      |
      +--> forge-tests
      +--> forge-release
      +--> selected model_verify items
```

`forge-package` builds the wheel once. Forge unit tests, release-verification
examples and model verification all consume that exact dependency artifact.

A model does not depend on the unit-test or release-verification item. Its only
Forge package prerequisite is `forge-package`.

The current Verification catalog contains 36 declarative active model cases: the final 32-case historical Qualification set plus four restored
historical cases whose replay-safety blocker was later removed. Every full
model case has four independent reference child items.

`model_authoring` remains outside native Verification by design: #213 accepted
it explicitly as a Q1/Q2-only authoring fixture. Its full lineage and the other
non-model fixtures are documented in `docs/background/example-history.md`.

## Verification runtime

Forge consumes immutable runtime images released by
`brainboxemb/docker.cad.solidcraft`. The current CAD-CI selection is declared
in root `cad-ci.yml`:

```text
FORGE_RUNTIME_IMAGE=ghcr.io/brainboxemb/cad-solidcraft:v0.3.2
REFERENCE_RUNTIME_IMAGE=ghcr.io/brainboxemb/cad-reference:v0.3.2
SOLIDCRAFT_VERSION=0.42.0
```

Forge does not build those images in normal CI. Model verification consumes the
released SolidCraft image; independent PythonSCAD/pyBOSL2/CadQuery/build123d
verification consumes the released reference image.

The verification library is not baked into the runtime image. Forge supplies
the exact released `lib.py.cad.verification` wheel as a CAD-CI dependency.

Current model verification is batched:

```text
examples/*/verification/verify.py
  -> scripts/model_verification_batch.py
  -> one SolidCraft runtime process for the selected/current model set
  -> scripts/model_verify_declarative.py per model inside that runtime
  -> released lib.py.cad.verification
```

All 36 current native model-verification cases use declarative `verify.py`
contracts. Model-specific dimensions, mutations, inspections and expectations
stay below the owning `examples/<model>/verification/` directory.

The former repository-wide Qualification package, procedural per-model
`verify_model.py` path and Forge-owned runtime image are not part of the
current architecture. Their migration history is recorded under
`docs/background/`.

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
than presentation metadata. Human engineering explanation belongs beside the
example in `examples/<slug>/README.md`; source migrations preserve that
documentation rather than reconstructing it from verification data.

## Release status

Release notes are maintained in `CHANGELOG.md`.

The former automatic release-validation/publication path was removed during the
CAD-CI cut-over because it no longer matched the active workflow. The current
Forge workflow does not automatically create a Git tag or GitHub Release.

Build, Pages and release publication migration is tracked in issue #366.
`docs/release.md` describes the current state.

## Build and Pages status

Durable accepted verification output lives on the generated `build` branch;
`build/main` is the authoritative complete baseline used by stable site
generation.

#497 completed the stable site migration to current Forge source plus durable
`build/main` evidence. Current replacement output is published on the
`gh-pages` branch through the generic CAD-CI publisher.

Main verification, durable build publication and stable Pages generation now
share one runner through externally accepted `tool.cad.ci 0.15.0`; #558 is
complete.

#366 now owns cut-over readiness. The replacement site restores the historical
standalone Results, Coverage and Joint anatomy knowledge as canonical
Verification pages and preserves old `/qualification/` URLs as generated
compatibility aliases. The public GitHub Pages source is still deliberately
pointed at `backup/gh-pages-before-f11-2026-11-20` until a separate explicit
live cut-over.

## Documentation map

Primary repository documents:

- `docs/api.md` — cross-object Forge API semantics.
- `docs/design.md` — repository-wide architecture and responsibility boundaries.
- `docs/development.md` — working on Forge itself.
- `docs/plan.md` — current unfinished work and issue ordering.
- `docs/requirements.md` — stable repository requirements.
- `docs/release.md` — package/release rules.

Secondary documentation:

- `docs/manual/` — current task-oriented guidance.
- `docs/reference/` — current version-pinned external engineering references.
- `docs/background/` — historical design, change, research and migration records.
- `docs/agent/` — generated machine-oriented API information.

## Companion repositories

- [lib.py.solidcraft.cmd](https://github.com/brainboxemb/lib.py.solidcraft.cmd)
- [2026-011-02.cad.solidcraft](https://github.com/brainboxemb/2026-011-02.cad.solidcraft)
- [tool.cad.ci](https://github.com/brainboxemb/tool.cad.ci)

## License

Forge exposes SolidCraft's native command interface. SolidCraft itself is an
independent open-source project; consult the respective repositories for their
license information.
