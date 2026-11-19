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


## Verification ownership boundary

Forge verification data owns only model-specific behavior:

- expected parameter/history/feature values;
- mutation command data and expected mutation results;
- model-specific reference source files/data;
- model-specific cameras, views and baselines;
- expected geometry and tolerances.

Shared checker knowledge must come from a released
`lib.py.cad.verfication` API. This includes CAD-tool-specific adapters that
know how to invoke and interpret SolidCraft, OpenSCAD, FreeCAD or another CAD
tool when that behavior is reusable.

Forge must not parse SolidCraft measurement/result schemas or maintain shared
SolidCraft eval/mutate/inspect verification helpers.

In particular Forge must not reimplement:

- scalar tolerance comparison;
- numeric vector tolerance comparison;
- XYZ bounds comparison;
- order-independent body-envelope comparison;
- generic mesh verification;
- image normalization/regression/diff mechanics;
- generic visual expected-shape projection/drawing;
- generic visual-view evidence composition;
- generic semantic result composition.

When Forge needs generic behavior that the library does not yet expose, stop
consumer implementation and add that behavior to the verification library with
its own requirements, design, tests and release first.
