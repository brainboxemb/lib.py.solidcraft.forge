# Forge compiler design

Status: **draft — audit-controlled**  
Applies to: SCPF component/occurrence handling and SolidCraft 0.42 commands

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
Forge components and occurrences
    ↓
check Placement, groups, attachments and parameters
    ↓
generate SolidCraft 0.42 commands
    ↓
static replayable SolidCraft document
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

### 2.3 Referring to a SolidCraft occurrence

Some SolidCraft commands need to point at an occurrence that already exists.

Forge may only use a reference form that is explicitly supported and qualified
for replay by SolidCraft 0.42. Forge must never construct such a reference by
guessing a generated browser name such as `Board:2`.

### 2.4 Display/browser name

A name displayed by SolidCraft, including generated forms such as
`Component:1`, is presentation state unless the authoritative SolidCraft
schema explicitly defines it as a stable programmable identifier.

**Rule ID-1**

> Forge must never predict a SolidCraft-generated occurrence name in order to
> address an occurrence later.

**Rule ID-2**

> Changing SolidCraft browser numbering must not change which Forge objects are
> moved, joined or inspected.

**Rule ID-3**

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

**Rule PL-1**

> Placement never creates a joint as an implementation workaround.

**Rule PL-2**

> Numeric and symbolic Placement describe the same semantic operation; only
> SolidCraft command generation differs.

**Rule PL-3**

> Copying an occurrence with a new Placement creates a new occurrence identity
> sharing the same reusable definition.

Any SolidCraft-specific distinction between "implicit first occurrence",
`occurrence.copy`, and `occurrence.move` belongs in the SolidCraft command generator.

## 5. Relationships and joints

`attach()` creates a attachment relationship between two Forge occurrences.

The attachment relationship contains:

- parent OccurrenceId;
- child OccurrenceId;
- parent local attachment reference;
- child local attachment reference;
- gap/offset/angle/as-built intent.

It does **not** identify either side using a SolidCraft browser name.

**Rule JT-1**

> One Forge attachment lowers to the required native relationship command(s);
> the relationship addresses native occurrences only through registered native
> references.

**Rule JT-2**

> A seed pose used to help the native solver is not the attachment relationship.

**Rule JT-3**

> Grouping or browser hierarchy must not silently add, remove or change the
> attachment relationship.

### Local attachment references

Keep distinct:

- standard `Anchor`;
- direct `AnchorFrame`;
- `AnchorTopology`;
- authored named anchors.

A named anchor is allowed because Forge owns that name. It must be
resolved to a definition-local reference before native occurrence addressing.

This is unrelated to predicting SolidCraft-generated occurrence names.

## 6. Grouping and hierarchy

`.group("CornerBrackets")` means hierarchy/browser organisation.

**Rule GR-1**

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

**Rule GR-2**

> Re-grouping an existing semantic assembly must preserve the complete
> occurrence relationship graph.

Immutable replacement of occurrences must remap every occurrence reference,
including attachment targets and assembly-owned anchors.

## 7. Rotation and coordinate transforms

Forge must not provide a partially correct transform path.

**Rule TR-1**

For each public combination of Placement rotation + attachment reference:

- transform the complete local point/frame/topology correctly; or
- reject the combination before native command generation.

Adding translation while ignoring rotation is not an acceptable fallback.

The Forge compiler should not implement an independent CAD solver, but basic
coordinate-frame transformation needed to preserve authored occurrence intent
belongs in the compiler/adapter boundary when SolidCraft requires explicit
world picks.

## 8. Parameter dependencies

Public parameters are dependency objects, not just numbers.

**Rule PA-1**

> Symbolic dependency is preserved until an operation explicitly requires a
> concrete Python value.

`pv()` marks such an explicit loss of symbolic dependency.

**Rule PA-2**

> Parameter publication and parameter dependency are separate concepts.

A nested component may consume a parent Parameter without publishing a duplicate
local parameter.

**Rule PA-3**

