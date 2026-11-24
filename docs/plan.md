# Forge NEW plan

This file contains unfinished work only.

## Accepted baseline

The twenty-owner migration gate is accepted and promoted on `main`.

For the accepted baseline:
- SCPF is primary per owner;
- historically real reference implementations remain local to the same physical owner;
- native and applicable geometry verification pass;
- saved-design and inspection behavior is retained;
- the public `Sketch.revolve()` contract is restored in `cadlib/scpf`;
- OLD-vs-NEW evidence is recorded in `docs/acceptance/five-owner-gate.md`,
  `docs/acceptance/ten-owner-gate.md` and
  `docs/acceptance/twenty-owner-gate.md`;
- durable `build/main/models` and `build/dev/models` contain the accepted owners.

Model-local SolidCraft visual verification has also been restored on `dev`.
The 16 accepted visual-policy owners produce current native per-view evidence
from `model.sc`; Pages must present that evidence rather than substitute STL
previews.

The historical `brainboxemb/lib.py.solidcraft.forge` repository remains the
A/B authority until model and documentation parity is complete.

## Now — #40 complete remaining model graph

The remaining 26 historical physical owners are migrated on the #40 work
branch, bringing the candidate repository to 46 physical owners including
NEW's `native-revolve` qualification owner.

Candidate structure:
- 36 multi-engine owners: SCPF primary plus the four historically real
  reference implementations, with native, geometry and visual verification;
- 10 intentionally SCPF-only owners, including the specialist exploded-view
  and native sheet-metal contracts;
- 36 model-local approved visual policies;
- `components` is one physical owner with
  `purpose: [example, verification]`, restoring the fourth historical
  Example without duplicating ownership.

Qualification completed for the 26-owner candidate: all owner aggregates,
native stages, applicable geometry stages and visual stages pass. Evidence is
recorded in `docs/acceptance/remaining-owner-gate.md`.

Remaining #40 work:
1. squash the accepted work branch to `dev`;
2. verify durable `build/dev/models` contains all 46 owners;
3. verify purpose-driven Pages projects four Examples and all 46 Verification
   owners without copying generated CAD artifacts.

## Next — #31 Pages and documentation parity

Historical stable Pages remains the acceptance authority.

Required public parity includes:
- four Examples;
- Verification for the migrated owner graph plus the historical special
  verification routes;
- the authored Guide;
- generated SCPF API Reference;
- Cheatsheet and API design contract;
- retained versioned SolidCraft reference documentation.

The reusable visual foundation is being corrected first in
`template.cad.library`. Forge should adopt that accepted foundation rather
than invent a parallel site design. Forge-specific Guide/API/Cheatsheet content
remains owned here.

## Later

1. qualify NEW release/version mechanics;
2. retire duplicated historical orchestration only after all real consumers
   and public documentation have equivalent coverage.
