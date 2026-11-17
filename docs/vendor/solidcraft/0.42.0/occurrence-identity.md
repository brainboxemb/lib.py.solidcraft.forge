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

## What this means for Forge

SolidCraft returns numeric occurrence ids at runtime, and Forge's normal
replay-first document now has an explicit result-binding mechanism for them.

A creation/copy command may bind its returned `occurrence` field:

```json
{
  "command": "occurrence.copy",
  "params": {
    "component": "Board",
    "translate": [100, 0, 0]
  },
  "bind": {
    "$board_occurrence_2": "occurrence"
  }
}
```

A later command can use the replay variable as the complete occurrence value:

```json
{
  "command": "occurrence.move",
  "params": {
    "occurrence": "$board_occurrence_2",
    "translate": ["width", 0, 0]
  }
}
```

Every replay resolves the variable from the ids returned by that execution.
The temporary native id is never written back into the replay document.

The resulting rules are:

- Forge must not guess generated names such as `Board:1` or `Board:2`;
- ordinary numeric copy Placement stays in `occurrence.copy.translate` when
  that is sufficient;
- symbolic/rotated Placement uses a later `occurrence.move` addressed by the
  replay-bound occurrence id;
- copied endpoints of a qualified `joint.create` use the same replay-bound
  occurrence ids;
- `joint.create` geometry selectors are world picks combined with the explicit
  occurrence id. A correct id with a stale local-coordinate pick is not a valid
  selection;
- a normal attached child may receive a replay-bound seed
  `occurrence.move` before the authored joint. That seed is creation state,
  not a second relationship, and its expressions remain associative;
- unsupported command/reference combinations fail explicitly instead of
  falling back to a generated display name or point-only occurrence guess.

Change 0013 documents the replay-variable format and execution rules. Change
0029 adds the copied-parent/floating-graph attachment qualification.

## Background experiment: two-phase execution

This experiment is kept only as SolidCraft behaviour evidence. It is **not**
the normal Forge execution model.

A pinned SolidCraft 0.42.0 qualification run showed that a runtime occurrence id
can be used in a later CLI phase.

Audit run: `43759461853`.

Phase 1 used the normal Forge `components` fixture up to creation/copy and ran:

```text
solidcraft-cli run phase1.json
  --results
  --json-out phase1-results.json
  --save phase1.sc
```

The typed results included:

```json
[
  {
    "component": 1,
    "name": "Block",
    "occurrence": 2,
    "parent": 0,
    "grounded": true
  },
  ...,
  {
    "component": 1,
    "occurrence": 4
  }
]
```

Occurrence `4` is the actual runtime id returned by `occurrence.copy`.

Phase 2 generated an `occurrence.move` command using numeric id `4` and ran
it against the saved phase-1 design:

```text
solidcraft-cli run phase2.json
  --in phase1.sc
  --results
  --save phase2.sc
```

SolidCraft returned:

```json
{
  "occurrence": 4,
  "pending": false,
  "transform": [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [40, 0, 17, 1]
  ]
}
```

The copy retained its phase-1 X placement of 40 mm and accepted the phase-2
Z move of 17 mm through the returned occurrence id.

### Note

This proves a SolidCraft runtime behaviour only. It must not be used to justify
adding runtime result binding to the normal replay-first Forge compiler.
