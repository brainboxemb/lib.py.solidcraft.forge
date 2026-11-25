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
  `template.cad.library@e9fb95cd22cb574d615d0bf9a8115c30bbac7ddf`:
  product-changing stable sources retain full schema-2 evidence, while
  metadata-only release commits may reuse that evidence only across a validated
  linear release-only history;
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

Canonical Forge **v0.16.0** is published and available to consumers:

- stable source: `021dc78a32d99d31f16a76efc9d036855114df0c`;
- annotated tag: `v0.16.0`;
- release workflow `45587716727`: PASS;
- durable stable evidence: `full: true`, `library: true`, 47/47 active owners;
- qualified runtime: v0.3.6 / SolidCraft 0.49.0.

Current Forge priority is #98: consume the accepted generic stable-main release
flow from template #47 before returning to Pages.

1. Complete #98 on `dev`:
   - `release/vX.Y.Z` starts from stable `main`;
   - only `CHANGELOG.md` and `cadlib/pyproject.toml:project.version` may
     change;
   - release PR/main-push qualification selects library + release only and zero
     model owners;
   - `release_only: true` candidates preserve the previous full
     `build/main` product evidence;
   - exact release-source history is validated before publication;
   - release branches clean up only after merge to `main`;
   - stable-only release metadata returns through `main -> dev`, never rebase.
2. Run one real unmerged Forge `release/* -> main` smoke proving semantic
   preflight, release+library selection, zero model owners and
   `release_only:true`.
3. After #98 is accepted, return to Pages:
   - #57 restore the global development warning;
   - #58 rewrite the landing page around Forge/SCPF itself;
   - visually/content-audit landing, Guide, API Reference, Cheatsheet, Examples
     and Verification;
   - create one issue per remaining independent Pages defect before changing it.

CAD project work continues independently and is no longer a prerequisite for
these Forge infrastructure/Pages tasks.

#73 remains retained engine/runtime regression evidence rather than a Forge
replay-workaround target. Other migrated Forge backlog (#59-#72) stays Later
unless active consumer work exposes a concrete blocker.

## Later

1. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
2. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
