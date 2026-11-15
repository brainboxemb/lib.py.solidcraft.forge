# Forge foundational remediation plan

Status: **draft implementation order from audit 2026-11**

This plan turns the findings in
[`audit-2026-11.md`](audit-2026-11.md) into small, dependency-ordered product
changes.

The order is intentional. A later phase must not be pulled forward merely
because its local patch is smaller.

## Phase 0 — Architecture/evidence baseline

Before product code:

- keep research PR #178 unmergeable/research-only;
- preserve the audit and architecture in PR #183;
- pin SolidCraft 0.42.0 as the only native target;
- retain the authoritative occurrence identity contract captured from 0.42;
- stop creating roadmap issues for foundational blockers.

Exit condition:

- occurrence identity/replay design is normative;
- no implementation relies on `Component:N` as an accepted fallback.

## Phase 1 — Execution document and runtime result binding

Purpose: provide the infrastructure needed to use the actual occurrence ids
returned by SolidCraft.

Build on the proven ideas from historical PR #166, but re-review/rewrite on
current `main`.

Deliver:

- typed/validated Forge execution document;
- logical result bindings (`$ref` or equivalent);
- phase planning only at unresolved-result barriers;
- outer native checkpoint for atomic multi-phase execution;
- live execution;
- replay that resolves fresh native ids;
- headless qualification executor using the same execution semantics;
- raw/static SolidCraft command export only when the plan has no runtime
  identity dependency.

Do **not** migrate assembly lowering yet.

Qualification:

- unit validation of reference graph;
- fake transport tests;
- native 0.42 create -> returned occurrence id -> later move;
- native 0.42 copy -> returned occurrence id -> later move;
- failure in a later phase restores the whole model;
- replay produces fresh ids and the same geometry.

Exit condition:

> Forge can reliably carry one SolidCraft-owned runtime id to a later command.

## Phase 2 — First-class DefinitionId and OccurrenceId semantic IR

Purpose: stop using Python object id and display names as compiler architecture.

Introduce internal semantic specs:

```text
DefinitionSpec(DefinitionId, ...)
OccurrenceSpec(OccurrenceId, DefinitionId, Placement, ...)
AttachmentSpec(parent OccurrenceId, child OccurrenceId, ...)
GroupSpec(...)
```

Public API stays unchanged.

Deliver:

- unique OccurrenceId created for every physical occurrence;
- `copy()` creates a new OccurrenceId;
- duplicate insertion of one occurrence object is rejected;
- authored `name=` remains a label/lookup alias;
- all semantic relationships use OccurrenceId;
- definition identity contains every build-affecting input.

Qualification:

- no native command generation required for semantic IR tests;
- duplicate occurrence test;
- copy identity test;
- attachment survives immutable graph transformations.

Exit condition:

> The complete assembly relationship graph can be inspected without any native
> name or Python `id()`.

## Phase 3 — Migrate assembly lowering to registered native identity

Purpose: remove predicted SolidCraft names.

Deliver:

- bind `component.create.result.occurrence` for first occurrences;
- bind every `occurrence.copy.result.occurrence`;
- later move/joint/origin commands use logical refs;
- remove:
  ```python
  native_name = f"{component_name}:{index}"
  ```
- remove `Component:N` expectations from semantic tests;
- keep native display names only as optional diagnostics.

Qualification:

- root Placement;
- symbolic Placement;
- rotated copies;
- two same-definition copies;
- joints between copied occurrences;
- nested group occurrence paths;
- save/reopen and replay.

Exit condition:

> Changing SolidCraft browser numbering cannot change the generated model.

## Phase 4 — Separate hierarchy from mechanics

Purpose: make `.group()` mean only hierarchy.

Deliver:

