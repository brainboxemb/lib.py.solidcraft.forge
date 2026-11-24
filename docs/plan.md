# Forge NEW plan

This file contains unfinished work only.

## Accepted baseline

The five-owner migration gate is accepted on `dev@606f07588c8a41ee4f2ae18aef55ff25d1ceb2fc`.

Accepted physical owners:
1. `simple-box`;
2. `primitive-csg`;
3. `anchored-holes`;
4. `assembly-decorator`;
5. `parametric-attach`.

For the gate:
- SCPF is primary per owner;
- historical reference implementations are local implementations only where they existed;
- owner-local command contracts pass;
- all five native stages pass;
- all 25 applicable geometry stages pass;
- historical saved-design mutations are retained;
- SCPF replay semantics are preserved through `scpf.headless.run_document()`;
- OLD vs NEW evidence is recorded in `docs/acceptance/five-owner-gate.md`;
- durable `build/dev/models` output is published;
- Pages exposes only owners whose `purpose` contains `example`.

The historical Forge repository remains the A/B authority.

## Now — #21 ten-owner gate

Add five representative physical owners:

6. `corner-anchor` — topology-backed anchor + parent-resize saved design; public example + verification;
7. `rectangular-pattern` — two-direction native feature pattern + saved-design mutation;
8. `rotated-sketch-cutter` — rotated local Sketch frames and Boolean cutters; migrate only the historical SCPF implementation;
9. `slot-family` — five native Slot constructions + saved-design width/length/position mutation;
10. `sheet-fold` — native sheet-metal fold + flat-pattern inspection.

For each owner:
- preserve historical `model.yml.purpose` exactly;
- migrate only reference implementations that actually existed;
- preserve owner-local source/compiler contract tests;
- migrate native/saved-design/inspection expectations exactly;
- reuse the generic two-runtime/staged-verification architecture;
- compare against retained OLD `build/dev-cad/examples/<id>/` evidence.

Do not start the remaining graph until the ten-owner gate is accepted, durably published, correctly projected by Pages and promoted through a full `dev -> main` run.

## After the ten-owner gate

1. classify and migrate the remaining graph;
2. migrate API/guides/reference documentation;
3. qualify NEW release/version mechanics;
4. retire duplicated historical orchestration only after parity.
