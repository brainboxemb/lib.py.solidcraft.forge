# Forge example and verification history

This document records how the current Forge example tree and 32-case
Verification catalog evolved. It exists to make repository history explicit;
it is not a second executable catalog.

Current behavior is defined by source, per-item CAD-CI configuration and durable
build evidence. Historical issue/commit references below explain why files and
fixtures exist and which migrations were completed or left unresolved.

## Current repository roles

`examples/` contains more than one kind of asset.

1. **Verified model cases** — the current 32-case catalog. These have local
   `model.yml`, `ci.yml`, `README.md`, `verification/verify.py` and four
   independent reference children.
2. **Forge release-verification fixtures** — a small fixed set used by
   `scripts/tool_verify.py`. Four overlap the 32-case catalog; `custom-anchor`
   is an expected-rejection fixture outside it.
3. **Focused regression/authoring fixtures** — older or narrow examples that
   were introduced to prove one compiler/API behavior and do not currently own
   a complete model-verification item.
4. **Legacy documentation/sample material** — historical examples that are not
   currently verified and require an explicit keep/migrate/remove decision.

The existence of a directory below `examples/` therefore does not by itself
mean "current Verification case".

## Where the number 32 comes from

The number 32 did not originate in the current Pages generator.

Immediately before the legacy top-level `qualification/` implementation was
removed by #393, commit
`be40b09e7454a90e87d83768a9e7453c52ba5d76` contained the last canonical
`QUALIFICATION_CASES` registry. It contained exactly these 32 slugs:

```text
simple-box
anchored-holes
hole-family
sheet-fold
top-sketch-after-chamfer
parameter-scope
parent-derived-child-size
components
repeated-parent-attachments
assembly-decorator
group-hierarchy
attach-angle
parametric-attach
parametric-offset
parametric-anchor
corner-anchor
anchor-topology-mutation
assembly-owned-anchor
four-corner-l
eight-corner-brackets
eight-flightcase-corners
xz-anchor
round-top-sketch
circle-negative-extrude
sketch-pattern-mirror
selective-profile-extrude
circular-feature-pattern
rectangular-pattern
slot-family
rounded-rectangle-sketch
primitive-csg
bracket
```

That historical registry is the lineage source for the current 32 model
verification cases. #548 later moved its human engineering text into the owning
example READMEs rather than keeping a central catalog.

The current site discovers those cases from local `examples/*/model.yml`
files. The current count is still 32, but "there are 32 model.yml files" is not
the historical justification for the catalog; it is only the current
distributed representation of the already-migrated historical set.

## Qualification to Verification timeline

### 2026-11-14 to 2026-11-15 — active Qualification catalog grows

The central `qualification/cases.py` registry grew as Forge capabilities were
added. At commit `a34f270c` (2026-11-14, as-built attachment) it contained 20
cases. By SCPF 0.3.2 commit `6472c7ca` on 2026-11-15 it contained 27.

At that point the registry included five cases that are not in the current
32-case set:

- `as-built-attach`;
- `custom-anchor`;
- `parametric-move`;
- `parametric-placement-pair`;
- `rotated-copy-placement`.

### 2026-11-15 — replay-first Placement removes three cases

Change 0009 / commit `9ff0bc28` removed these native Q3-Q6 cases:

- `parametric-move`;
- `parametric-placement-pair`;
- `rotated-copy-placement`.

The documented reason was not that the examples were unimportant. Their native
lowering depended on a predicted SolidCraft occurrence name such as
`Component:2`. Change 0009 explicitly said they could return to native
qualification after Forge had a replay-safe SolidCraft occurrence selector.

Focused Python/command tests were retained.

### 2026-11-16 — replay-safe attachments remove two more cases

Change 0010 / commit `3293e760` removed:

- `as-built-attach`;
- `custom-anchor`.

The same change retained other affected component/corner cases in the central
catalog as explicit `BLOCKED` cases instead of deleting them.

This distinction matters: removal from the registry was a capability-state
decision at that point in time, not evidence that the example directory no
longer had value.

### 2026-11-16 — replay variables restore the missing mechanism

Change 0013 / issue #191 / commit `585b58bf` introduced deterministic replay
variables bound to the real occurrence IDs returned by
`component.create`/`occurrence.copy`.

That restored:

- symbolic occurrence Placement;
- rotated copy Placement;
- non-identity first-occurrence Placement;
- copied attachment endpoints;
- rotated as-built attachment;
- the previously blocked component/corner cases.

The central catalog was rewritten to use the replay-safe mechanism, but the five
cases removed in changes 0009/0010 were not re-added.

No current historical decision has been found that explicitly says those five
cases were permanently superseded. Their absence must therefore not be
interpreted as an intentional permanent removal without a current review.

### 2026-11-16 to 2026-11-18 — catalog grows to the final 32

