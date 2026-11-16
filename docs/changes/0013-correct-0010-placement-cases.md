# Change 0013 — Correct the change 0010 qualification cases

Status: implementation  
SolidCraft target: **0.42.0**

## Problem

Change 0010 correctly removed guessed SolidCraft occurrence names such as
`Block:2` from attachment commands.

It also marked four qualification cases as blocked because their fixtures used
`attach()` on copied occurrences:

- `components`;
- `four-corner-l`;
- `eight-corner-brackets`;
- `eight-flightcase-corners`.

That classification was too broad. Those fixtures were treated as attachment
models even where their actual job was ordinary occurrence placement.

## Rule

Start from what the model means.

Use `Placement` when the assembly can calculate an occurrence position and
orientation directly.

Use `attach()` only when the model needs an actual relationship between two
occurrences.

Do not add a joint merely because a Placement backend path is missing.

## Corrected cases

### components

This case only qualifies one reusable definition with two occurrences.

The second block is therefore:

```python
right = left.copy(
    placement=Placement(x=Block.length),
)
```

The current SolidCraft 0.42 backend can write this directly as
`occurrence.copy(..., translate=[40,0,0])`.

The case is no longer blocked.

### four-corner-l

The frame dimensions directly determine X, Y and Z. The quarter-turn around Z
is also part of the occurrence pose.

The four profiles therefore use `Placement`, not `attach()`.

### eight-corner-brackets

The frame dimensions directly determine all eight X/Y/Z positions and the
corner clocking. These are ordinary `Placement` values.

### eight-flightcase-corners

The case dimensions directly determine the eight positions. Each protector has
one explicit axis-angle orientation. These are ordinary `Placement` values.

## Remaining backend limit

The last three cases remain blocked, but for a different reason.

Change 0009 deliberately limits replay-first Placement because SolidCraft 0.42:

- creates the first component occurrence at identity;
- accepts only numeric `occurrence.copy.translate`;
- has no rotation input on `occurrence.copy`;
- requires an existing occurrence selector for a later `occurrence.move`.

Forge still does not guess generated names such as `Component:2`.

Therefore the current backend cannot yet write these parameter-driven,
rotated Placements safely into one static replay document.

This is a Placement backend gap. It is not an attachment limitation.

## What stays valid from change 0010

Change 0010's attachment rule remains valid:

- no guessed generated occurrence names;
- no point-only copied-occurrence lookup;
- no temporary move just to make a copied occurrence selectable;
- copied attachment endpoints remain unsupported until SolidCraft provides a
  replay-safe reference that Forge can write into the static command document.

## Qualification

This change must prove:

- `components` compiles with one shared Block definition and one
  `occurrence.copy(..., translate=[40,0,0])`;
- `components` contains no `joint.create` and no `occurrence.move`;
- the three corner models contain no `attach()`;
- the three corner cases fail on the current Placement backend, not on copied
  attachment addressing;
- exactly those three cases remain `BLOCKED`;
- supported cases still contain no predicted SolidCraft `Component:N`
  occurrence selector.
