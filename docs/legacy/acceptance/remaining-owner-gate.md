# Remaining owner migration gate

## Scope

This gate completes the physical model-owner migration from the historical
`brainboxemb/lib.py.solidcraft.forge` repository.

The accepted candidate adds the 26 historical owners that were still absent
after the twenty-owner gate:

- `anchor-topology-mutation`
- `as-built-attach`
- `assembly-owned-anchor`
- `attach-angle`
- `components`
- `eight-corner-brackets`
- `eight-flightcase-corners`
- `exploded-views`
- `four-corner-l`
- `group-hierarchy`
- `parameter-scope`
- `parametric-anchor`
- `parametric-move`
- `parametric-offset`
- `parametric-placement-pair`
- `parent-derived-child-size`
- `repeated-parent-attachments`
- `rotated-copy-placement`
- `selective-profile-extrude`
- `sheet-contour-flange`
- `sheet-edge-flange`
- `sheet-hem`
- `sheet-path-flange`
- `sheet-perforate`
- `sketch-pattern-mirror`
- `xz-anchor`

Together with the accepted twenty-owner baseline and NEW's
`native-revolve` qualification owner, the candidate repository contains 46
physical owners.

## Ownership parity

The historical repository was inspected owner by owner.

Twenty of the added owners retain all four historically real reference
implementations beside SCPF:

- CadQuery
- build123d
- PythonSCAD
- pyBOSL2

Those owners use SCPF as primary and retain:
- the model-local command contract;
- native SolidCraft verification;
- the historical geometry contract;
- the approved model-local visual policy and baselines;
- saved-design mutation or inspection inputs where historically present.

Six specialist owners remain intentionally SCPF-only:

- `exploded-views`
- `sheet-contour-flange`
- `sheet-edge-flange`
- `sheet-hem`
- `sheet-path-flange`
- `sheet-perforate`

No reference implementation, mesh-geometry stage or visual policy was
invented for those owners. Their native mutation/inspection contracts are
retained instead.

`components` remains one physical owner and declares
`purpose: [example, verification]`. It restores the fourth historical
Example without creating a duplicate model owner.

## Qualification

Runtime candidate branch head:

`aae11968d3731eb6c99bef9af883947daf8abd8a`

Pull request: #41

CI run: **45479575241**

Qualification artifact: **14960673955**

GitHub tested the pull request through merge-test source SHA:

`0fb030d0ca99812678600c14c4e1f3660076ac12`

The qualification build plan records:
- 46 active physical owners;
- exactly the 26 new owners selected by the work-branch gate;
- a non-full selective qualification, so the accepted twenty-owner baseline
  was not rebuilt unnecessarily.

Artifact inspection records for the 26-owner slice:
- 26/26 owner aggregate results: **pass**;
- 106 implementation results: **pass**;
- 26 native SolidCraft stages: **pass**;
- 100 applicable mesh-geometry stages: **pass**;
- 20 visual verification stages: **pass**;
- 62 visual per-view checks: **pass**;
- all visual artifacts referenced by the reports exist in the qualification
  output;
- the SolidCraft batch reports **pass**;
- the reference batch reports **pass**.

The six specialist owners each contain one SCPF implementation and exactly one
native verification stage in the qualification artifact.

Repository tests also qualify the complete 46-owner discovery contract, the
historically real implementation sets, the two-runtime scheduling contract
and all 36 migrated visual policies.

## Acceptance boundary

This gate accepts the remaining physical model graph and its build/
verification evidence.

Post-merge acceptance still requires:
1. durable `build/dev/models` publication for all 46 owners;
2. purpose-driven Pages projection with four Examples and all physical owners
   represented under Verification;
3. no generated CAD artifacts copied into `gh-pages`.

Public Guide, API Reference, Cheatsheet and special historical Verification
routes remain owned by #31 and are not part of this gate.
