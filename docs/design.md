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

The GitHub workflow does not understand Forge runtime metadata or selected item
kinds.

## Runtime lifecycle

Runtime construction is separate from normal CI.

```text
runtime.json + Dockerfile + Forge runtime build inputs
  -> solidcraft_runtime.py
  -> SolidCraft runtime workflow
  -> immutable GHCR image
```

The resulting immutable image is not rediscovered during normal CI. Its exact
reference is deliberately copied into root `cad-ci.yml` as
`FORGE_RUNTIME_IMAGE`.

That separation makes a runtime update explicit:

1. change the runtime build definition;
2. build and publish the new immutable image;
3. update the CI expectation in `cad-ci.yml`;
4. Forge checks that the explicit expectation matches the build definition.

## Version roles

`scpf/scpf/version.py::TESTED_SOLIDCRAFT_VERSION` remains package-level
compatibility behavior.

`cad-ci.yml::variables.SOLIDCRAFT_VERSION` is the version normal CI expects
for the selected immutable runtime.

Forge tests keep those contracts aligned. Normal workflow YAML does not derive
one from the other.

## Verification

Model/reference commands consume `FORGE_RUNTIME_IMAGE` from their environment.
They pull and run that exact immutable image. Generic comparison/reporting code
stays in released `lib.py.cad.verfication`; Forge keeps only its own policy,
adapters and expected data.


## Verification adapter boundary

Forge model verification has three layers:

```text
SolidCraft/model adapter
  -> normalized consumer values
  -> released cad_verification functions
  -> model-specific pass/fail policy and evidence
```

The SolidCraft/model adapter may know the SolidCraft measurement JSON schema and
extract values such as parameters, bodies, bounds, timeline rows and feature
state. Those extraction rules are engine-specific and stay in Forge.

Once values are ordinary scalars, vectors, bounds, body envelopes, images or
semantic statuses, comparison/composition uses released
`lib.py.cad.verfication` functions. Forge must not keep parallel generic
comparison math such as `close()`, `vector_close()`, `bbox_close()` or
`bounds_match()`.

Reference execution remains a thin Forge adapter because choosing/running
PythonSCAD, pyBOSL2, CadQuery and build123d is consumer policy. Its exported STL
geometry is validated by the library.

Visual rendering remains a Forge adapter because SolidCraft snapshot commands,
view selection and camera conversion are engine/model policy. Generic visual
verification after rendering belongs to the library.
