# Forge plan

This file contains unfinished work only.

## Accepted baseline

The Forge migration is complete and promoted to stable `main`.

The accepted baseline now has:
- 47 physical model owners;
- SCPF as primary per owner;
- historically real reference implementations local to the same physical owner;
- native and applicable geometry verification;
- 36 model-local approved SolidCraft visual-verification policies;
- current per-view native evidence generated from `model.sc`;
- saved-design and inspection behavior retained where historically real;
- `components` as one physical owner with
  `purpose: [example, verification]`;
- exactly four public Examples;
- all 47 physical owners projected into Verification;
- durable generated CAD artifacts on `build/<scope>/models/**`, not copied to
  `gh-pages`;
- the historical nine-chapter Guide and Cheatsheet;
- 45 case-sensitive public SCPF API Reference routes, statically validated
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
  method;
- the accepted library/CAD NEW workflow split: pull requests run central `ci`
  only, permanent `dev`/`main` runs use one `build` job for qualification and
  durable publication, and Pages is dispatched as an independent workflow;
- generic stable-main release qualification from
  `template.cad.library@e9fb95cd22cb574d615d0bf9a8115c30bbac7ddf`,
  consumed and live-qualified in Forge #98: product-changing stable sources
  retain full schema-2 evidence, while metadata-only release commits reuse that
  evidence only across a validated linear release-only history;
- Forge-owned release metadata validation for package version, dated changelog
  section, active blockers and the tested SolidCraft version;
- explicit owner-issued `/release` publication delegated to released
  `tool.py.lib.ci v0.2.1`, with Pages excluded from release evidence;
- a hard migration boundary that rejects `0.15.0` and older as Forge
  releases;
- canonical post-migration release `v0.16.0`, published from stable main
  `021dc78a32d99d31f16a76efc9d036855114df0c` after exact full build/main
  qualification.

The historical repository is being finalized as
`brainboxemb/lib.py.solidcraft.forge.OLD`, an archived A/B/provenance reference.

## Now

Forge release infrastructure and the global development warning are accepted:

- stable-main release-flow implementation is on Forge `main`
  `dc9bd4b75e9aedf8f5ffa215be7382775baa89c9`;
- unmerged release-only smoke PR #103 / run `45603049650`: PASS;
- #57 global development warning is accepted on `dev`
  `02511eaa57d4129a3f90bad327ce5373651decc8`;
- #57 permanent Pages publication `45604568348`: PASS.

The active Pages task is #58: make the landing page explain Forge/SCPF as a
product rather than describing the website.

1. #58 — rewrite the landing page:
   - Forge/SCPF is the Python API/compiler for SolidCraft;
   - show the compilation relationship:
     SCPF model -> Forge compiler -> SolidCraft commands/native geometry;
   - make explicit that SolidCraft remains the CAD engine;
   - project SCPF package version and tested SolidCraft version statically from
     source without importing `scpf`;
   - give direct entry points to Guide, API Reference, Cheatsheet, Examples and
     Verification;
   - retain a link to real SolidCraft CAD projects;
   - review desktop/mobile screenshot evidence.
2. After #58, run a full visual/content audit:
   - landing;
   - Guide;
   - API Reference;
   - Cheatsheet;
   - Examples;
   - Verification and special routes;
   - create one issue per independent defect before changing it.

CAD project work continues independently and is not a prerequisite for this
Pages phase.

#73 remains retained engine/runtime regression evidence rather than a Forge
replay-workaround target. Other migrated Forge backlog (#59-#72) stays Later
unless active consumer work exposes a concrete blocker.

## Later

1. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
2. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
