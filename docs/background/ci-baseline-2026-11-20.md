# Forge CI baseline — 2026-11-20

This report records the verified CI baseline reached before durable build and
Pages migration continues.

It is background evidence. Current work order remains in `docs/plan.md`.

## Accepted CI stack

Current Forge CI is proven on:

- `tool.cad.ci` v0.12.2;
- exact tool commit `8bab91eaf8554533e5f63620421ed9554f66eb91`;
- released `lib.py.cad.ci` 0.7.1.

The detailed timing baseline below was captured on v0.12.1. v0.12.2 changes only
reusable-workflow artifact transport for successful runs that materialize no
`build/` output; it does not change CAD-CI selection or model execution.

Structured CAD-CI evidence is retained in the `forge-cad-ci-build` workflow
artifact when materialized build output exists.

## Five-model proof

Exactly five model items participate in the staged proof:

- `simple-box`
- `anchor-topology-mutation`
- `attach-angle`
- `four-corner-l`
- `xz-anchor`

The other 27 model items remain `process: false`.

Each active model exposes two ordered steps:

```text
contract_test -> model_verify
```

The final reliability run built 13 targets with 13 successes and no errors:

- `forge-package`
- `forge-tests`
- `forge-release`
- five `contract_test` steps
- five `model_verify` steps

`reference-verification` was not selected in this normal five-model run.

## Reliable timing baseline

Source: structured CAD-CI evidence from run `44720568295`.

| Step | Duration |
| --- | ---: |
| forge-package / tool_build | 1.101 s |
| forge-release / tool_verify | 0.567 s |
| forge-tests / tool_test | 0.578 s |
| anchor-topology-mutation / contract_test | 0.132 s |
| anchor-topology-mutation / model_verify | 44.059 s |
| attach-angle / contract_test | 0.141 s |
| attach-angle / model_verify | 1.429 s |
| four-corner-l / contract_test | 0.133 s |
| four-corner-l / model_verify | 1.880 s |
| simple-box / contract_test | 0.148 s |
| simple-box / model_verify | 1.414 s |
| xz-anchor / contract_test | 0.142 s |
| xz-anchor / model_verify | 1.453 s |

Total CAD-CI run duration was approximately **54.0 s**.

The four warm model-verification actions are therefore approximately
**1.4–1.9 s per model**. The first model owns the cold runtime cost.

## Historical comparison

Historical stored qualification evidence showed the same five small models at
approximately:

| Model | Historical complete case |
| --- | ---: |
| simple-box | 1.55 s |
| anchor-topology-mutation | 1.52 s |
| attach-angle | 1.46 s |
| four-corner-l | 2.57 s |
| xz-anchor | 1.64 s |

Together these five historical model cases were approximately **8.74 s**.
Including the historical global Q1/Q2 suites gave approximately **18.18 s**.

This supports the conclusion that the model work itself is not inherently slow.

An earlier current-architecture run of roughly **156 s** must not be used as the
five-model baseline: that run also selected repository-wide
`reference-verification all`. Historical all-model reference verification was
already approximately **127 s** by itself.

## Verification coverage audit

The reliability audit established:

- **Q1**: reusable Forge API/compiler coverage remains in `forge-tests`;
- **Q2**: model-owned command-contract tests are restored as explicit
  `contract_test` steps for all five active models;
- **Q4/Q5**: current declarative expectations materially preserve the historical
  native/model verification semantics for the five proof models;
- **Q6 visual regression**: not yet restored; remains under #430/#378.

The current five-model proof is therefore suitable as a reliable CI baseline,
but it is not yet the final complete verification architecture.

## Parked runtime-performance finding

The cold first model is explained primarily by image acquisition, not by warm
model execution.

Evidence:

- first `model_verify`: approximately **44.1 s**;
- four warm `model_verify` actions: approximately **1.4–1.9 s**;
- clean pull of the same
  `ghcr.io/brainboxemb/cad-solidcraft:v0.1.0` image in the runtime repository:
  approximately **45.5 s**.

The released v0.1.0 runtime is monolithic. Build-record analysis showed roughly:

- total compressed image data: **1.24 GB**;
- one combined Python/reference-tooling layer: approximately **879 MB**.

That image includes independent reference tooling that normal SolidCraft model
verification does not need.

This is recorded and parked in:

- Forge #484 — cold runtime overhead;
- `docker.cad.solidcraft` #4 — runtime/reference-toolchain split.

No runtime optimization is part of the current durable-build work.

## Other parked maintenance

Forge #481 records stale development-branch cleanup.

The branch-hygiene rule is already merged: development branches should exist
only while work is active. Physical deletion of the old refs remains pending
because the connected GitHub tooling used during this work does not expose ref
deletion.

This does not block CI development.

## Continuation

The reliable CI baseline is now sufficient to continue the main generated-output
path:

```text
main
  -> verified item output
  -> build
  -> gh-pages
```

The active continuation is Forge #366: make accepted item output durable on
`build`, then cut Pages publication over to the generic CAD-CI publisher.
