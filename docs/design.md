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


## Runtime versus application packages

The runtime image and the application packages have different lifecycles.

```text
immutable CAD runtime image
  SolidCraft
  CADCraft
  PythonSCAD / pyBOSL2 / CadQuery / build123d
  stable shared Python dependencies

verification invocation
  exact built Forge wheel
  exact released cad-verification package
  model-specific definition/data
```

The verification package is not a Docker build input. Its version/commit is
therefore absent from `docker/solidcraft_runtime/runtime.json` and from the
runtime image hash.

Stable dependencies may deliberately remain in the image for efficiency. For
the current verification package this includes Pillow, trimesh and scipy. They
are runtime dependency inputs in their own right rather than being installed
transitively by installing the verification package.

The verification invocation supplies the exact verification package separately
and makes it importable together with the exact Forge wheel. The package is
tested against the dependency versions present in the runtime.

PyYAML and matplotlib remain in the image only if a current CAD/reference
runtime path demonstrably needs them; otherwise #438 removes them.
