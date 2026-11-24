# Forge NEW plan

This file contains unfinished work only.

## Accepted baseline

The Forge migration is complete on `dev`.

The accepted baseline now has:
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
  `gh-pages`;
- the historical nine-chapter Guide and Cheatsheet;
- 44 case-sensitive public SCPF API Reference routes, statically validated
  against `cadlib/src/scpf` without importing or executing the package;
- Verification `coverage`, `joint-anatomy` and `results` projections from
  source declarations and durable build evidence;
- the reusable Hextra/CAD presentation foundation from
  `template.cad.library`;
- a fixed 63-route OLD-vs-NEW route/content gate;
- accepted desktop/mobile rendered-layout evidence, including the corrected
  rich joint-anatomy diagram presentation;
- policy-owned merge execution through PR comment `/merge`, with
  `.github/workflows/merge-policy.yml` choosing and executing the merge
  method.

The historical `brainboxemb/lib.py.solidcraft.forge` repository is now an
archival/A-B reference rather than an unfinished migration gate.

## Now

- #47: align Forge CI/build/Pages workflow roles with the accepted
  `template.cad.library` / CAD NEW split.

## Later

1. qualify NEW release/version mechanics;
2. retire duplicated historical orchestration only after all real consumers
   and public documentation have equivalent coverage.
