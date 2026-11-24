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

## Now

- #45: adopt the mandatory local `/merge` execution rule already accepted in the model-project, CAD NEW and library-template baselines.

## #31 final integration

PR #34 has been squash-merged into `dev`. It delivered:
- historical nine-chapter Guide and Cheatsheet projections;
- 44 case-sensitive public SCPF API Reference routes, statically validated
  against `cadlib/src/scpf` without importing or executing the package;
- the API design-contract compatibility route;
- Verification `coverage`, `joint-anatomy` and `results` projections from
  source declarations and durable build evidence;
- the shared Hextra/CAD presentation foundation;
- a fixed 63-route OLD-vs-NEW route/content gate;
- desktop/mobile rendered-layout evidence with zero missing local assets.

Post-merge screenshot review found one remaining Forge-specific rendering
regression: nested rich HTML in `joint-anatomy` can be projected as literal
Markdown/code blocks because source indentation is retained outside `<pre>`.
The correction remains part of #31 on branch
`issue/31-pages-parity-final`. An earlier `dev -> main` promotion occurred
before this visual defect was accepted as real, so the corrected `dev` baseline
must be promoted to `main` once more after this fix is qualified.

Remaining work:
1. qualify the `joint-anatomy` projection fix with CI, Pages and fresh
   desktop/mobile screenshots;
2. squash the fix PR into `dev`;
3. verify the normal post-merge durable build/Pages chain;
4. close #31;
5. promote the corrected `dev` baseline to `main` again with the repository's
   normal merge-commit policy.

The reusable visual foundation remains template-owned. Forge-specific Guide,
API Reference, Cheatsheet and Verification explanatory content remain owned
here.

## Later

1. qualify NEW release/version mechanics;
2. retire duplicated historical orchestration only after all real consumers
   and public documentation have equivalent coverage.
