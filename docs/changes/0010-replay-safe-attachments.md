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

`joint.create` can also find an occurrence from a world point when
`occurrence` is omitted. The engine chooses the placement whose body bounds
are nearest that point. If two placements are equally near, the earlier
occurrence path wins.

That is real SolidCraft behaviour, but it is **not how the normal SolidCraft UI
identifies a picked body for a joint**.

When the user clicks a face, edge or vertex in the Joint dialog, the UI sends:

- the geometry pick;
- the native occurrence id;
- and, when needed, the occurrence path for a repeated subassembly.

The point says where on the part the joint origin is. The occurrence id says
which placed part was picked.

This matters for Forge. Two mating faces can occupy the same world position in
a perfectly normal assembly. A point alone can then refer to either part.
Forge must not let SolidCraft silently choose the earlier occurrence.

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

## Moving a copy only to make selection possible

The research probe that moves a copied component away before
`joint.create` is not a valid Forge implementation.

It only makes point-only occurrence lookup unambiguous. The SolidCraft UI does
not need that trick because it already knows which occurrence the user clicked
and sends the occurrence id with the geometry pick.

Forge will not move a component only to make an otherwise ambiguous point pick
work.

## What is now established

The source and native probes establish enough for change 0010:

1. SolidCraft stores the resolved native occurrence in the joint origin.
2. Face and edge picks are converted to local component data and named topology
   where possible, so the joint can follow later geometry changes.
3. Save/reopen preserves the resolved joint reference.
4. The normal SolidCraft UI sends occurrence/path together with a body pick.
5. Point-only occurrence lookup can be ambiguous and silently chooses the
   earlier occurrence path.
6. Forge cannot know the native id/path of a later copy in a static replayable
   command document without adding a different runtime-result mechanism.

## Current implementation state

The `Component:N` construction has been removed from the current 0010 branch.

A copied occurrence is rejected as an attachment endpoint in SolidCraft 0.42
replay-first output. Forge cannot provide the explicit native occurrence/path
reference that the normal SolidCraft joint workflow uses for that copy.

This is deliberate capability removal, not a replacement workaround.

First occurrences still use the component name only in the joint commands where
SolidCraft 0.42 has been tested to support it.

The following qualification cases stay in the catalog but are marked
`BLOCKED`:

- `components`;
- `four-corner-l`;
- `eight-corner-brackets`;
- `eight-flightcase-corners`;

These cases are not removed and are not counted as PASS. They document the
reusable-copy attachment capability that Forge cannot currently generate safely
for SolidCraft 0.42. Qualification cases whose real purpose is another feature
must not be blocked merely because their fixture happened to reuse a child
definition; `xz-anchor` was changed to use separate marker definitions for
that reason.

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
- copied occurrences used as attachment endpoints are rejected before command
  generation;
- point-only copy selection is not used in generated Forge attachment commands;
- rotated, chained and as-built cases are only enabled when their own SolidCraft
  reference method has been proved.