New feature cases for sketches, patterns, slots, holes, sheet metal and other
current Forge capabilities were added. The last canonical pre-removal registry
contained 32 cases.

### 2026-11-19 — central Qualification implementation removed

#393 removed the top-level `qualification/` implementation and deliberately did
not replace it with another central runner. The exact historical implementation
was retained in Git history at
`be40b09e7454a90e87d83768a9e7453c52ba5d76`.

#394 then proved the new per-model `model_verify` path with `simple-box`.
#395 migrated the next ten historical cases in registry order.

### 2026-11-19 to 2026-11-20 — declarative per-model migration

#432 migrated model-specific verification from procedural
`verification/verify_model.py` files to declarative
`verification/verify.py` contracts backed by released
`lib.py.cad.verification`.

#544/#545 migrated the final procedural case, `sketch-pattern-mirror`.
At that point all 32 historical cases were declarative, but six were still
intentionally `process: false`.

### 2026-11-20 — all 32 cases activated and made durable

#546/#547 activated the final six:

- `assembly-owned-anchor`;
- `corner-anchor`;
- `eight-corner-brackets`;
- `parametric-anchor`;
- `parametric-attach`;
- `parametric-offset`.

The acceptance result records main commit
`b4f601173d4a5ffddb7b0e2321b9d9174cce5c30` and main workflow run
`44819058164` as green with durable publication.

From this point the current 32-case catalog had:

- 32 active model `ci.yml` items;
- 32 declarative model-verification contracts;
- four independent reference child items per model (128 total);
- durable `build/main` output for every model.

### 2026-11-20 — documentation and Pages migration

#548 moved the canonical engineering text from the historical registry and
geometry-contract source into each owning README. #497 then changed stable
Pages to read source documentation plus current durable `build/main`
evidence.

The site now discovers model pages from local `model.yml` files. Tests that
assert a count of 32 protect the completed migration, but they do not by
themselves establish that every other directory in `examples/` is obsolete.

## Current hard evidence for the 32-case set

As of the build branch commit
`407f42bf410ecb4e2403fceaa661371a51afeea2`:

- `main/examples/` contains all 32 verification model scopes;
- each of those scopes has complete CAD-CI item evidence;
- each has four reference child item scopes;
- the model batch manifest lists all 32 models with `compile_error: null`;
- current source contains exactly the same 32 top-level `model.yml` and
  top-level `ci.yml` files.

Individual durable item `source_commit` values can be older than the current
site commit when no technical input for that item changed. That is expected:
presentation-only changes must reuse accepted technical evidence rather than
rerun CAD merely to rebuild Pages.

## Directories outside the 32-case catalog

### `as-built-attach`

Historical status:
- official Qualification case on 2026-11-14/15;
- removed by change 0010 when copied/as-built occurrence addressing was not
  replay-safe.

Current state:
- source and three historical independent references remain;
- local `tests/test_contract.py` expects replay-bound occurrence IDs;
- the ordinary unit suite also proves rotated as-built attachment with bound
  IDs;
- the original replay-safety blocker has therefore been removed;
- there is no current `model.yml`, model `ci.yml` or native Verification
  contract.

Assessment: **unresolved requalification gap**. The case needs an explicit
current decision: restore full Verification, replace it with documented
equivalent coverage, or retire the directory.

### `parametric-move`

Historical status:
- official Qualification case by SCPF 0.3.0;
- removed by change 0009 because symbolic occurrence movement required an
  unsafe predicted occurrence name.

Current state:
- replay variables now support symbolic `occurrence.move`;
- current unit tests prove symbolic ordinary Placement through a bound real
  occurrence ID;
- old example and historical references remain;
- no current model CI/Verification contract exists.

Assessment: **unresolved requalification gap**.

### `parametric-placement-pair`

Historical status:
- official Qualification case by SCPF 0.3.0;
- removed by change 0009 for the same replay-safety reason.

Current state:
- local contract test explicitly expects two replay-bound occurrences and
  symbolic spacing;
- the underlying mechanism is supported by current unit tests;
- no current model CI/Verification contract exists.

Assessment: **unresolved requalification gap**.

### `rotated-copy-placement`

Historical status:
- added as an official Qualification case with SCPF 0.3.1;
- removed by change 0009 because rotation required a later move addressed by a
  predicted occurrence name.

Current state:
- local contract test now requires a bound occurrence variable before
  `occurrence.move`;
- current unit tests explicitly prove rotated copies and symbolic rotated copies
  through bound IDs;
- no current model CI/Verification contract exists.

Assessment: **unresolved requalification gap**.

### `custom-anchor`

Historical status:
- official Qualification case before change 0010;
- removed when rotated normal-attachment references were made replay-safe by
  rejection instead of guessed occurrence selection.

