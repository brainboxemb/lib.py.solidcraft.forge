# Forge NEW plan

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
- a hard migration boundary that rejects `0.15.0` and older as Forge NEW
  releases; no Forge NEW tag or GitHub Release has been published.

The historical repository is being finalized as
`brainboxemb/lib.py.solidcraft.forge.OLD`, an archived A/B/provenance reference.

## Now

The API/runtime migration baseline is accepted on `dev`:

- #74 associative native Sketch-line folds are accepted;
- SolidCraft runtime v0.3.6 / SolidCraft 0.49.0 is immutable and accepted;
- #83 restored canonical SolidCraft reference capture/runtime verification;
- #85 permanent v0.3.6/0.49 adoption is accepted with full 47-owner evidence.

Current work is #89 repository canonicalization.

1. Execute the GitHub repository settings swap:
   - historical `brainboxemb/lib.py.solidcraft.forge` ->
     `brainboxemb/lib.py.solidcraft.forge.OLD`;
   - archive the historical `.OLD` repository;
   - current `brainboxemb/lib.py.solidcraft.forge.NEW` ->
     canonical `brainboxemb/lib.py.solidcraft.forge`.
2. After the settings swap, finish and merge the #89 identity audit:
   - canonical README/handoff/source identity;
   - canonical Hugo Pages base URL/source repository;
   - historical parity source renamed to `.OLD`;
   - verify branch refs, merge policy, release path and Pages from the canonical
     repository.
3. Reconcile this plan after #89, then prepare the first migrated Forge release:
   - promote the accepted `dev` baseline to stable `main` with the required
     merge commit;
   - bump package version above historical 0.15.0;
   - add the required dated changelog section;
   - require exact full stable `build/main` evidence;
   - publish only through `/release vX.Y.Z <exact-main-sha>`.
4. Update the active CAD project to the new canonical Forge release:
   - replace the four Mounting Rail fixed fold lines with the accepted #74
     `Sketch.line(...)` path;
   - verify native post-generation length edits remain associative;
   - requalify Mounting Rail M8 and Simple MFT against the immutable
     Forge/runtime pair.
5. Return to Pages as a dedicated quality phase only after the canonical release
   and downstream adoption:
   - restore the global development warning (#57);
   - rewrite the landing page around Forge/SCPF itself (#58);
   - visually/content-audit landing, Guide, API Reference, Cheatsheet, Examples
     and Verification;
   - create one issue per remaining independent Pages defect before changing it.

## Later

1. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
2. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
