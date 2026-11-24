# Forge NEW plan

This file contains unfinished work only.

## Accepted baseline

The physical Forge model migration is complete on `dev`.

The accepted migration baseline now has:
- 46 physical model owners;
- SCPF as primary per owner;
- historically real reference implementations local to the same physical owner;
- native and applicable geometry verification;
- 36 model-local approved SolidCraft visual-verification policies;
- current per-view native evidence generated from `model.sc`;
- saved-design and inspection behavior retained where historically real;
- `components` as one physical owner with
  `purpose: [example, verification]`;
- exactly four public Examples;
- all 46 physical owners projected into Verification;
- durable generated CAD artifacts on `build/<scope>/models/**`, not copied to
  `gh-pages`.

The historical `brainboxemb/lib.py.solidcraft.forge` repository remains the
A/B authority until documentation and public-route parity is accepted.

## Now — #31 final integration

PR #34 is the single remaining migration lane.

Implemented and qualified on the PR branch:
- historical nine-chapter Guide and Cheatsheet projections;
- 44 case-sensitive public SCPF API Reference routes, statically validated
  against `cadlib/src/scpf` without importing or executing the package;
- the API design-contract compatibility route;
- Verification `coverage`, `joint-anatomy` and `results` projections from
  source declarations and durable build evidence;
- the accepted reusable Hextra/CAD presentation foundation from
  `template.cad.library`;
- a fixed 63-route OLD-vs-NEW route/content gate;
- desktop/mobile rendered-layout evidence with zero missing local assets.

Remaining work:
1. require final CI and Pages checks on the current PR head;
2. inspect the Forge-specific documentation screenshots produced by the final
   Pages run;
3. squash PR #34 into `dev`;
4. verify the post-merge durable build/Pages chain and close #31;
5. promote the accepted `dev` baseline to `main` with the repository's
   normal merge-commit policy.

The reusable visual foundation remains template-owned. Forge-specific Guide,
API Reference, Cheatsheet and Verification explanatory content remain owned
here.

## Later

1. qualify NEW release/version mechanics;
2. retire duplicated historical orchestration only after all real consumers
   and public documentation have equivalent coverage.
