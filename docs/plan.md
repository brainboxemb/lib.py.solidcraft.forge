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

Forge release infrastructure and the identified public Pages content fixes are
accepted or in final qualification:

- #57 global development warning;
- #58 Forge/SCPF product landing;
- #106 canonical API Reference landing wording;
- #107 source-owned Joint anatomy SolidCraft version;
- #109 canonical Guide landing wording;
- #68 CadCraft removal while retaining SVG/DXF engineering assets;
- #112 complete `Use when` / `Limits` guidance across public callables.

The active Pages task is #113: make the Examples and Verification landing copy
user-facing instead of exposing internal model-owner projection mechanics.

After #113, finish the audit rather than starting another broad rewrite:

1. review desktop/mobile evidence for Guide chapter detail routes;
2. review API Reference detail routes;
3. review Cheatsheet;
4. review Examples model pages;
5. review Verification model pages and Coverage/Results/Joint anatomy;
6. create one issue per independent remaining defect before changing it;
7. if no new defects remain, reconcile the Pages phase as complete.

CAD project work continues independently and is not a prerequisite for this
Pages phase.

#73 remains retained engine/runtime regression evidence rather than a Forge
replay-workaround target. Other migrated Forge backlog stays Later unless active
consumer work exposes a concrete blocker.

## Later

1. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
2. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
