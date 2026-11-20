# Forge design

This document summarizes repository-level responsibility boundaries. Detailed
test and verification design remains under `docs/design/`.

## Main execution path

Normal Forge CI is intentionally simple:

```text
GitHub workflow
  -> tool.cad.ci reusable-ci
     -> read cad-ci.yml
     -> inject repository variables
     -> execute selected SCons targets
        -> Forge-owned commands
```

The GitHub workflow does not understand runtime packaging or selected item
kinds.

## Runtime lifecycle

Runtime construction and release are external to Forge:

```text
docker.cad.solidcraft
  versions.env + Dockerfile
  -> build/test
  -> immutable release vX.Y.Z
  -> ghcr.io/brainboxemb/cad-solidcraft:vX.Y.Z

lib.py.solidcraft.forge
  cad-ci.yml
  -> selects one immutable released runtime
  -> tool.cad.ci injects FORGE_RUNTIME_IMAGE
  -> model/reference commands pull and run it
```

Forge contains no runtime build or publication path.

A runtime update is explicit:

1. release a new `docker.cad.solidcraft` version;
2. verify that immutable image in the runtime repository;
3. update Forge's `FORGE_RUNTIME_IMAGE`;
4. prove Forge CI against the new release.

## Version roles

`docker.cad.solidcraft` owns runtime SemVer and runtime dependency pins.

`scpf/scpf/version.py::TESTED_SOLIDCRAFT_VERSION` remains Forge's package-level
SolidCraft compatibility behavior.

`cad-ci.yml::variables.SOLIDCRAFT_VERSION` is the SolidCraft version Forge CI
expects from the selected released runtime.

Forge does not own a runtime content hash, timestamp version or Docker release
number.

## Runtime package composition

Runtime package composition belongs to `docker.cad.solidcraft`.

It may preinstall frequently reused released libraries and stable dependencies,
including the CAD verification library, for execution efficiency.

Forge does not duplicate those pins. It only supplies:

```text
exact built Forge wheel
model source
model-specific verification data
```

to the selected external runtime.

## Verification

Model/reference commands consume `FORGE_RUNTIME_IMAGE` from their environment.
They pull and run that exact immutable release.

Verification behavior stays in released `lib.py.cad.verfication`, including
CAD-tool-specific adapters. Forge keeps Forge compilation and model-specific
expected data.

## Declarative model verification flow

The final model-verification path has one Forge producer step followed by the
released verification-library runner:

```text
examples/<model>/scpf/model.py
  -> scripts/model_verify_declarative.py
     -> exact built Forge wheel
     -> compile Forge model to command document
     -> replay command document to initial native model.sc
     -> load examples/<model>/verification/verify.py
     -> run_solidcraft_verification(model.sc, output, VERIFICATION)
        -> baseline evaluation/checks
        -> saved-design mutation/evaluation/checks
        -> inspections
        -> artifacts + verification.json
```

`scripts/model_verify_declarative.py` may know how Forge produces the initial
native SolidCraft model and how to locate a model-local verification file. It
must not know the SolidCraft measurement schema, implement numeric/body/timeline
comparisons, or duplicate mutation/evaluation verification logic.

Generated SolidCraft timeline names are not model-owned unless explicitly
checked. `SolidCraftTimelineExpectation` therefore uses the released partial
field contract.

During staged migration, older models keep their existing
`scripts/model_verify.py` + procedural `verify_model.py` path. Each model is
switched explicitly to `scripts/model_verify_declarative.py` in its own
migration change. New generic verification behavior must not be implemented in
Forge.


## Staged item participation

Forge uses released CAD-CI `process` only as declarative repository
configuration.

The flow is:

```text
Forge item ci.yml
  -> process: true|false
  -> released tool.cad.ci
  -> released lib.py.cad.ci planner/executor
```

Forge contains no helper that interprets `process`, no duplicate changed-path
selection and no second execution policy.

During the five-model proof, the `scpf` item remains active. Exactly five model
verification items participate; the other model verification items remain
present in the repository but are excluded by the released CAD-CI planner.
Shared/reference items remain active where required by existing dependencies.
