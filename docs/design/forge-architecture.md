# Forge compiler architecture and invariants

Status: **draft — audit-controlled**  
Applies to: SCPF / Forge semantic model and SolidCraft 0.42 adapter

This document defines how Forge should be structured after the foundational
audit. It is deliberately stricter than "the current generated commands happen
to work".

The public modelling contract remains
[`docs/05-cad-api-design.md`](../05-cad-api-design.md). This document defines
the compiler architecture required to implement that contract reliably.

## 1. Core principle

Forge describes CAD intent using Python objects.

SolidCraft is the CAD engine.

The compiler must translate between those domains without making browser/UI
side effects part of Forge semantics.

```text
Forge public objects
    ↓
semantic model / IR
    ↓
validated relationships and dependencies
    ↓
SolidCraft 0.42 adapter
    ↓
native command plan
    ↓
SolidCraft document
```

There must be an explicit boundary between Forge identity and SolidCraft
presentation names.

## 2. Identity model

Forge needs distinct identities for distinct concepts.

### 2.1 Definition identity

A **definition** represents reusable physical geometry plus all build-affecting
inputs.

Two occurrences may share one definition only when the resulting reusable
component definition is semantically the same.

Definition identity is not the SolidCraft component display name.

### 2.2 Occurrence identity

Every physical occurrence in an assembly has a Forge-owned stable identity.

Properties:

- created when the semantic assembly occurrence is created;
- a `copy()` gets a new occurrence identity;
- copies may share definition identity;
- grouping does not replace or invalidate occurrence identity;
- attachment targets point to occurrence identity;
- Placement belongs to occurrence identity;
- user `name=` is a useful authored label, not the identity mechanism.

### 2.3 Native reference

A **native reference** is the SolidCraft-side value required by commands to
refer to one occurrence.

The SolidCraft adapter owns the mapping:

```text
Forge OccurrenceId -> NativeOccurrenceRef
```

No other compiler layer may synthesize or guess that native reference.

### 2.4 Display/browser name

A name displayed by SolidCraft, including generated forms such as
`Component:1`, is presentation state unless the authoritative SolidCraft
schema explicitly defines it as a stable programmable identifier.

**Invariant ID-1**

> Forge must never predict a SolidCraft-generated occurrence name in order to
> address an occurrence later.

**Invariant ID-2**

> Changing SolidCraft browser numbering must not change which Forge objects are
> moved, joined or inspected.

**Invariant ID-3**

> One Forge occurrence identity may appear at most once in one assembly graph.
> A second physical occurrence must be created with `.copy()`, which gets a
> new OccurrenceId while retaining the same DefinitionId.

## 3. Definition vs occurrence

Public component code describes reusable geometry:

```python
board = Board(width=12, depth=60, height=80)
```

The definition owns:

- reusable geometry;
- intrinsic component parameters;
- intrinsic component anchor definitions;
- material/feature intent that is part of the physical part.

The occurrence owns:

- OccurrenceId;
- optional authored `name=`;
- Placement;
- group/hierarchy membership;
- attachment relationships involving that occurrence.

A component definition must never acquire assembly-specific state merely
because its first occurrence happened to be placed first.

## 4. Placement

`Placement` is declarative occurrence pose in the parent coordinate frame.

**Invariant PL-1**

> Placement never creates a joint as an implementation workaround.

**Invariant PL-2**

> Numeric and symbolic Placement describe the same semantic operation; only
> native lowering differs.

**Invariant PL-3**

> Copying an occurrence with a new Placement creates a new occurrence identity
> sharing the same reusable definition.

Any SolidCraft-specific distinction between "implicit first occurrence",
`occurrence.copy`, and `occurrence.move` belongs in the native adapter.

## 5. Relationships and joints

`attach()` creates a semantic relationship between two Forge occurrences.

The semantic relationship contains:

- parent OccurrenceId;
- child OccurrenceId;
- parent local attachment reference;
- child local attachment reference;
- gap/offset/angle/as-built intent.

It does **not** identify either side using a SolidCraft browser name.

**Invariant JT-1**

> One Forge attachment lowers to the required native relationship command(s);
> the relationship addresses native occurrences only through registered native
> references.

**Invariant JT-2**

> A seed pose used to help the native solver is not the semantic relationship.

