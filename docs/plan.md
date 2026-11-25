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
  releases; no Forge NEW tag or GitHub Release has been published;
- immutable CAD runtime `docker.cad.solidcraft v0.3.6` with SolidCraft 0.49.0,
  externally qualified first on Forge and the real Mounting Rail M8 / Simple MFT
  consumer;
- canonical SolidCraft 0.49.0 reference evidence captured from exact
  `cad-solidcraft:v0.3.6`: 886 commands, 20 additions vs 0.48.1 and no
  removed command IDs.

The historical `brainboxemb/lib.py.solidcraft.forge` repository is now an
archival/A-B reference rather than an unfinished migration gate.

## Now

The post-migration API/runtime chain is immutable and qualified:

- #74 associative Sketch-line fold support is accepted on `dev`;
- runtime v0.3.6 / SolidCraft 0.49.0 is published from exact qualified source
  `fa323fba8146d36e2598d08cb88b3a74e8c71761`;
- Forge candidate qualification #79 / run `45579896509` passed;
- real CAD consumer A/B #64 / run `45580463512` passed with unchanged
  Mounting Rail M8 and Simple MFT geometry;
- #83 restored canonical reference capture and the 0.49.0 snapshot is generated
  from the immutable runtime;
- Forge permanently consumes `cad-solidcraft:v0.3.6`,
  `cad-reference:v0.3.6` and tests SolidCraft 0.49.0.

1. Create the dedicated repository-canonicalization change:
   - rename the historical `brainboxemb/lib.py.solidcraft.forge` to an
     explicit `.OLD` archival name and archive it;
   - rename this repository from `.NEW` to canonical
     `brainboxemb/lib.py.solidcraft.forge`;
   - update active consumer/template references explicitly rather than relying
     on GitHub rename redirects;
   - verify branch policy, build evidence, Pages provenance, package metadata
     and release workflows after the rename.
2. Publish the first actual migrated Forge release from canonical stable
   `main`, qualified against immutable SolidCraft 0.49.0:
   - bump the package above the historical `0.15.0` baseline;
   - add the required dated changelog section;
   - require exact full stable `build/main` evidence;
   - publish only through `/release vX.Y.Z <exact-main-sha>`.
3. Update the active CAD project to the new canonical Forge release:
   - replace the four Mounting Rail fixed fold lines with the accepted #74
     `Sketch.line(...)` path;
   - verify native post-generation length edits remain associative;
   - requalify Mounting Rail M8 and Simple MFT against the immutable
     Forge/runtime pair.
4. Return to Pages as a dedicated quality phase only after the canonical release
   and downstream adoption:
   - restore the global development warning (#57);
   - rewrite the landing page around Forge/SCPF itself (#58);
   - visually/content-audit landing, Guide, API Reference, Cheatsheet, Examples
     and Verification;
   - create one issue per remaining independent Pages defect before changing it.

#73 remains retained engine/runtime regression evidence rather than a Forge
replay-workaround target. The accepted flat-first consumer construction order
stands; do not force `plane.fixed=true`, move physical holes, or change replay
semantics merely to mask the historical SolidCraft sheet-state behavior.

## Later

1. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
2. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
