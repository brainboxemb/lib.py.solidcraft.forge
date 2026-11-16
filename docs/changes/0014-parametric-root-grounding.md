# Change 0014 — Keep parametric root Placement associative

Status: implementation  
SolidCraft target: **0.42.0**

## Problem

Change 0013 restored replayable occurrence ids and made parameter-driven
Placement work again without predicting browser names such as `Board:2`.

A native HUB75 regression exposed one remaining SolidCraft 0.42 limitation.

The first physical occurrence of the assembly was created with
`grounded=true`. Forge then placed it with:

```text
occurrence.move(
    occurrence=$panel,
    translate=[..., "opening_height ..."],
    move_grounded=true,
)
```

SolidCraft 0.42 evaluates that expression correctly for the initial build, but
a later `parameters.change(opening_height=...)` leaves the grounded occurrence
at its old position.

Copies of the same component are ungrounded and do follow the changed
parameter. The result is internally inconsistent: one occurrence stays behind
while the copies move.

## SolidCraft 0.42 behaviour

In SolidCraft 0.42, expression-based occurrence moves are stored so ungrounded
occurrences can follow parameter changes.

`move_grounded=true` permits a grounded occurrence to be moved initially, but
0.42 does not store an equivalent "this grounded move may keep following its
expression" flag.

Later SolidCraft code adds that capability, but Forge targets 0.42 and must not
assume it exists.

## Decision

Ground a physical root occurrence only when its Placement position is fixed.

A root occurrence stays **ungrounded** when any of its Placement X/Y/Z values
contains a Parameter or Expression.

Examples:

```python
# Fixed root: may be grounded.
part = Part(placement=Placement(x=30))

# Parametric root: must stay ungrounded on SolidCraft 0.42.
panel = Panel(
    placement=Placement(
        z=half(opening_height),
    ),
)
```

This does not change the public meaning of Placement.

It is a SolidCraft 0.42 backend compatibility rule that preserves the declared
parametric relationship.

## Lowering

For a fixed root:

```text
component.create(... grounded=true) -> $part
occurrence.move(
    occurrence=$part,
    translate=[30, 0, 0],
    move_grounded=true,
)
```

For a parameter-driven root:

```text
component.create(... grounded=false) -> $panel
occurrence.move(
    occurrence=$panel,
    translate=[0, 0, "opening_height / 2"],
)
```

No `move_grounded` flag is added to the second form.

## Qualification

The change must prove:

- a fixed root occurrence remains grounded;
- a root occurrence whose Placement position contains a Parameter/Expression
  is created with `grounded=false`;
- its later `occurrence.move` keeps the symbolic expression and does not use
  `move_grounded`;
- the HUB75 wood-frame native model still builds through replay variables;
- after changing `opening_height` in the saved SolidCraft design, **all five**
  HUB75 panel occurrences move to the new centred height;
- existing fixed-root grouping/grounding tests remain green.

## Scope

This change does not alter:

- the public `Placement` API;
- replay-variable syntax;
- numeric `occurrence.copy(..., translate=...)`;
- attachment semantics;
- grouping semantics.

It only changes the grounding choice for a parameter-driven physical root on
SolidCraft 0.42.