- GroupSpec is browser/native hierarchy only;
- grouping does not imply `grounded=True`;
- root/mechanical grounding is a separate native policy;
- `Assembly.group()` remaps the complete occurrence relationship graph;
- one reusable definition may be evaluated for occurrences under different
  parents based on actual SolidCraft 0.42 capability, rather than the current
  compiler shortcut.

Qualification:

- group before/after attachment gives equivalent relationships;
- independently grouped parts;
- externally attached grouped children;
- HUB75-like sideboards + CornerBrackets regression;
- saved width/height/depth mutation.

Exit condition:

> Grouping a correct semantic assembly cannot change its mechanical solution.

## Phase 5 — Definition identity and namespace correctness

Purpose: make reuse deterministic.

Deliver:

- definition identity includes every build-affecting input;
- inherited/external parameter values cannot disappear through deduplication;
- dataclass fixed non-numeric inputs are represented;
- unsafe/unserializable build inputs force explicit identity/separate
  definitions;
- unique compiler namespace comes from DefinitionId;
- remove lossy human-name slug as uniqueness mechanism.

Qualification:

- same class, same inputs -> one definition;
- same class, different numeric fixed input -> two definitions;
- same inherited binding name but conflicting default -> explicit conflict;
- bool/string/enum dataclass variant -> distinct definition;
- deliberate slug collision case (`Foo 2` vs `Foo_2`).

## Phase 6 — Typed native expressions and dependency graph

Purpose: stop inferring parameter semantics from arbitrary strings.

Deliver:

- typed expression/reference values in compiler IR;
- parameter namespacing rewrites only expression nodes;
- literal text, material names, feature names and enum strings remain opaque;
- dependency graph records actual emitted native dependencies;
- parameter publication is not treated as proof of associativity;
- `pv()`/authoring-time picks are classified explicitly.

Qualification:

- Text2D literal equal to parameter name is unchanged;
- material/name collision examples;
- partial dependency flattening is detected;
- root model and `@assembly` use the same dependency-loss diagnostics.

## Phase 7 — Transform-safe attachment references

Purpose: eliminate partial rotation support.

Deliver:

For every Anchor/AnchorFrame/AnchorTopology combination under rotated
Placement:

- full coordinate-frame transformation; or
- early explicit rejection.

No translation-only approximation.

Qualification:

- face anchor on rotated parent/child;
- direct AnchorFrame rotation;
- topology references;
- corner references;
- save/reopen mutation where supported.

## Phase 8 — Sketch/profile semantic contract

Purpose: align implementation with normative design.

Deliver:

- implement `sketch.add(profile, anchor=CENTER)`;
- make semantic centring the default as documented;
- reserve `offset=(u,v)` for actual design displacement;
- migrate tests/examples away from `(-width/2,-height/2)` centring hacks;
- signed-extrusion design remains separate change 0006.

Qualification:

- centered rectangle/circle/rounded rectangle;
- symbolic dimensions;
- deliberate offset;
- external PythonSCAD/pyBOSL2/CadQuery references.

## Phase 9 — Qualification and release cleanup

Deliver:

- one native validation source, not skipped duplicate native unittest classes;
- derive all native version assertions from
  `TESTED_SOLIDCRAFT_VERSION`;
- add Q5 wherever public behaviour claims associativity;
- requalify/remove old 0.30.1 workarounds;
- classify tests by semantic/native-adapter/native-qualification layer;
- add architecture blockers to release validation.

Release gate:

- Q1-Q6 all green;
- no open foundational blocker;
- downstream CAD project passes pinned Forge release;
- generated docs/reference/agent source agree with the implementation.

## Phase 10 — Downstream CAD migration

Only after Forge foundations are released:

- pin the CAD repository to the new Forge version;
- remove workarounds that duplicated library/compiler responsibilities;
- rebuild the HUB75 complex example;
- reintroduce AnchorFrame use only where it is the simplest semantic
  relationship;
- keep explicit Placement where no relationship is needed.

The CAD project is validation of Forge. It is not where Forge compiler bugs are
worked around.