**Invariant JT-3**

> Grouping or browser hierarchy must not silently add, remove or change the
> attachment relationship.

### Local attachment references

Keep distinct:

- standard `Anchor`;
- direct `AnchorFrame`;
- `AnchorTopology`;
- authored semantic named anchors.

A semantic named anchor is allowed because Forge owns that name. It must be
resolved to a definition-local reference before native occurrence addressing.

This is unrelated to predicting SolidCraft-generated occurrence names.

## 6. Grouping and hierarchy

`.group("CornerBrackets")` means hierarchy/browser organisation.

**Invariant GR-1**

> Grouping alone has no mechanical meaning.

Therefore grouping must not imply:

- grounding;
- a rigid joint;
- a Placement;
- a solver constraint.

If the native SolidCraft representation requires an intermediate component,
the adapter may create one, but any required grounding must come from an
independent mechanical/root policy, not from the fact that `.group()` was
called.

**Invariant GR-2**

> Re-grouping an existing semantic assembly must preserve the complete
> occurrence relationship graph.

Immutable replacement of occurrences must remap every occurrence reference,
including attachment targets and assembly-owned anchors.

## 7. Rotation and coordinate transforms

Forge must not provide a partially correct transform path.

**Invariant TR-1**

For each public combination of Placement rotation + attachment reference:

- transform the complete local point/frame/topology correctly; or
- reject the combination before native command generation.

Adding translation while ignoring rotation is not an acceptable fallback.

The semantic compiler should not implement an independent CAD solver, but basic
coordinate-frame transformation needed to preserve authored occurrence intent
belongs in the compiler/adapter boundary when SolidCraft requires explicit
world picks.

## 8. Parameter dependencies

Public parameters are dependency objects, not just numbers.

**Invariant PA-1**

> Symbolic dependency is preserved until an operation explicitly requires a
> concrete Python value.

`pv()` marks such an explicit loss of symbolic dependency.

**Invariant PA-2**

> Parameter publication and parameter dependency are separate concepts.

A nested component may consume a parent Parameter without publishing a duplicate
local parameter.

**Invariant PA-3**

> Definition deduplication must include every build-affecting input.

The audit must verify how reference fields participate before the final
DefinitionId algorithm is chosen.

## 9. Compiler stages

Replace the current monolithic assembly lowering with explicit stages.

### Stage A — semantic collection

Input: `ModelInstance` / `Assembly`

Output conceptually:

- DefinitionSpec objects;
- OccurrenceSpec objects with OccurrenceId;
- GroupSpec hierarchy;
- AttachmentSpec relationships;
- parameter dependency graph.

No SolidCraft-generated names exist at this stage.

### Stage B — validation

Check semantic invariants before native commands:

- all attachment targets exist;
- occurrence names are unique where required for authored lookup;
- group transformations preserve references;
- definition-sharing is valid;
- unsupported rotated attachment combinations are rejected;
- parameter conflicts are explicit.

### Stage C — native capability planning

Use the pinned SolidCraft 0.42 command schemas to determine how to:

- create definitions/components;
- register native occurrence references;
- create copies;
- apply Placement;
- author joint references;
- represent hierarchy;
- apply true mechanical grounding where required.

This stage owns every SolidCraft-specific workaround.

### Stage D — native command emission

Emit native JSON only after every semantic occurrence has a
`NativeOccurrenceRef`.

No command emitter may derive a native occurrence reference from
`component_name + index`.

### Stage E — qualification

Prove:

- command schema validity;
- initial geometry;
- saved-design parameter mutation;
- occurrence relationship correctness;
- hierarchy independent from mechanics;
- replay equivalence where relevant.

## 10. First-occurrence behaviour

SolidCraft may create one implicit occurrence when a component definition is
created.

That is a native-engine fact, not a Forge semantic distinction.

**Invariant NA-1**

> "first occurrence" may exist inside the SolidCraft adapter but never as the
> identity of the semantic occurrence.

The adapter may choose which Forge occurrence is bound to that native implicit
occurrence, but the binding must be explicit in its registration table.

## 11. Public script surface

Forge currently has both:

- normal package imports (`from scpf import ...`);
- an implicit namespace injected by `run_script()`.

**Invariant API-1**

