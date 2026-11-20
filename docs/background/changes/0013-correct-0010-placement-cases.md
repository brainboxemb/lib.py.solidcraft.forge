# Change 0013 — Replayable occurrence ids

Status: implementation  
SolidCraft target: **0.42.0**

## Problem

Forge must not predict SolidCraft-generated occurrence names such as
`Board:2`.

Change 0009 removed that unsafe addressing. The immediate result was also a
loss of useful Placement behaviour: symbolic positions, rotated copies and a
definition whose first occurrence was not at identity could no longer be
written as a replayable command file.

Change 0010 exposed the same problem for a copied occurrence used by an
attachment.

The public model was not the problem. A copy still means:

```python
right = left.copy(
    placement=Placement(
        x=100,
        rotation=(Z, 90),
    ),
)
```

The missing piece was a replayable way to refer to the real occurrence id that
SolidCraft returns when the occurrence is created.

## SolidCraft behaviour

SolidCraft 0.42 returns an occurrence id from both:

- `component.create`;
- `occurrence.copy`.

`occurrence.copy` accepts a numeric `translate`, but it does not accept
`axis` and `angle`. Rotation therefore needs a later `occurrence.move`.

The later command must use the actual returned id. It must not guess a browser
name.

## Replay variables

Forge replay documents may bind a returned field to a named variable:

```json
{
  "command": "occurrence.copy",
  "params": {
    "component": "Board",
    "translate": [100, 0, 0]
  },
  "bind": {
    "$board_2": "occurrence"
  }
}
```

A later command can use that variable:

```json
{
  "command": "occurrence.move",
  "params": {
    "occurrence": "$board_2",
    "axis": [0, 0, 1],
    "angle": "90 deg"
  }
}
```

During every replay Forge executes the first command, reads the returned
`occurrence` field, binds `$board_2` to that value and resolves the later
command.

The temporary SolidCraft id is never written back into the replay file.

The replay mechanism itself is not typed as "id only": a binding stores the
value of a returned SolidCraft result field and a later command receives that
value during the same replay. Change 0013 introduced this with occurrence ids
because Placement needed them. Other SolidCraft-returned execution values may
use the same mechanism when a later native command requires them. Replay
variables remain execution plumbing; they are not public modelling objects.

## Replay file

A replay file is explicitly identified as Forge replay data:

```json
{
  "format": "scpf-replay",
  "version": 1,
  "commands": []
}
```

A variable:

- starts with `$`;
- is bound exactly once;
- may only be used after its binding command;
- is replaced only when the complete JSON string is that variable name.

Forge does not perform text substitution inside CAD expressions.

## Replay log

One concrete execution can write a separate `scpf-replay-log` file.

The log contains:

- a SHA-256 hash of the replay document;
- the concrete value of every replay variable for that run;
- each command's resolved parameters;
- the bindings produced by each command.

The log is diagnostic output. It is never input for another replay.

## Native execution

The live GUI connection and the headless SolidCraft runner use the same replay
rules.

Commands are kept in one native batch until a later command needs a variable
that is produced by that batch. Forge then starts the next batch with the real
resolved id.

For a live GUI run Forge takes a SolidCraft checkpoint before a multi-phase
replay. If a later phase fails, the complete replay is restored to that
checkpoint.

For headless qualification, phases are saved to temporary `.sc` files. The
next phase opens the previous file, whose occurrence ids are part of the saved
design. Only the final successful phase is written to the requested output
path.

## Placement lowering

Use the simplest SolidCraft operation that preserves the declared Placement.

### Numeric unrotated copy

```python
right = left.copy(placement=Placement(x=100))
```

lowers directly to:

```text
occurrence.copy(component="Board", translate=[100, 0, 0])
```

There is no later move.

### Rotated or symbolic copy

The copy is created and its occurrence id is bound. A later
`occurrence.move` uses that bound id for the part of Placement that
`occurrence.copy` cannot express safely.

### First occurrence

`component.create` also binds its returned occurrence id. A non-identity
first occurrence can therefore be placed without predicting `Component:1`.

## Attachments

Attachments continue to mean an actual assembly relationship. Placement is not
converted into a joint.

When an attachment endpoint is a copied occurrence, its real runtime id comes
from the same replay-variable mechanism. There is no separate copied-attachment
addressing workaround.

## Qualification

Change 0013 must prove that:

- normal numeric copy translation stays in `occurrence.copy`;
- symbolic and rotated Placement use a bound occurrence id;
- no generated `Component:N` selector is predicted;
- replay variables are deterministic;
- use-before-bind is rejected;
- live execution resolves variables and rolls back the complete replay on a
  later failure;
- headless qualification uses the same replay file semantics;
- copied attachment endpoints use bound ids;
- the four corner/component fixtures contain no artificial Placement joints;
- saved-design parameter changes continue to move the placed occurrences.
