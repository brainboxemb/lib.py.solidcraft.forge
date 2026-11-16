# Change 0010 — Remove guessed SolidCraft occurrence names from attachments

Status: design review and implementation  
SolidCraft target: **0.42.0**

## Problem

The old attachment compiler makes SolidCraft occurrence names itself:

```python
native_name = f"{component_name}:{index}"
```

For example, Forge may build `Block:2` and pass that string to
`joint.create`, `joint.origin`, `joint.as_built` or
`occurrence.move`.

Forge does not create or control SolidCraft's `:1`, `:2`, ... numbering.
If SolidCraft numbers the occurrences differently, Forge can address the wrong
part.

Change 0010 must remove that dependency. It must not replace it with another
method until we understand why that method is correct.

## What SolidCraft 0.42 actually supports

The native research branch is
`qualification/0010-joint-reference-probe`.

The tests show several different behaviours. They must not be treated as if
they were the same API.

### Component name

For these joint commands, SolidCraft accepts a component name for that
component's first occurrence:

- `joint.create`;
- `joint.origin`;
- `joint.as_built`.

For example, `"Block"` can address the first occurrence of component
`Block` in those commands.

This does **not** mean every command accepts the component name.
`occurrence.move(occurrence="Block", ...)` fails with:

```text
no occurrence Block
```

### Geometry pick

`joint.create` also supports a different form. A side can contain a world
point on geometry and omit `occurrence`.

Examples include:

```json
{"face": [80, 0, 5]}
```

and:

```json
{
  "point": [80, 0, 5],
  "z": [1, 0, 0],
  "x": [0, 0, 1]
}
```

SolidCraft's own 0.42 schema says that when `occurrence` is omitted it is
found from the supplied point. This is therefore a real `joint.create`
selection method, not something Forge invented.

The native tests show:

- a unique face pick can select a copied occurrence;
- a unique point/frame pick can select a copied occurrence;
- four copies at different positions can be selected independently;
- if two occurrences have selectable geometry at the same world point, the
  point alone is ambiguous and SolidCraft can select the wrong occurrence.

That last case is the important risk.

## Comparison with fillet

Forge already uses point-based native selection for operations such as
`solid.fillet`.

A Forge edge selection is converted to a point on the required edge. SolidCraft
uses that point to select the native edge. That is a normal CAD selection
mechanism.

A point used by `joint.create` may be equally valid. The question is not
"does it use a point?" The question is:

> Does the point describe the geometry the user intends to select, and does
> SolidCraft store a stable native joint reference after that selection?

Change 0010 must answer that before copied attachments are accepted or rejected.

## Temporary placement before creating a joint

One experiment moves a copied component a small distance away before
`joint.create` runs. Forge then gives SolidCraft a geometry point that belongs
only to that copy. After `joint.create`, the joint solver moves the component
to its required attached position.

Do not call this only a "staging offset". The actual behaviour is:

> Forge first places the copied component a small distance away so SolidCraft
> can select that copy by its geometry. Forge then creates the joint.

This may match normal interactive CAD use: a loose part is positioned where it
can be selected, the user selects geometry on both parts, and the joint then
places the part.

It may also be an unnecessary workaround. We need native evidence before making
that decision.

## Questions that must be answered

Before copied attachments are considered supported, test and document:

1. Does `joint.create` store the selected occurrence and topology in the
   saved model, or does it keep depending on the original world point?
2. Does the joint still refer to the same occurrence after save and reopen?
3. Does the selected face/edge remain attached after model parameter changes?
4. Does a copied part remain the selected part after other copies are added or
   reordered?
5. When a point is ambiguous, does SolidCraft report that clearly or silently
   choose one occurrence?
6. Is temporarily placing a loose component before creating the joint
   equivalent to the normal SolidCraft UI workflow?
7. Which cases need an explicit occurrence/path instead of a point pick?

## Current implementation state

The `Component:N` construction has been removed from the current 0010 branch.

While the questions above are being checked, copied occurrences are temporarily
rejected as attachment endpoints. That is a conservative implementation state,
not yet the final design decision.

First occurrences still use the component name only in the joint commands where
SolidCraft 0.42 has been tested to support it.

## Rules that are already final

Whatever decision is made about geometry picks:

- Forge must not generate `Component:1`, `Component:2`, ... to address an
  occurrence;
- one SolidCraft command accepting a component name does not prove another
  command accepts it;
- a geometry pick is acceptable only when it is the intended SolidCraft
  selection mechanism for that operation;
- ambiguity must be tested, not assumed away;
- unsupported cases must fail clearly instead of silently selecting another
  occurrence.

## Qualification

The final 0010 tests must at least prove:

- generated Forge commands contain no guessed `Component:N` occurrence
  selectors;
- first-occurrence component-name selection works in each command where Forge
  uses it;
- copied-occurrence selection, if kept, survives save/reopen;
- copied-occurrence selection, if kept, survives relevant parameter changes;
- ambiguous geometry-pick cases are either prevented or rejected clearly;
- rotated, chained and as-built cases are only enabled when their own SolidCraft
  reference method has been proved.
