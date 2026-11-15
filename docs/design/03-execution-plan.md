# Forge execution plan and runtime bindings

Status: **normative executor design**

This document defines how Forge carries SolidCraft-owned runtime identity across
commands without predicting occurrence display names.

## 1. Why a raw command list is insufficient

Some SolidCraft commands create identity that later commands need.

Example:

1. occurrence.copy creates a new occurrence;
2. SolidCraft returns its numeric occurrence id;
3. a later occurrence.move or joint.create must target that exact occurrence.

A static raw batch cannot safely replace the returned id with a guessed label
such as Board:2.

## 2. Forge execution document

Forge keeps the native command list, plus optional result bindings.

Example:

~~~json
{
  "commands": [
    {
      "command": "occurrence.copy",
      "params": {"component": "Board", "translate": [40, 0, 0]}
    },
    {
      "command": "occurrence.move",
      "params": {
        "occurrence": {"$ref": "occurrence:right"},
        "translate": [0, 0, 20]
      }
    }
  ],
  "bindings": {
    "occurrence:right": {
      "command": 0,
      "field": "occurrence"
    }
  }
}
~~~

The logical binding name is Forge-owned. It is not a SolidCraft component or
occurrence name.

The reference object is deliberately explicit and serializable:

~~~json
{"$ref": "occurrence:right"}
~~~

It may appear recursively in command parameters.

## 3. Execution phases

SolidCraft 0.42 engine.batch returns one result for every completed command, but
does not provide verified substitution of a result into a later step of that
same batch.

Forge therefore creates dependency barriers.

For the example above:

~~~text
checkpoint
batch A
  occurrence.copy(...)
result A
  occurrence:right = result[0].occurrence = 42

batch B
  occurrence.move(occurrence=42, ...)

forget checkpoint
~~~

Commands without unresolved references stay together in the largest possible
batch. Forge does not split every native command into a separate network call.

## 4. Transaction boundary

One SolidCraft engine.batch rolls itself back on failure. Multiple phases need a
larger transaction boundary.

Before the first phase Forge executes:

~~~text
edit.checkpoint
~~~

If any later phase or binding extraction fails:

~~~text
edit.restore_checkpoint(checkpoint)
~~~

On complete success Forge removes the temporary checkpoint without restoring:

~~~text
edit.restore_checkpoint(checkpoint, forget=true)
~~~

Therefore phased identity resolution must not weaken the previous atomic model
execution guarantee.

## 5. Replay

Replay uses the same Forge execution document and the same logical bindings.
It must not freeze runtime ids from an earlier SolidCraft design into the file.

A replay document therefore records:

- native commands;
- logical result bindings;
- logical references.

At replay time the ids are obtained again from the new SolidCraft execution.

## 6. Validation invariants

An execution document is invalid when:

- a reference names no binding;
- a binding points outside the command list;
- a command refers to a result produced by itself or by a later command;
- a binding expects a result field that SolidCraft did not return;
- a reference object mixes $ref with unrelated keys.

These errors are Forge plan errors and must be reported before or during
execution. They are not converted into name guesses.

## 7. Raw command compatibility

A document without runtime references remains a normal single SolidCraft
engine.batch. Existing raw command/replay workflows therefore keep the current
path until the compiler actually needs result binding.

## 8. Compiler integration

The assembly compiler now:

1. assigns Forge logical handles `occurrence:0`, `occurrence:1`, ... in
   authored assembly order;
2. binds `component.create` / `occurrence.copy` result fields to those
   handles;
3. emits `$ref` values for later move, custom-origin and attachment selectors;
4. retains generated labels only for Forge-authored human-readable names such
   as joint labels, never as occurrence selectors;
5. emits only bindings that are actually referenced.

Live, replay and headless qualification all resolve the same document format.

This closes the compiler identity mechanism, but not the entire release gate.
Native foundational qualification must still prove create/place/copy/rotate,
parameter mutation, attachments, repeated-parent graphs and replay behavior
against the pinned SolidCraft version.