Current state:
- the limitation still exists;
- open issue #81 tracks inline `AnchorFrame` references for rotated
  occurrences;
- `scripts/tool_verify.py` deliberately uses `custom-anchor` as an
  expected-rejection Forge release fixture.

Assessment: **intentional blocked release fixture**, not silently obsolete.
It should not become a passing Verification case until #81 (or an equivalent
current design) resolves the limitation.

### `attached-through-all`

Historical status:
- introduced by #249 as the smallest reproduction for TOP-face
  `Sketch.extrude(Depth.THROUGH_ALL)` cut direction;
- never part of the central `QUALIFICATION_CASES` registry.

Current state:
- local command-contract test remains;
- the same behavior is directly covered by
  `scpf/tests/test_sketch_attachment.py`, including TOP and BOTTOM direction;
- no model CI/Verification contract exists.

Assessment: **focused regression fixture**. Its directory role should be made
explicit; it is not evidence of a missing historical 32-case migration.

### `model_authoring`

Historical status:
- #213 explicitly required a small abstract qualification case for
  component/occurrence/material/parameter authoring boundaries;
- the fixture and local contract test were added;
- it never entered the central `QUALIFICATION_CASES` registry.

Current state:
- local `tests/test_contract.py` remains;
- no current model `ci.yml` invokes that example-local contract test;
- the general unit suite tests many authoring rules, but it does not use this
  fixture as the requested integrated example.

Assessment: **unfinished lineage**. The original request for an automatically
qualified abstract fixture was never carried into the current model-verification
architecture.

### `plate`

Historical status:
- early sample from #7, before the later Qualification catalog architecture.

Current state:
- only `README.md`, `scpf/model.py` and `scpf/reference.json` remain;
- no current model CI/Verification contract exists;
- the README still claims additional CadQuery/vcad/µcad/PythonSCAD variants,
  but those files are no longer present in the directory.

Assessment: **legacy/stale sample**. It requires an explicit keep-and-modernize
or remove/archive decision.

## Release-verification overlap

Forge release verification is intentionally a different set from the model
Verification catalog.

Current `scripts/tool_verify.py` uses:

- passing: `simple-box`, `anchored-holes`, `components`,
  `corner-anchor`;
- expected rejection: `custom-anchor`.

The first four also belong to the 32-case model Verification catalog.
`custom-anchor` does not, because its current purpose is specifically to prove
that an unsupported rotated normal attachment fails clearly.

## Stale active documentation found by this audit

Some current primary documentation still describes an earlier staged migration
state in which only five model items were `process: true`.

That statement became obsolete after #546/#547 activated the final six and the
complete durable 32-case catalog became normal current state.

Primary documentation must describe the current 32-active state; the five-case
staging history belongs here instead.

## Branches are not current-work truth

The repository currently contains many `issue/*` branches whose corresponding
issues are already closed (#430, #432, #438, #443, #444, #452, #464, #468,
#484, #497, #511 and #548 among them).

Those refs are branch-cleanup debt tracked separately by #481. Their existence
must not be used as evidence that the corresponding issue is still active.

Conversely, a closed issue also does not prove every historical follow-up was
completed. The removed/recovered cases above are an example of why capability
lineage must be checked explicitly.

## Explicit local role contract

#560 adds a repository-level structural guard without recreating a central
executable catalog.

- A full Verification case is recognized from its complete local contract:
  `ci.yml`, `model.yml`, `README.md`, `scpf/model.py`,
  `verification/verify.py` and four reference child implementations.
- Any other top-level `examples/<slug>/` directory must contain a local
  `role.yml`.
- `ci/site-source` validates this structure without starting a CAD runtime.
- A new directory that has neither form fails the source-only check.

The eight non-catalog directories now declare their current state locally.
Five are explicitly marked `verification-candidate`; the remaining three are
an intentional blocked release fixture, a focused regression fixture and a
legacy sample pending retirement/modernization.

This role metadata documents exceptions only. It does not become the membership
source for full model Verification.

## Required reconciliation

Tracked by #559.

For every directory below `examples/`, make one explicit current decision:

- current full Verification case;
- Forge release-verification fixture;
- focused regression/authoring fixture with a current executing owner;
- maintained documentation sample;
- or retired/removed historical material.

In particular:

1. Reassess the four formerly-qualified cases whose replay-safety blocker is
   now gone.
2. Resolve the unfinished `model_authoring` qualification lineage.
3. Keep `custom-anchor` explicitly blocked until its real limitation changes.
4. Make the focused `attached-through-all` role explicit.
5. Modernize or retire `plate`.
6. Add a structural guard so a new `examples/*` directory cannot silently
   exist outside every declared current role.

Do not expand the Verification catalog merely because a historical fixture
exists. The decision must follow current product behavior and current evidence.
