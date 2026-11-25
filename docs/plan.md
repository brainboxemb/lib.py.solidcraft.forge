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

The historical `brainboxemb/lib.py.solidcraft.forge` repository is now an
archival/A-B reference rather than an unfinished migration gate.

## Now

1. Qualify Forge against SolidCraft 0.49.0 through #79 and
   `docker.cad.solidcraft#29`:
   - runtime v0.3.6 candidate is SolidCraft 0.49.0 with the existing two-role
     composition unchanged;
   - use runtime-main `:edge` only in a short-lived, unmerged Forge
     qualification PR;
   - require the full Forge graph, including the component/joined-Cylinder
     regression, #73 retained sheet evidence, and the accepted #74
     associative-fold saved-design mutation;
   - record the exact runtime-main commit and Forge qualification run before any
     immutable runtime release.
2. If the `:edge` qualification is green:
   - publish immutable runtime v0.3.6 from the exact qualified runtime-main
     commit;
   - replace temporary `:edge` pins with
     `cad-solidcraft:v0.3.6` / `cad-reference:v0.3.6`;
   - set the tested SolidCraft contract to 0.49.0 and rerun the same Forge
     qualification before merging permanent runtime adoption.
3. Requalify the active Mounting Rail M8 / Simple MFT CAD consumer against the
   immutable Forge/runtime pair. The rail must use the accepted #74
   `Sketch.line(...)` fold path so native length edits remain associative.
4. Only after the API/runtime/consumer chain is green, create the dedicated
   repository-canonicalization change:
   - rename the historical `brainboxemb/lib.py.solidcraft.forge` to an
     explicit `.OLD` archival name and archive it;
   - rename this repository from `.NEW` to canonical
     `brainboxemb/lib.py.solidcraft.forge`;
   - update active consumer/template references explicitly rather than relying
     on GitHub rename redirects;
   - verify branch policy, build evidence, Pages provenance, package metadata
     and release workflows after the rename.
5. Publish the first actual migrated Forge release from canonical stable
   `main`, qualified against SolidCraft 0.49.0:
   - bump the package above the historical `0.15.0` baseline;
   - add the required dated changelog section;
   - require exact full stable `build/main` evidence;
   - publish only through `/release vX.Y.Z <exact-main-sha>`;
   - update and requalify the active CAD consumer against that canonical
     release.
6. Return to Pages as a dedicated quality phase only after the first canonical
   release:
   - restore the global development warning (#57);
   - rewrite the landing page around Forge/SCPF itself (#58);
   - visually/content-audit landing, Guide, API Reference, Cheatsheet, Examples
     and Verification;
   - create one issue per remaining independent Pages defect before changing it.

#73 remains retained engine/runtime regression evidence. The accepted flat-first
consumer construction order is not a Forge replay workaround target; do not
force `plane.fixed=true`, move physical holes, or change replay semantics merely
to mask the historical SolidCraft sheet-state behavior.

## Later

1. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
2. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
