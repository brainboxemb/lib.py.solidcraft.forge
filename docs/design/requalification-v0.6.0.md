# SCPF v0.6.0 renewed qualification — 2026-11-17

Status: **renewed qualification complete**

This record closes the qualification-integrity question around the already
published SCPF v0.6.0 release. It does not create a second v0.6.0 release.

## Release and evidence identity

| Item | Value |
| --- | --- |
| Release | `v0.6.0` |
| Tagged release commit | `d0cadaa9af5952979d689b4b19184ff89a0da18b` |
| Corrected qualification commit | `7ae925fd4bb0541f78a97a4710144043de117f9a` |
| Corrected qualification run | `44042448381` |
| Qualification artifact | `scpf-qualification-7ae925fd4bb0541f78a97a4710144043de117f9a` |
| Artifact id | `14309587952` |
| Forge package version reported by the run | `0.6.0` |
| SolidCraft version | `0.42.0` |
| Qualified at | `2026-11-17T07:58:39Z` |

The corrected run completed successfully, including the final
`Enforce qualification status` step.

## Does corrected main still test v0.6.0 behaviour?

Yes for Forge model/compiler/runtime behaviour.

The source tree after v0.6.0 is not byte-identical to the release tag because
PR #235 improved generated API documentation. A commit-by-commit comparison
from the tagged release to the corrected qualification commit found only one
post-release commit that touched files under `scpf/scpf/`: #235.

It changed these package files:

- `compiler.py`
- `core.py`
- `explicit_sketch.py`
- `model_objects.py`
- `runner.py`

Those changes are documentation strings and examples only. For each of the five
files, replacing every complete triple-quoted string with one fixed token makes
the tagged v0.6.0 source and corrected qualification source identical outside
those strings. All other `scpf/scpf/` files are unchanged from the tag.

Therefore the corrected gate exercises the same executable Forge modelling,
lowering and replay behaviour as the published v0.6.0 release. The renewed
qualification claim does not rely on a later runtime fix.

## Corrected qualification result

The structured qualification artifact contains 24 supported cases.

| Evidence | Result |
| --- | --- |
| Overall case status | 24 PASS |
| Q1 public API/compiler evidence | 24 PASS |
| Q2 command-contract evidence | 24 PASS |
| Q3 native SolidCraft build | 24 PASS |
| Q4 native semantic/geometry validation | 24 PASS |
| Q5 saved-design mutation | 14 required cases PASS; 10 cases explicitly not required |
| Q6 expected-shape + render regression | 24 PASS |
| Q6 expected-shape layer | 24 PASS |
| Q6 render-regression layer | 24 PASS |

No geometry, API, command-lowering or saved-design recompute discrepancy was
found that requires a corrective Forge runtime release.

## What changed relative to the original v0.6.0 qualification claim?

The audit found that several PASS claims had insufficient evidence. The
remediation strengthened the evidence; it did not change the qualified Forge
runtime behaviour.

- #221/#222: every supported case now executes the required PythonSCAD,
  pyBOSL2, CadQuery and build123d references unless there is a documented
  technical exception. Internal geometry is checked with volume and 3D feature
  probes rather than bounding boxes alone.
- #223: Q1 and Q2 PASS are now case-specific. Every case names concrete proving
  tests and has its own run evidence; global suite success no longer gives all
  cases an automatic PASS.
- #224: Q6 now requires both an independently declared expected shape and the
  approved native render regression. Hole and Slot cases use meaningful
  case-specific views and explicit 3D internal-feature declarations.
- #228: Q5 applicability is explicit. `simple-box` and
  `rectangular-pattern` gained saved-design mutation evidence because their
  qualification claims depend on editable native parameters.
- #229: API coverage claims resolve to real qualification cases and are checked
  against current native PASS evidence.
- #230: Q4 geometry, external references and Q6 expectations share one
  machine-readable geometry contract per case.

The renewed result therefore means more than the original v0.6.0 PASS: the
same Forge behaviour has now passed the corrected evidence model.

## Release decision

A corrective Forge runtime release is **not required** for the qualification
audit findings above.

Do not create or overwrite the existing `v0.6.0` tag. Downstream projects may
pin the exact tagged release commit
`d0cadaa9af5952979d689b4b19184ff89a0da18b` after their own project CI passes
with that dependency.

## Downstream acceptance

Downstream acceptance is complete.

CAD PR `brainboxemb/2026-011-02.cad.solidcraft#99` updated the project from
SCPF 0.5.0 to the exact v0.6.0 release-tag commit
`d0cadaa9af5952979d689b4b19184ff89a0da18b`.

The CAD source needed the intentional v0.6.0 authoring migration:

- `Hole.pattern(...)` became `Hole.repeat_linear(...)`;
- negative Sketch extrusion became a negative signed distance;
- symmetric Sketch extrusion became `sym=True`;
- obsolete `Direction` imports were removed.

No Forge workaround or post-tag Forge runtime code was used.

On exact CAD PR head `873bed09ba3b567316c34e7eef7b480ce4665d1c`:

| CAD gate | Run | Result |
| --- | --- | --- |
| Models, regressions and site smoke | `44044529488` | PASS |
| Native SolidCraft CAD verification | `44044529348` | PASS |

The native gate built/evaluated all ten project models against SolidCraft
0.42.0 and completed the independent SCPF/SCPC comparison and source-matched
result-site build.

CAD PR #99 merged as
`f8ae58dc017e5fcb1fcde3936065cabb36dfa48e`.

The same merged commit then passed both workflows on CAD `main`:

| Post-merge CAD main gate | Run | Result |
| --- | --- | --- |
| Models, regressions and site smoke | `44044740923` | PASS |
| Native SolidCraft CAD verification | `44044740913` | PASS |

This completes issue #227 and the downstream requirement of qualification audit
#220.
