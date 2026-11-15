# SolidCraft execution and occurrence identity

Status: **normative replay contract for SCPF 0.3.0**

This document separates the normal replay-first compiler from possible future
live execution modes.

## 1. Normal Forge contract: static native replay

The normal Forge path is:

```text
Python model
    -> Forge compiler
    -> native SolidCraft commands.json
    -> save / replay directly in SolidCraft
```

Replaying the generated command document must not require Python, Forge or a
Forge-specific runtime result-binding layer.

This is the release path qualified by SCPF 0.3.0.

## 2. Verified SolidCraft 0.42 occurrence capabilities

### component.create

Creates a reusable component and its first occurrence.

### occurrence.copy

Creates another occurrence of the same component definition. For a concrete
Position it accepts numeric `translate=[x,y,z]` at creation time.

Forge prefers this direct lowering for concrete copied positions.

### occurrence.move

Targets an existing occurrence and can store length expressions in
`translate`.

PR #158 proved the important behaviour:

```json
{"command":"occurrence.copy","params":{"component":"Block"}}
{"command":"occurrence.move","params":{
  "occurrence":"Block:2",
  "translate":["offset",0,0]
}}
```

After saving the model, changing `offset` from 40 to 70 moved the second
occurrence without rerunning Python and without a placement joint.

That is qualified native parametric occurrence positioning in SolidCraft 0.42.

## 3. Static occurrence targeting

SolidCraft 0.42 assigns sequential occurrence labels such as:

```text
Block:1
Block:2
```

Forge's current replay-first lowering uses this naming behaviour where a later
native command must address a newly created occurrence.

This behaviour is not treated as a universal CAD invariant. It is a
**version-qualified SolidCraft backend contract**. Qualification must therefore
cover every static targeting pattern Forge relies on, especially:

- first occurrence;
- copied occurrence;
- multiple repeated occurrences;
- parametric Position;
- Position plus orientation;
- attachment after placement;
- nested/grouped occurrences where naming context differs.

If a future SolidCraft version changes occurrence naming, its upgrade
qualification must fail before Forge claims compatibility with that version.

## 4. Position lowering rules

Forge API semantics and backend commands remain separate.

### Concrete copied Position

```text
copy().at(Position(x=40))
    -> occurrence.copy(..., translate=[40,0,0])
```

No follow-up occurrence target is needed.

### Parametric Position

```text
copy().at(Position(x=half(spacing)))
    -> occurrence.copy(...)
    -> occurrence.move(target, translate=["spacing / 2",0,0])
```

This uses the SolidCraft 0.42 expressed-move capability qualified in #158.

### Position plus orientation

A full Placement may require native `occurrence.move` even when translation
was already supplied during copy creation. Forge emits only the native
operations needed to establish the declared final pose.

None of these lowering choices introduce a public Forge move action.

## 5. Replay-first qualification requirement

A lowering that depends on occurrence targeting is supported only when it has
native evidence against the target SolidCraft release.

For parametric Position this includes:

1. generated command contract;
2. successful native build;
3. saved/reopened design;
4. `parameters.change` without rerunning Forge;
5. measured occurrence movement;
6. no hidden placement joint.

Repeated symmetric parametric positioning is additionally required for 0.3.0
because it matches the HUB75 WoodFrame use case.

## 6. Result handles are not required by normal Forge

SolidCraft command results also contain numeric occurrence ids. A future
execution mode could run commands in phases and bind later commands to those
returned ids.

That may be useful for an explicitly selected live/resolved executor, but it
changes the execution model:

```text
compile phase A
execute
read result ids
compile/resolve phase B
execute
```

Such an executor is tracked separately in roadmap issue #168.

It is **not** required for normal SCPF 0.3.0 compilation and must not leak
`$ref` or Forge-only bindings into replayable command documents.

## 7. Rejected workaround: placement joints

Forge must not convert Position/Placement into a planar or rigid joint merely
to retain a parameter expression.

A joint is an assembly relationship. Position is occurrence state.

SolidCraft 0.42 already provides native expressed occurrence positioning, so
the historical placement-joint workaround is neither necessary nor semantically
correct.

## 8. Upgrade rule

Occurrence naming/targeting is part of the SolidCraft compatibility surface.
When changing `TESTED_SOLIDCRAFT_VERSION`:

- rerun the full native qualification;
- specifically verify repeated and parametric occurrence targeting;
- verify saved-model mutation;
- do not infer compatibility from API shape alone.

If static replay targeting stops being reliable in a later SolidCraft version,
Forge must report that compatibility gap or deliberately introduce a separately
designed execution mode. It must not silently change Position semantics.
