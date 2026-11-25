# Forge NEW plan

This file contains unfinished work only.

## Accepted baseline

The Forge migration is complete and promoted to stable `main`.

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

The historical `brainboxemb/lib.py.solidcraft.forge` repository is now an
archival/A-B reference rather than an unfinished migration gate.

## Now

1. Unblock the active CAD consumer through #74:
   - expose native associative Sketch-line/curve input for `Shape.fold()`;
   - retain the existing fixed-points fold form;
   - add a Forge-owned sheet-metal qualification fixture whose fold line follows
     an editable native length parameter;
   - re-run the downstream Mounting Rail M8 / Simple MFT consumer against the
     corrected Forge behavior.
2. Treat #73 as retained engine/runtime regression evidence, not as a Forge
   replay-workaround target. The flat-first consumer construction order is
   accepted; do not force `plane.fixed=true`, move physical holes, or change
   replay semantics merely to mask the historical SolidCraft sheet-state
   behavior.
3. After #74 and downstream qualification are green, canonicalize repository
   identity under #76:
   - rename the historical repository to an explicit `.OLD` archival name;
   - archive the historical repository;
   - rename this repository from `.NEW` to canonical
     `brainboxemb/lib.py.solidcraft.forge`;
   - update active consumer/template references explicitly instead of relying on
     GitHub rename redirects;
   - verify branch policy, build evidence, Pages provenance, package metadata
     and release workflows after the rename.
4. Publish the first actual migrated Forge release from canonical stable
   `main`:
   - bump the package above the historical `0.15.0` baseline;
   - add the required dated changelog section;
   - require exact full stable `build/main` evidence;
   - publish only through `/release vX.Y.Z <exact-main-sha>`;
   - update and requalify the active CAD consumer against that canonical
     release.
   A SolidCraft 0.49.0 runtime upgrade is a separate
   `docker.cad.solidcraft` qualification and is not implicitly part of this
   release.
5. Return to Pages as a dedicated quality phase only after the first canonical
   release:
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
