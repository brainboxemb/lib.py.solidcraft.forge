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


## Visual verification flow

Visual verification is part of each model's normal verification output, not a
second CI runner.

```text
model_verify
  -> saved model.sc + measurements.json
  -> Forge SolidCraft visual adapter
     -> deterministic SolidCraft camera
     -> solidcraft-cli snapshot
     -> camera JSON + actual PNG
  -> released cad_verification visual APIs
     -> normalized actual/baseline
     -> regression metrics + diff PNG
     -> independent expected-shape goal PNG
     -> expected-shape overlay PNG
     -> structured view evidence
```

### Model-local data

A model may own:

```text
examples/<model>/verification/
  visual.json
  baselines/
    <view>.png
```

`visual.json` contains only Forge/model policy: required views, render and
normalization dimensions, comparison thresholds, expected boxes/features and
baseline provenance. It does not implement image comparison or projection.

### Camera conversion

Forge derives a deterministic SolidCraft orthographic camera from measured
model bounds:

- target = center of the complete measured body envelope;
- framing size = largest XYZ span, minimum 1 mm;
- SolidCraft distance = size × 1.65;
- front = yaw 0°, pitch 0°;
- right = yaw -90°, pitch 0°;
- top = yaw 0°, pitch +90°;
- iso = yaw -45°, pitch +32°.

SolidCraft's orthographic half-height is 0.4 × camera distance. The generic
`OrthographicCamera` therefore uses the same yaw/pitch in degrees and
`distance = 0.4 × SolidCraft distance`. This preserves the historical
front X-right/Z-up and top X-right/Y-up projection semantics while using the
verification library for actual projection/drawing.

### Baselines

Existing approved visual baselines are migrated as the model's baseline PNGs
with their provenance retained. CI compares against those files. It may report a
missing baseline, but it must not approve or replace one automatically.
