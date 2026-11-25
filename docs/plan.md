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

The Forge Pages quality phase is accepted on development and ready for stable
promotion.

Accepted development source:
- `53c368f1668077b326dec4cb47b18c7ad6570f55`;
- permanent dev CI `45621976335`: PASS.

Accepted Pages set:
- #57 global development warning;
- #58 Forge/SCPF product landing;
- #106 canonical API Reference landing wording;
- #107 source-owned Joint anatomy SolidCraft version;
- #109 canonical Guide landing wording;
- #68 CadCraft source/link removal with SVG/DXF retained;
- #112 complete public callable Use when / Limits guidance;
- #113 user-facing Examples and Verification landing copy.

Final audit at that baseline found no remaining independent Pages defect in the
reviewed categories:
- no stale NEW product identity;
- no hardcoded current 0.48.1 in the public Pages generators/landings;
- no CadCraft files/references;
- no owner-internal copy on the two catalogue landings;
- all public callables have non-empty Use when + Limits;
- rendered capture/verifier covers Guide, API Reference, Cheatsheet, Examples,
  Verification, Coverage, Results and Joint anatomy.

Current task is #117: promote that accepted Pages set to stable `main`.

1. Merge `main -> dev` through `/merge` as history-only synchronization;
   current comparison has zero file changes.
2. Require permanent green dev evidence after the sync.
3. Open `dev -> main` and require full product qualification plus Pages
   desktop/mobile evidence.
4. Merge through `/merge` so stable receives the normal promotion merge
   commit.
5. Require permanent full `build/main` evidence and successful Pages
   publication.
6. Verify the canonical public root now contains the accepted Pages set.

CAD project work continues independently and is not a prerequisite for this
stabilization.

#73 remains retained engine/runtime regression evidence rather than a Forge
replay-workaround target. Other migrated Forge backlog stays Later unless active
consumer work exposes a concrete blocker.

## Later

1. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
2. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
