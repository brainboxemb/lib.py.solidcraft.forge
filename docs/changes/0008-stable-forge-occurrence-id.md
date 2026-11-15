# Change 0008 — Stable Forge occurrence id

Status: implementation

## Problem

Forge uses Python `id(instance)` in `compile_assembly()` to remember which
occurrence an attachment, custom anchor or copy belongs to.

That breaks when Forge replaces a `ModelInstance` object while it is still the
same physical occurrence.

A clear example is `.group()`:

1. `parent + child.attach(parent)` stores `parent` in the attachment;
2. `.group("Pair")` creates replacement `ModelInstance` objects;
3. the attachment still points at the earlier Python object;
4. `compile_assembly()` compares Python object ids and can no longer find the
   parent.

The same Python object can also currently be added twice to one assembly. The
compiler then creates two SolidCraft occurrences but stores only one
`id(instance)` lookup entry.

## Change

Each `ModelInstance` gets an internal Forge occurrence number.

Rules:

- creating a component instance gets a new number;
- `.copy()` gets a new number;
- `.group()` keeps the number;
- `.attach()` keeps the number;
- changing Placement through `replace()` keeps the number;
- the same occurrence number may appear only once in one `Assembly`.

`compile_assembly()` uses this Forge number instead of Python `id(instance)`
for:

- occurrence lookup;
- custom anchor lookup;
- copied-placement tracking;
- attachment parent/child lookup.

## What does not change

This change does not change SolidCraft occurrence names or commands.

In particular it does not yet remove code such as:

```python
native_name = f"{component_name}:{index}"
```

That is a separate replay-first repair.

This change only makes Forge's own occurrence tracking reliable before we change
how SolidCraft occurrences are addressed.

## Tests

The tests prove:

- `.copy()` gets a different Forge occurrence number;
- `.group()` keeps the same number;
- `.attach()` keeps the same child number and parent reference;
- adding the same occurrence twice is rejected;
- an attachment still compiles after grouping replaced the Python objects;
- existing generated SolidCraft commands remain unchanged.
