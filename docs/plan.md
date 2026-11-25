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
  qualification;
- stable Pages quality phase promoted to main
  `b091449dab32e75ef3c4f22ca0679d21f21beedf`, with full 47-owner evidence
  and canonical stable Pages deployment.

The historical repository is being finalized as
`brainboxemb/lib.py.solidcraft.forge.OLD`, an archived A/B/provenance reference.

## Now

### #139 — A4 drawing PDF artifacts

Turn the accepted native component drawing into a consumable build artifact:

- make `iso-a4-part` the default drawing template while retaining explicit
  `iso-a3-part` support;
- replay-bind the native drawing id and declare a safe relative PDF artifact;
- have `builder-scpf` reopen the saved native design and call SolidCraft
  `drawing.export` to create a vector PDF below `drawings/`;
- prove `components` produces `drawings/Block-drawing.pdf` on the pinned
  SolidCraft 0.49.0 runtime;
- publish the API/reference documentation needed by the CAD consumer;
- after acceptance, release Forge and consume that release in the CAD
  `sample-plate` owner as the first public A4 drawing/PDF verification.

The release/CI correction and the Forge Pages quality phase are complete on
stable `main`.

Accepted stable state:

- release branches start from stable `main`, allow only release metadata and
  reuse retained full product evidence only across validated release-only
  history;
- Forge v0.16.0 remains the current canonical package release;
- stable Pages source:
  `b091449dab32e75ef3c4f22ca0679d21f21beedf`;
- permanent stable build `45623785680`: PASS;
- durable stable evidence: `full: true`, `library: true`, 47/47 owners;
- Pages assembly/publication `45624236854`: PASS;
- GitHub Pages deployment `45624348968`: PASS;
- the stable public site includes the accepted #57/#58/#68/#106/#107/#109/
  #112/#113 content and presentation fixes.

No release blocker remains from the completed stabilization phase.

Forge work should now return to demonstrated consumer value rather than
continuing a broad migration/site-cleanup stream:

1. keep #73 as retained engine/runtime regression evidence, not a replay
   workaround target;
2. prioritize migrated product/API backlog (#59-#72) only when an active CAD
   consumer or concrete design requirement needs it;
3. keep template.cad.library #62 as the non-blocking generic optimization for
   avoiding full model qualification on history-only `main -> dev` syncs;
4. coordinate new Forge API changes with the active CAD repository rather than
   adding speculative coverage.

CAD project work continues independently and may now consume the stable Forge
and release-flow baseline.

## Later

1. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
2. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