> A documented public symbol must have one meaning on both surfaces.

The final design must choose whether the implicit namespace mirrors all public
exports or is a deliberately smaller documented prelude. Silent drift is not
allowed.

## 12. Test architecture

Tests are split by layer.

### Semantic tests

Assert:

- occurrence identity;
- definition sharing;
- Placement;
- grouping graph;
- attachment graph;
- parameter dependencies.

They do not mention `Component:1`.

### Native adapter contract tests

Assert:

- SolidCraft schema-compatible commands;
- explicit native registration;
- correct reference reuse;
- engine-specific first-occurrence handling.

They may inspect native references, but must not confuse a display label with
Forge identity.

### Native qualification

Assert real SolidCraft outcomes:

- BRep/bounds;
- parameters;
- joints/relationships;
- save/reopen;
- mutation without rerunning Python.

### Cross-library references

PythonSCAD, pyBOSL2 and CadQuery continue to express the same modelling intent
idiomatically. They are geometry/modelling comparisons, not native identity
authorities.

## 13. Native SolidCraft 0.42 identity contract

The pinned 0.42 runtime has now been introspected directly. The relevant
contract is recorded in
[`docs/vendor/solidcraft/0.42.0/occurrence-identity.md`](../vendor/solidcraft/0.42.0/occurrence-identity.md).

The important facts are:

- `component.create` returns `result.occurrence` as a numeric occurrence id;
- `occurrence.copy` returns the new numeric occurrence id;
- `occurrence.move`, joint/origin commands and component inspection accept
  native occurrence ids;
- `occurrence.copy` does not provide a field for Forge to prescribe the id of
  the occurrence that will be created.

Therefore Forge must obtain runtime identity from SolidCraft. Browser labels are
not a substitute.

### 13.1 Static native command document

A raw independently replayable SolidCraft command list remains valid when no
later command needs the identity of an occurrence created earlier in that same
document.

Examples include a copy whose complete numeric translation is supplied directly
to `occurrence.copy` and which is never subsequently referenced.

### 13.2 Identity-dependent execution document

When a later operation needs a just-created occurrence, Forge must keep a
logical reference in the serialized document and bind it to the actual native
id returned at execution time.

Conceptually:

```text
Forge OccurrenceId
    -> logical execution reference
    -> component.create / occurrence.copy
    -> SolidCraft result.occurrence
    -> NativeOccurrenceRef
    -> later move / joint / origin
```

This is required for:

- first-occurrence Placement that needs a later `occurrence.move`;
- copied symbolic Placement that needs a later move;
- copied rotation/orientation;
- attachments/joints involving created occurrences;
- custom joint origins on created occurrences;
- any later inspection/action targeting the occurrence.

Historical PRs #166/#167 implemented one version of this result-binding model.
Their code is evidence, not an automatic merge source, but the architectural
need is now confirmed by the 0.42 schema.

**Invariant EX-1**

> Identity-dependent Forge output is a Forge execution document, not a raw
> SolidCraft command list pretending generated browser labels are stable ids.

**Invariant EX-2**

> Replay resolves logical occurrence references again against the new
> execution. It never stores native ids from an earlier design.

**Invariant EX-3**

> A static/raw-native export may be offered only when the compiler proves the
> plan has no unresolved runtime identity dependency.

## 14. Migration strategy

Do not rewrite Forge in one large PR.

Recommended implementation order after the audit:

1. native 0.42 schema capture and identity experiment;
2. introduce internal `OccurrenceId` / registration table without changing
   public API;
3. move current occurrence creation/copy/move lowering behind the native
   adapter;
4. remove all predicted `Component:N` addressing;
5. repair grouping as hierarchy-only and remap the full relationship graph;
6. normalize attachment/rotation handling;
7. align script namespace with public exports;
8. reclassify and rewrite tests;
9. re-run Q1-Q6 and downstream CAD qualification.

Each step must be independently reviewable and reversible.

## 15. Non-goals

This architecture does not:

- create a second CAD kernel;
- make browser names part of Forge API;
- hide unsupported behaviour behind guessed coordinates;
- turn every shape into an occurrence;
- make every parameter public;
- require anchors for ordinary absolute Placement.

The goal is smaller: make the existing object-first Forge contract reliable,
explicit and explainable.
