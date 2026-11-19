# Verification

Forge uses separate tool-release verification and per-model verification.

## Forge release verification

The Forge tool item is `scpf/ci.yml` and runs:

```text
tool_build -> tool_test -> tool_verify
```

`tool_build` creates the installable SCPF wheel.

`tool_test` runs the reusable unit-test suite under `scpf/tests/` against the
built package.

`tool_verify` is the final Forge release-verification step. It uses the fixed
representative example set:

- `simple-box`
- `anchored-holes`
- `components`
- `corner-anchor`
- `custom-anchor`

The first four run their example-owned command-contract tests and compile with
the exact built wheel. `custom-anchor` is an intentional negative example: it
proves that the currently unsupported rotated-parent attachment is rejected
with the expected Forge model error.

The generated release-verification evidence is stored below the Forge tool
item's `tool_verify/` output.

## Model verification

`model_verify` is independent of Forge release verification.

A migrated model is a CAD-CI model item that depends on `forge-tool`. The
model-verification wrapper:

1. obtains the exact wheel produced by `tool_build`;
2. compiles that model to its own `solidcraft.json`;
3. runs the model-owned verifier in the immutable SolidCraft runtime.

The shared wrapper is `scripts/model_verify.py`. Model-specific expectations
remain under `examples/<model>/verification/`.

The shared immutable verification runtime is defined by:

```text
docker/solidcraft_runtime/Dockerfile
docker/solidcraft_runtime/runtime.json
```

The runtime includes SolidCraft plus the versioned reference/visual/diagram
toolchain used by #378. Runtime lifecycle remains separate from normal Forge CI:

- `.github/workflows/solidcraft-runtime.yml` checks/builds/publishes immutable
  images and supports `workflow_dispatch`;
- root `cad-ci.yml` declares the exact `FORGE_RUNTIME_IMAGE` and
  `SOLIDCRAFT_VERSION` expected by normal CI;
- `.github/workflows/scpf.yml` delegates directly to released
  `tool.cad.ci/reusable-ci.yml`;
- model/reference commands consume the injected image reference and fail if the
  immutable image cannot be pulled;
- normal Forge CI never builds a missing runtime image implicitly.

A Forge unit check compares the explicit CI expectation with the current runtime
build definition so a runtime configuration change cannot silently leave
`cad-ci.yml` behind.

All 32 historical model cases now have native `model_verify` coverage. Issue #378 tracks the remaining reference, visual, diagram and summary verification layers.

## Historical integration tests

Example-owned tests under `examples/<example>/tests/` are still useful
command-contract tests. Their historical `integration` label does not make
every historical model a Forge `tool_verify` release example.

## Layer meaning

| Layer | Proves |
| --- | --- |
| `tool_build` | the distributable Forge package can be built |
| `tool_test` | reusable Forge Python/API/compiler rules pass against that package |
| `tool_verify` | the built Forge package passes the fixed release example set |
| `model_verify` | one migrated model produces the expected native SolidCraft result |

The removed repository-wide qualification runner and numbered qualification
levels are historical terminology, not current step names.