> Definition deduplication must include every build-affecting input.

The audit must verify how reference fields participate before the final
DefinitionId algorithm is chosen.

**Rule PA-4**

> User-authored strings and native name/enum fields are opaque data.
> Parameter namespacing may rewrite only typed parameter expressions and
> references, never arbitrary strings.

## 9. Compiler steps

`compile_assembly()` currently handles too many unrelated jobs in one
function. Split those jobs into concrete steps.

### Step A — collect Forge objects

Read the `ModelInstance` / `Assembly` and collect:

- component definitions;
- occurrences;
- `Placement` values;
- groups;
- attachments;
- parameter dependencies.

No SolidCraft-generated occurrence names are created here.

### Step B — validate the Forge model

Before generating SolidCraft commands, check:

- every attachment target is actually present;
- one occurrence object is not inserted twice;
- grouping did not break an attachment reference;
- two occurrences only share one component definition when their build inputs
  really match;
- unsupported rotated attachment cases fail explicitly;
- parameter conflicts are reported.

### Step C — generate SolidCraft commands

Generate `component.create`, `occurrence.copy`, Placement, group and joint
commands from the checked Forge model.

SolidCraft-specific workarounds belong here and must be tied to the exact
SolidCraft version/case that requires them.

### Step D — qualify the generated model

Check:

- the generated commands are valid for SolidCraft 0.42;
- the initial geometry is correct;
- saved parameter changes update what Forge claims is associative;
- groups do not change mechanical relationships;
- replay gives the same model.

## 10. First-occurrence behaviour

SolidCraft may create one implicit occurrence when a component definition is
created.

That is a native-engine fact, not a Forge semantic distinction.

**Rule NA-1**

> "first occurrence" may exist inside the SolidCraft adapter but never as the
> identity of the semantic occurrence.

The adapter may choose which Forge occurrence is bound to that native implicit
occurrence, but the binding must be explicit in its registration table.

## 11. Public script surface

Forge currently has both:

- normal package imports (`from scpf import ...`);
- an implicit namespace injected by `run_script()`.

**Rule API-1**

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

### Generated SolidCraft command tests

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

## 13. Replay-first occurrence handling

The normal Forge output is a static SolidCraft command document that can be
replayed without Forge staying in the execution loop.

### 13.1 Put Placement in create/copy where possible

For ordinary positioning:

- use `component.create` placement fields for the first occurrence where
  SolidCraft supports them;
- use `occurrence.copy` placement fields for copies where SolidCraft supports
  them;
- do not create an occurrence at one location and then add a later
  `occurrence.move` merely because the current compiler was written that way.

### 13.2 Never guess SolidCraft occurrence names

This is forbidden:

```python
native_name = f"{component_name}:{index}"
```

Forge does not control SolidCraft's generated browser numbering.

### 13.3 If replay cannot address an occurrence safely, do not fake it

Some later commands, especially joint-related commands, need to point at an
already-created occurrence.

For each such command we need a replay-safe SolidCraft reference that has been
qualified on 0.42.

If we do not have one yet, that specific Forge capability is unsupported until
we do. Do not solve it by:

- guessing `Component:1` / `Component:2`;
- adding runtime `$ref` result binding to the normal compiler path;
- adding a joint merely to avoid a Placement problem.

Historical runtime-result-handle experiments remain useful background, but they
are not the normal Forge architecture.

## 14. Migration strategy

Do not rewrite Forge in one large PR.

Recommended implementation order after the audit:

1. give each Forge occurrence a stable internal identity;
2. lower ordinary Placement directly through `component.create` /
   `occurrence.copy` where SolidCraft supports it;
3. remove all guessed `Component:N` addressing;
4. explicitly reject relationship cases that still lack a replay-safe
   occurrence reference;
5. repair grouping so it only changes hierarchy;
6. fix attachment handling under rotation;
7. align the implicit script namespace with the public package exports;
8. rewrite tests that currently depend on SolidCraft browser numbering;
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
