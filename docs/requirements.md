# Forge requirements

This document records stable repository requirements. Detailed API behavior is
documented in the subject-specific Forge documentation.

## CI ownership

- `tool.cad.ci` is the only generic CAD-CI planner/executor.
- Forge workflows remain thin orchestration.
- Forge owns Forge/SolidCraft-specific commands, expectations and fixtures.
- Generic verification mechanics come from released `lib.py.cad.verfication`.

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


## Visual verification

Forge visual verification separates domain policy from generic image mechanics.

Forge owns:
- which views a model requires;
- conversion from measured SolidCraft model bounds to a deterministic
  SolidCraft snapshot camera;
- the exact approved model-local baseline images;
- model-local expected boxes/features;
- the decision that a visual view is required.

Released `lib.py.cad.verfication` owns:
- image normalization;
- image comparison metrics;
- deterministic diff images;
- orthographic point projection;
- generic expected boxes/holes/slots;
- goal and overlay drawing;
- structured visual evidence values.

Visual evidence must use the same physical camera projection for the actual
SolidCraft snapshot and the independent expected-shape overlay.

The historical render contract remains:
- native snapshot size 720 x 540 pixels;
- normalized regression size 96 x 72 pixels;
- changed pixel threshold 12;
- maximum mean absolute difference 6.0;
- maximum changed-pixel fraction 0.08.

Approved baselines are versioned with the model that owns them. A current render
must never silently become its own approved baseline during CI.
