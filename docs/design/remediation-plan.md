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

## Phase 1 — Give every Forge occurrence a stable internal identity

Purpose: stop using Python `id()`, list position and SolidCraft browser names to decide which Forge occurrence an attachment or Placement belongs to.

Deliver:

- explicit internal component-definition id and occurrence id;
- `copy()` creates a new occurrence id while sharing component-definition id;
- one occurrence identity may appear only once in an assembly graph;
- attachments/group transformations preserve occurrence references;
- definition identity includes every build-affecting input.

Qualification:

- Forge-object tests only; no SolidCraft-generated names;
- duplicate occurrence rejection;
- copy identity;
- attachment graph survives grouping/immutable replacement.

Exit condition:

> The complete Forge assembly graph is unambiguous before native lowering.

## Phase 2 — Replay-first Placement lowering and SolidCraft command limits

Purpose: remove avoidable post-create occurrence targeting while preserving
static replay.

Deliver:

- lower ordinary Placement directly through `component.create` and
  `occurrence.copy` wherever SolidCraft 0.42 supports it;
- isolate every remaining command that needs to address an already-created
  occurrence;
- for each such command, use only a proven replay-safe SolidCraft reference
  mechanism;
- remove guessed `Component:N` addressing;
- if no replay-safe selector exists yet, reject/mark that specific capability
  unsupported rather than adding a runtime execution plan.

Explicit non-goal:

- no `$ref` result bindings;
- no phased Forge-managed execution as the normal compiler route.

Qualification:

- first occurrence Placement;
- copy Placement, including symbolic values supported natively;
- rotated copies where create/copy semantics support them;
- replay produces the same design without Forge runtime result capture;
- tests fail if a generated browser name is used as a selector.

Exit condition:

> Normal Placement no longer depends on guessed SolidCraft names or a later
> identity-resolving move.

## Phase 3 — Replay-safe joint/attachment command generation

Purpose: keep joints/attachments only for genuine relationships.

Deliver:

- enumerate attachment/joint paths that need native occurrence references;
- use only replay-safe qualified selectors;
- keep attachment meaning separate from seed Placement;
- reject unsupported relationship cases instead of guessing names or adding
  runtime result binding;
- preserve ordinary Placement as the preferred tool when no relationship is
  required.

Qualification:

- focused relationship cases only;
- initial native geometry/relationship inspection;
- saved-design mutation where associativity is claimed;
- no `Component:N` prediction.

Exit condition:

> Every supported relationship has a replay-safe native addressing contract.

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
- unique compiler namespace comes from component-definition id;
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

- typed parameter expressions in the compiler;
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
- make centering defined by the Forge sketch API the default as documented;
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
- classify tests by Forge-object/SolidCraft-command/native-qualification layer;
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
- keep explicit Placement for ordinary component positioning;
- introduce an attachment/joint relationship only where the CAD design
  actually needs a persistent semantic relationship between occurrences;
- do not reintroduce AnchorFrame merely because Forge supports it.

For the HUB75 wood frame, AnchorFrame is **not** a migration goal. If the model
is clear and robust with explicit Placement, it should remain that way.

AnchorFrame remains a low-level relationship/frame primitive that can be used
later only when a concrete model benefits from defining an explicit attachment
frame that cannot be expressed more simply.

The CAD project is validation of Forge. It is not where Forge compiler bugs are
worked around, and it is not a showcase that must exercise every Forge API.
