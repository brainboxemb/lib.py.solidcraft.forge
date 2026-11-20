# Forge requirements

This document records stable repository requirements. Detailed API behavior is
documented in the subject-specific Forge documentation.

## CI ownership

- `tool.cad.ci` is the only generic CAD-CI planner/executor.
- Forge workflows remain thin orchestration.
- Forge owns Forge compilation, model definitions and model-specific
  expectation data.
- Shared verification behavior comes from released
  `lib.py.cad.verfication`, including CAD-tool-specific adapters such as the
  SolidCraft adapter.

## Runtime build and CI expectation

The runtime build definition and the runtime expected by normal CI are separate
contracts.

- `docker/solidcraft_runtime/runtime.json` describes what the runtime image
  build contains.
- `docker/solidcraft_runtime/Dockerfile` describes how that image is built.
- root `cad-ci.yml` declares the exact immutable runtime image expected by
  normal Forge CI.
- root `cad-ci.yml` also declares the SolidCraft version expected by CI.
- normal Forge CI must not derive either value from the runtime build files.
- Forge must check that the explicit CI expectation remains compatible with the
  current runtime build definition.

A runtime configuration change may therefore build a new immutable image first;
normal CI changes to that new image only when `cad-ci.yml` is explicitly
updated.

## Runtime consumption

Forge CAD-CI commands read the injected repository environment:

- `FORGE_RUNTIME_IMAGE` is the exact immutable image reference;
- `SOLIDCRAFT_VERSION` is the SolidCraft version expected by CI.

Consumer commands do not parse `cad-ci.yml` themselves.

A missing immutable image is an error. Normal CI does not build a missing image
implicitly; runtime publication remains the responsibility of the separate
SolidCraft runtime workflow.

## Forge package compatibility

The package keeps its own tested SolidCraft compatibility guard. CI must verify
that its declared `SOLIDCRAFT_VERSION` agrees with the package/runtime build
contract rather than silently maintaining unrelated version literals.


## Shared runtime efficiency

Library ownership and runtime packaging are separate concerns.

`lib.py.cad.verfication` remains an independently designed, tested and
released Python library. The immutable SolidCraft runtime may and should
preinstall an exact released version when that library is used by essentially
every model verification.

Therefore:

- `runtime.json` pins the verification-library release version and exact
  commit that is installed in the image;
- changing that pin intentionally changes the immutable runtime image ID;
- model verification must use the library already present in that image rather
  than reinstalling the same package for every model;
- preinstallation does not transfer verification-code ownership to Forge;
- Forge must not copy or modify verification-library implementation inside this
  repository.

The same principle applies to other stable libraries used by nearly every
runtime invocation: preinstalling them is an efficiency choice, while their
code ownership remains with their own package/repository.


## Manual runtime publication

SolidCraft runtime images are built and published only by an explicit manual
workflow invocation.

- the runtime workflow uses `workflow_dispatch`;
- it must not run on `push`, `pull_request` or path changes;
- changing `runtime.json`, the Dockerfile or runtime helper scripts only
  changes the source definition; it does not publish an image;
- normal Forge CI consumes the explicit immutable image configured in
  `cad-ci.yml` and must not build a missing image automatically.

The operator sequence is:

1. change and review the runtime definition;
2. manually run the SolidCraft runtime workflow;
3. verify the published immutable image;
4. explicitly update the CI runtime reference.


## GitHub Actions cache

Forge runtime publication must not use GitHub Actions cache storage.

- Do not use `actions/cache`.
- Do not use Buildx `cache-from: type=gha` or `cache-to: type=gha`.
- Runtime reuse is based on the exact immutable GHCR image reference.
- A local directory named `.cache` is not GitHub cache storage unless it is
  persisted through a cache action/service.


## Runtime image publication

The manually invoked runtime workflow must publish the exact immutable
single-platform runtime tag in a form that normal Docker clients can consume.

After publication:

- the exact tag must pass the strict registry/presence check;
- a real `docker pull` of that exact tag must succeed;
- publication must not leave an OCI index that references a missing child
  manifest.

Build provenance/attestation is disabled for this runtime image when it would
change the registry representation in a way that breaks normal pullability.


## Declarative model verification

A migrated Forge model owns only model-specific verification data.

For SolidCraft-backed model verification:

- the model may define a `SolidCraftVerification` value in
  `verification/definition.py`;
- body counts, expected bounds, parameter values, timeline expectations,
  mutation command paths and other model-specific expected values remain with
  the model;
- the definition contains data only and must not contain checker callbacks;
- the model must not parse SolidCraft result JSON, invoke SolidCraft
  verification commands, construct verification checks or write
  `verification.json`.

The shared Forge launcher owns only the producer boundary required before
verification:

1. build/locate the exact Forge wheel;
2. compile/replay the Forge model into the initial native SolidCraft `.sc`
   model;
3. load the model-local verification definition;
4. call released `run_solidcraft_verification()`.

Shared SolidCraft evaluation, mutation, inspection, schema interpretation,
comparison and report construction are responsibilities of released
`lib.py.cad.verfication`.

Model migrations are proven one model at a time before catalog expansion.
