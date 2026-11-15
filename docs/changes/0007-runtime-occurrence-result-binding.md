# Change 0007 — Runtime occurrence result binding

Status: implementation in progress  
SolidCraft target: 0.42.0

## Problem

Forge currently emits raw SolidCraft command JSON.

That works only while every later command can address its target without
needing a value created at runtime. Occurrence identity breaks that assumption.

SolidCraft 0.42 returns the real native occurrence id from:

- component.create;
- occurrence.copy.

Later operations such as occurrence.move and joint/origin commands accept that
native id.

Forge must therefore carry a value returned by an earlier native command into a
later command.

Predicting generated browser labels such as Component:1 or Component:2 is not
an acceptable substitute.

This change implements only the execution/result-binding infrastructure. It
does not yet change assembly lowering.

## Decision

A Forge execution document remains JSON and keeps the existing commands array.

When a later command depends on an earlier native result, the document adds a
bindings object and places an exact logical reference in the dependent command.

Example:

~~~json
{
  "commands": [
    {
      "command": "occurrence.copy",
      "params": {
        "component": "Block"
      }
    },
    {
      "command": "occurrence.move",
      "params": {
        "occurrence": {
          "$ref": "occurrence:right"
        },
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

The logical reference is Forge metadata. It is never sent to SolidCraft.

## Execution contract

### Static document

If a document contains no runtime references, execution stays exactly as it is
today:

~~~text
one engine.batch
rollback=true
param_check=strict
~~~

This preserves current raw replay behaviour.

### Identity-dependent document

If a document contains a runtime reference:

1. validate every binding before execution;
2. create one outer SolidCraft checkpoint;
3. execute commands in the largest possible phases;
4. capture requested typed result fields from each phase;
5. resolve logical references to the actual returned native values;
6. execute the next dependent phase;
7. after complete success, forget the temporary checkpoint;
8. after any later failure, restore the outer checkpoint.

A result-binding document therefore remains atomic even though SolidCraft must
be called in more than one phase.

## Validation rules

- a reference has exactly one field: $ref;
- every reference names an existing binding;
- a binding producer must appear before every consumer;
- a binding records exactly command index and result field;
- unused bindings are rejected;
- raw command documents remain valid without a bindings object.

## Public API impact

No CAD modelling API changes in this change.

This adds internal/execution helpers:

~~~python
result_ref(name)
validate_document(document)
send_document(document, ...)
~~~

The CLI replay path accepts either:

- an existing raw commands document; or
- a Forge result-binding execution document.

## SolidCraft command contract

Pinned SolidCraft 0.42 evidence is recorded in:

~~~text
docs/vendor/solidcraft/0.42.0/occurrence-identity.md
~~~

The relevant native contract is:

~~~text
component.create -> result.occurrence
occurrence.copy   -> result.occurrence

later:
occurrence.move(occurrence=<numeric id>)
joint/origin(... occurrence=<numeric id> ...)
~~~

## Qualification

### Q1 — Python execution-document tests

Verify:

- references remain plain JSON data;
- bindings must precede use;
- unknown/unused bindings fail;
- raw command documents still validate unchanged.

### Q2 — transport/executor tests

Verify with the fake control server:

- a returned native occurrence id is inserted into the later command;
- the document splits only at a dependency barrier;
- a later phase failure restores the outer checkpoint;
- replay resolves a fresh runtime id.

### Native follow-up

Before this infrastructure is used by assembly lowering, qualify the same
result-binding contract against pinned SolidCraft 0.42:

- create/copy;
- capture returned occurrence id;
- later move using that id;
- live/checkpoint behaviour where available.

The audit has already proven the equivalent two-phase headless 0.42 path.
Change 0007 makes that capability a normal Forge execution primitive.

## Non-goals

This change does not:

- add OccurrenceId to ModelInstance yet;
- modify compile_assembly;
- remove Component:N prediction yet;
- change Placement;
- change grouping;
- change AnchorFrame/joint semantics.

Those are later remediation phases built on this execution foundation.
