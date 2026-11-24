# Forge NEW plan

This file contains unfinished work only.

## Accepted baseline

The twenty-owner migration gate is accepted and promoted on `main@87ba6e3b535f4b93f65d519e7694688473bc8b96`.

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
10. `sheet-fold`;
11. `round-top-sketch`;
12. `native-revolve`;
13. `circle-negative-extrude`;
14. `bracket`;
15. `hole-family`;
16. `top-sketch-after-chamfer`;
17. `circular-feature-pattern`;
18. `rounded-rectangle-sketch`;
19. `attached-through-all`;
20. `cone-boolean`;

For the baseline:
- SCPF is primary per owner;
- historical reference implementations are local implementations only where they existed;
- all 20 native SCPF stages pass;
- all 80 applicable geometry stages pass;
- historical saved-design and inspection behavior is retained;
- the historical public `Sketch.revolve()` contract is restored in `cadlib/scpf`;
- OLD vs NEW evidence is recorded in `docs/acceptance/five-owner-gate.md`, `docs/acceptance/ten-owner-gate.md` and `docs/acceptance/twenty-owner-gate.md`;
- `build/main/models` and `build/dev/models` contain all twenty owners;
- stable Pages projects the currently migrated example-purpose owners `simple-box`, `anchored-holes` and `corner-anchor`, and all twenty owners appear under Verification.

The historical `brainboxemb/lib.py.solidcraft.forge` repository remains the A/B authority until remaining model and documentation parity is demonstrated.

## Now — #31 Pages and documentation parity

Historical stable Pages is the acceptance authority for the public documentation surface.

Recorded historical route inventory:
- 4 Examples;
- 48 Verification routes, including special `coverage`, `joint-anatomy` and `results`;
- 9 Guide chapters;
- 44 API Reference routes;
- Cheatsheet;
- API design contract.

Completed on `dev`:
- source-owned `docs/reference/solidcraft` restored for SolidCraft 0.42.0, 0.45.0 and 0.48.1;
- reference documentation is projected into Hugo/Hextra from `docs/reference/**`.

Active work:
1. restore the authored 9-chapter Guide and Cheatsheet through source-owned `docs/` plus Hugo projection;
2. restore the generated public SCPF API Reference without reviving the retired OLD site generator;
3. migrate `components` as one physical owner with `purpose: [example, verification]` to restore the fourth historical Example;
4. restore/replace the three special Verification routes using current durable evidence;
5. restore model-local visual verification (#38), beginning with simple-box front/right/iso and then the remaining historically visual owners;
6. record explicit OLD-vs-NEW Pages route/content acceptance before closing #31.

## Next — remaining model graph

Continue controlled owner slices using the historical functional groups:
1. parameters and dependencies;
2. components and occurrences;
3. anchors and local frames;
4. associative relationships;
5. remaining sheet-metal owners.

Keep one physical owner per model, SCPF primary, and preserve only historically real reference implementations.

## Later

1. qualify NEW release/version mechanics;
2. retire duplicated historical orchestration only after all real consumers and public documentation have equivalent coverage.
