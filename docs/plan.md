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

## Now — #31 Pages and documentation parity

PR #34 is the single remaining migration lane.

Already present or accepted:
- retained versioned SolidCraft reference documentation for 0.42.0, 0.45.0
  and 0.48.1;
- source-owned historical nine-chapter Guide plus Hugo projection;
- source-owned Cheatsheet plus Hugo projection;
- the historical SCPF API design contract;
- the historical 44-route SCPF API Reference manifest retained as authored
  migration data.

Current work order:
1. restore the 44 public SCPF API Reference routes without importing or
   executing `scpf` during Pages build; validate the retained manifest
   statically against the current `cadlib/src/scpf` source surface;
2. restore the special Verification routes `coverage`, `joint-anatomy` and
   `results` from current source declarations and durable build evidence;
3. adopt the accepted reusable presentation foundation from
   `template.cad.library`; do not invent a parallel Forge visual foundation;
4. record a final OLD-vs-NEW route/content gate and inspect representative
   rendered pages before declaring migration parity;
5. merge #34 to `dev`, verify durable Pages output, close #31, then promote
   the accepted `dev` baseline to `main` according to repository policy.

The reusable visual foundation remains template-owned. Forge-specific Guide,
API Reference, Cheatsheet and Verification explanatory content remain owned
here.

## Later

1. qualify NEW release/version mechanics;
2. retire duplicated historical orchestration only after all real consumers
   and public documentation have equivalent coverage.
