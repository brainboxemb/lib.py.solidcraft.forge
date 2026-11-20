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
They pull and run that exact immutable image. Verification behavior stays in released `lib.py.cad.verfication`, including
CAD-tool-specific adapters. Forge keeps Forge compilation and model-specific
expected data.


## Runtime package composition

The immutable runtime is deliberately a reusable execution environment, not
only a CAD-engine binary image.

It may contain exact released application libraries and stable dependencies
that are required by nearly every verification run. In particular:

```text
SolidCraft runtime image
  SolidCraft
  reference CAD tooling
  released lib.py.cad.verfication
  stable shared Python dependencies
```

`lib.py.cad.verfication` is still developed and released independently. The
runtime consumes that release as a build input through
`docker/solidcraft_runtime/runtime.json`.

This gives two useful properties at the same time:

1. ownership remains clean: reusable CAD verification behavior is implemented
   and tested in the verification-library repository;
2. execution remains efficient: model checks reuse one prebuilt image instead
   of installing the verification package and its common dependencies on every
   invocation.

The runtime image hash therefore changes when the pinned verification-library
release changes. That is intentional and makes the exact verification code part
of the reproducible execution environment.

The exact built Forge wheel remains separate because Forge itself is the code
being qualified. The runtime must not substitute a preinstalled Forge package
for that built wheel.


## Manual runtime lifecycle

Runtime definition changes and runtime publication are deliberately separate.

```text
runtime definition change
  -> normal source review/CI
  -> no image build

explicit workflow_dispatch
  -> resolve exact runtime image ID
  -> if image exists: verify/reuse
  -> if absent: build and publish
  -> require published image

separate source change
  -> update cad-ci.yml to selected immutable image
```

There is no automatic `push` or `pull_request` trigger on the runtime
publication workflow.


## Runtime build reuse

Runtime reuse is explicit and image-based:

```text
runtime inputs -> exact image reference -> GHCR exists?
                                      yes -> reuse image
                                       no -> manual build/publish
```

The runtime workflow does not import or export Buildx layers through GitHub
Actions cache and does not use `actions/cache`. The immutable GHCR image is
the reusable object.


## Runtime image publication format

The SolidCraft runtime is a single Linux/amd64 execution image. The manual
runtime workflow publishes that tag as a directly pullable image manifest.

Buildx provenance is disabled for this image:

```yaml
provenance: false
```

The runtime helper validates both the top-level manifest and a real Docker pull.
A tag whose child manifest is missing is treated as unavailable and can be
re-published by the manual runtime workflow.

This changes publication representation only. Runtime package composition is
owned separately by #438.


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
native SolidCraft model and how to locate a model-local definition. It must not know
the SolidCraft measurement schema, implement numeric/body/timeline comparisons,
or duplicate mutation/evaluation verification logic.

A migrated model definition exports one `VERIFICATION` value built from
released types such as:

```python
SolidCraftVerification(
    verification_id="simple-box",
    baseline=SolidCraftModelExpectation(...),
    saved_designs=(
        SolidCraftSavedDesign(
            id="length_50",
            command_path=...,
            expectation=SolidCraftModelExpectation(...),
        ),
    ),
)
```

Generated SolidCraft timeline names are not model-owned unless explicitly
checked. `SolidCraftTimelineExpectation` therefore uses the released 0.10.0
partial-field contract.

During staged migration, older models keep their existing
`scripts/model_verify.py` + procedural `verify_model.py` path. Each model is
switched explicitly to `scripts/model_verify_declarative.py` in its own
migration change. New generic verification behavior must not be implemented in
Forge.
