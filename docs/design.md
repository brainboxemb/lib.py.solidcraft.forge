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
CAD-tool-specific adapters. Forge keeps only Forge compilation and
model-specific expected data.


## Verification adapter boundary

Forge model verification has this ownership flow:

```text
Forge model-specific expectation data
  -> released cad_verification CAD-tool adapter
     -> CAD-tool result/schema interpretation
     -> released generic comparison/assertion functions
     -> verification evidence
```

For SolidCraft, the adapter lives in
`cad_verification.adapters.solidcraft`. Forge must not maintain a parallel
SolidCraft/model adapter.

Forge keeps model-specific values such as expected bodies, parameters, history,
mutations, views, cameras and tolerances. The verification library knows how
those declarations are checked against SolidCraft.

Forge compilation/replay that produces the initial SolidCraft design remains a
Forge producer responsibility. Shared SolidCraft evaluation, mutation,
inspection, result parsing and checking belong to the released verification
adapter.

The same structure may later apply to OpenSCAD, FreeCAD, CadQuery or other CAD
tools: tool-specific checking belongs to a sibling verification adapter, while
model-specific reference data stays in Forge.

Forge must not keep parallel comparison math or result-schema helpers such as
`close()`, `vector_close()`, `bbox_close()`, `bounds_match()` or a
shared `solidcraft_measurements.py`.
