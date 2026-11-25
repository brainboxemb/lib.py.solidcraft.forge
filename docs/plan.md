# Forge plan

This file contains unfinished work only.

## Accepted baseline

The Forge migration is complete and promoted to stable `main`.

The accepted baseline now has:
- 49 physical model owners;
- SCPF as primary per owner;
- historically real reference implementations local to the same physical owner;
- native and applicable geometry verification;
- 36 model-local approved SolidCraft visual-verification policies;
- current per-view native evidence generated from `model.sc`;
- saved-design and inspection behavior retained where historically real;
- `components` as one physical owner with
  `purpose: [example, verification]`;
- exactly four public Examples;
- all 49 physical owners projected into Verification;
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
- canonical post-migration releases through `v0.18.0`; v0.18.0 is published
  from exact stable main `009a2bd86dad7c4d452d72a4541f4bdf2dbd34d2`;
- shared topology selection is part of the stable public API:
  `Edges.from_faces(...)`, one world-cardinal `Faces` vocabulary, and
  replay-bound native `model.faces` / `model.edges` identity;
- the stable v0.18.0 source has exact full schema-2 evidence with
  `library: true` and all 49 physical owners passing;
- stable Pages quality and the canonical Pages deployment remain accepted.

The historical repository is being finalized as
`brainboxemb/lib.py.solidcraft.forge.OLD`, an archived A/B/provenance reference.

## Now

Forge **v0.18.0** is the current canonical package release.

Accepted stable state:

- #148 shared face/edge topology selection is implemented, promoted and
  released;
- `Edges.from_faces(...)` selects complete native boundaries of named
  cardinal faces without caller XYZ picks;
- TOP/BOTTOM, LEFT/RIGHT and FRONT/BACK are one documented world-cardinal
  `Faces` vocabulary across topology consumers;
- SolidCraft-returned face/edge identity is resolved at replay time and native
  `{body, index}` edge references are consumed by modify features;
- the Box one-face and XZ FRONT/BACK two-face qualification owners are part of
  the 49-owner stable graph;
- stable product promotion #150 / PR #152 received full qualification and was
  integrated with the policy-selected merge commit;
- release #151 / PR #153 published annotated tag `v0.18.0` exactly at
  `009a2bd86dad7c4d452d72a4541f4bdf2dbd34d2`;
- stable-to-development synchronization #154 / PR #155 returned the release
  metadata to `dev` without rebasing shared history.

### Active: #160 first-class Drawings documentation and verification

Expose the already released native drawing feature as a first-class Forge
capability rather than an incidental part of Components/API documentation.

Current branch: `feature/160-drawings-capability-pages`.

Acceptance:
- add Drawings as a dedicated Guide chapter;
- add one physical `sample-plate-drawing` owner with
  `purpose: [example, verification]`;
- add an eighth Verification section, Drawings;
- render/link implementation-local vector PDFs from durable build evidence
  without copying them into `gh-pages`;
- add a Drawings Cheatsheet group;
- qualify the new owner natively against pinned SolidCraft;
- keep A4 default and A3 explicit behavior unchanged.

### Active: #156 release-only stable push selection regression

The v0.18.0 release PR itself correctly selected only the `release` module,
the library owner and zero model owners. The subsequent metadata-only stable
`main` push unexpectedly reran full 49-owner qualification and published a
new full baseline instead of retaining the previous full product evidence.

This did not invalidate v0.18.0: the exact release SHA received stronger
full/library/all-owner evidence and the release validator accepted it.
Nevertheless it violates the documented release optimization contract and must
be corrected separately without changing v0.18.0 provenance.

After #156:
1. keep #73 as retained engine/runtime regression evidence, not a replay
   workaround target;
2. prioritize migrated product/API backlog (#59-#72) only when an active CAD
   consumer or concrete design requirement needs it;
3. keep template.cad.library #62 as the non-blocking generic optimization for
   avoiding unnecessary full qualification on history-only synchronization;
4. coordinate new Forge API changes with the active CAD repository rather than
   adding speculative coverage.

CAD project work may consume Forge v0.18.0 as the stable topology-selection
baseline.

## Later

1. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
2. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
