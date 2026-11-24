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

Migrate the ten remaining owners from the first two historical Verification groups:

- basic geometry: `round-top-sketch`, `native-revolve`, `circle-negative-extrude`, `bracket`;
- parent/child features and faces: `hole-family`, `top-sketch-after-chamfer`, `circular-feature-pattern`, `rounded-rectangle-sketch`, `attached-through-all`, `cone-boolean`.

All ten remain `purpose: verification`. `native-revolve`, `attached-through-all` and `cone-boolean` are intentionally SCPF-only; the other seven retain all four historical reference implementations.

Acceptance requires owner-local command contracts, native verification, every historically applicable reference geometry stage, durable build output and Verification Pages projection against OLD evidence.

Do not create sibling owners for CAD engines and do not synthesize reference implementations that did not historically exist.

## After #29

Continue the remaining graph by the historical functional groups: parameters/dependencies, components/occurrences, anchors/local frames, associative relationships, then sheet metal.

## Later

1. migrate remaining API/guide/reference documentation;
2. qualify NEW release/version mechanics;
3. retire duplicated historical orchestration only after all real consumers have equivalent coverage.
