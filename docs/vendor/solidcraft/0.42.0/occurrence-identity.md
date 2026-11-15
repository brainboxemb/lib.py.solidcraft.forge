# SolidCraft 0.42 occurrence identity contract

Status: **captured from pinned native runtime**  
SolidCraft: **0.42.0**  
Audit run: `43757985541`  
Forge audit source: `348dfe9e14144a509c0017417782ec8743fed8b8`

This file records only the identity-relevant conclusions from authoritative
`engine.describe` responses produced by the pinned SolidCraft 0.42.0
executable. It supplements the unchanged vendor command catalog.

The full machine-generated schemas were retained in the qualification artifact
under `output/audit/solidcraft-0.42.0/`.

## component.create

Relevant input semantics:

- `name?`: new component name;
- `parent?`: component id or name;
- `parent_path?`: exact parent placement path;
- `activate?`;
- `grounded?`.

Relevant output fields:

```text
component : integer uint64
occurrence: integer uint64 | null
name      : string
parent    : integer uint64
grounded  : boolean
```

The schema describes `occurrence` as:

> Its placement, by id.

Therefore creation of the first placement exposes the actual native occurrence
identity in the command result.

## occurrence.copy

Input accepts either:

- `occurrence`: occurrence id or name; or
- `component`: component id or name.

Additional fields include `path`, `parent`, `parent_path`, `translate`
and `in_place`.

Relevant output:

```text
component : integer uint64
occurrence: integer uint64
```

The schema describes `occurrence` as:

> The new placement, by id.

Therefore every copied occurrence exposes its actual native occurrence identity
in the command result.

## occurrence.move

Required input:

```text
occurrence: occurrence id or name
```

It also supports an exact occurrence `path`.

The output again returns:

```text
occurrence: integer uint64
transform : 4x4 placement matrix
pending   : boolean
```

A parameter-expression `translate` is explicitly documented as associative:
the occurrence moves with the named parameters when they change.

## component.list

The native component tree exposes occurrence/placement ids explicitly.

In compact placement information:

```text
id       : occurrence id
name     : string
parent   : component id
grounded : boolean
transform: optional matrix
```

The command therefore distinguishes native occurrence id from display name.

## joint/origin commands

The 0.42 joint/origin schemas accept occurrence references by id or name, and
exact nested placement paths where needed.

`joint.origin` explicitly documents:

```text
occurrence?: id | name
path?: [occurrence ids from root]
```

Thus the same native numeric occurrence identity returned by create/copy is
usable by later relationship commands.

## Architectural conclusion

SolidCraft 0.42 does **not** require Forge to predict generated browser labels
such as `Board:1` or `Board:2`.

The native engine already provides the required identity:

```text
component.create
    -> result.occurrence

occurrence.copy
    -> result.occurrence

later move/joint/origin
    <- occurrence id
```

The remaining problem is execution/replay architecture: a later static command
cannot know a runtime id until the create/copy command has executed.

That is a Forge execution-plan problem, not a SolidCraft identity problem.

Historical PRs #166/#167 already implemented one possible solution using
Forge-owned logical references and result bindings. The foundational audit must
decide how to restore or redesign that mechanism while preserving the desired
replay semantics.

## Forbidden fallback

The following is not a valid identity mechanism:

```python
native_name = f"{component_name}:{index}"
```

Generated browser names may remain useful human-readable labels, but they are
not Forge occurrence identity and must not be used as the compiler's addressing
mechanism.
