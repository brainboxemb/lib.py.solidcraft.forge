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
- generic library release qualification from `template.cad.library`: durable
  schema-2 build plans record explicit library qualification and
  `modules/release` validates exact full stable build evidence;
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

The immediate priority is the active CAD project, not more Forge infrastructure:

1. CAD #73 — replace the temporary Forge-main SHA pin with canonical
   `brainboxemb/lib.py.solidcraft.forge@v0.16.0` and requalify bootstrap/build.
2. CAD #67 — finish the Basic / Components / Subassemblies / Assemblies catalog
   taxonomy with generic Display/MFT grouping.
3. CAD #62 / draft PR #63 — resume the MFT mounting-rail corner bracket after
   #67 is accepted:
   - retain the already-qualified 6 mm load-bearing feet below both rail ends;
   - retain the low rounded outside-corner protector;
   - preserve outward/open C-channels;
   - keep provisional MFT screw/hardware dimensions unfrozen until measured or
     explicitly accepted.

After that CAD checkpoint, prioritize the release-process correction before
returning to Pages:

4. Template `template.cad.library#47` / PR #48 — separate release preparation
   from normal dev promotion:
   - `release/vX.Y.Z` starts from stable `main`;
   - only `release/*` may go directly to `main`;
   - full stable qualification remains mandatory;
   - after publication synchronize `main -> dev` through merge policy;
   - never rebase the shared permanent `dev` branch.
5. Forge #98 — consume the accepted generic release-flow policy and update
   Forge AGENTS/development/release documentation accordingly.
6. Return to Pages as a dedicated quality phase:
   - restore the global development warning (#57);
   - rewrite the landing page around Forge/SCPF itself (#58);
   - visually/content-audit landing, Guide, API Reference, Cheatsheet, Examples
     and Verification;
   - create one issue per remaining independent Pages defect before changing it.

#73 remains retained engine/runtime regression evidence rather than a Forge
replay-workaround target. Other migrated Forge backlog (#59-#72) stays Later
unless the active CAD work exposes a concrete blocker.

## Later

1. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
2. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
