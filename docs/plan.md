# Forge NEW plan

This file contains unfinished work only.

## Accepted baseline

The ten-owner migration gate is accepted and promoted on `main@378b5051cc2accc98e4774af3189d377be52ab1c`.

Accepted physical owners:
1. `simple-box`;
2. `primitive-csg`;
3. `anchored-holes`;
4. `assembly-decorator`;
5. `parametric-attach`;
6. `corner-anchor`;
7. `rectangular-pattern`;
8. `rotated-sketch-cutter`;
9. `slot-family`;
10. `sheet-fold`.

For the baseline:
- SCPF is primary per owner;
- historical reference implementations are local implementations only where they existed;
- owner-local command contracts pass;
- all 10 native SCPF stages pass;
- all 45 applicable geometry stages pass;
- historical saved-design and inspection behavior is retained;
- SCPF replay semantics remain consumer-owned through `scpf.headless.run_document()`;
- OLD vs NEW evidence is recorded in `docs/acceptance/five-owner-gate.md` and `docs/acceptance/ten-owner-gate.md`;
- `build/main/models` and `build/dev/models` contain all ten owners;
- Pages projects owners by purpose without creating duplicate owners: Examples contains `simple-box`, `anchored-holes` and `corner-anchor`; Verification contains all ten owners.

The historical `brainboxemb/lib.py.solidcraft.forge` repository remains the A/B authority until remaining-graph parity is demonstrated.

## Now — #29 core feature slice

The twenty-owner candidate is technically accepted on `553033bdd2ccf0e5612e8f12d2a95c51a51ec462` by CI run **45456265226** with qualification artifact **14950656646**. OLD vs NEW evidence is recorded in `docs/acceptance/twenty-owner-gate.md`.

The ten added owners are:
- basic geometry: `round-top-sketch`, `native-revolve`, `circle-negative-extrude`, `bracket`;
- parent/child features and faces: `hole-family`, `top-sketch-after-chamfer`, `circular-feature-pattern`, `rounded-rectangle-sketch`, `attached-through-all`, `cone-boolean`.

All ten remain `purpose: verification`. `native-revolve`, `attached-through-all` and `cone-boolean` are intentionally SCPF-only; the other seven retain all four historical reference implementations.

The candidate restored the historical public `Sketch.revolve()` contract in `cadlib/scpf` because the migration exposed that NEW had lost it. No model-local workaround was introduced.

Remaining work for #29 is integration acceptance only: squash PR #30 to `dev`, verify durable build and Pages output for twenty owners, then complete a full `dev -> main` promotion with a merge commit and stable post-merge checks.

## After #29

Continue the remaining graph by the historical functional groups: parameters/dependencies, components/occurrences, anchors/local frames, associative relationships, then sheet metal.

## Later

1. migrate remaining API/guide/reference documentation;
2. qualify NEW release/version mechanics;
3. retire duplicated historical orchestration only after all real consumers have equivalent coverage.
