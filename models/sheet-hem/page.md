# Native sheet hem

**Group:** `sheet-metal`
**Saved-design required:** `true`

> Documentation provenance: Forge #785 promotes the released #773 hem fixture to public Verification.

## Goal

Prove that an existing sheet edge can fold back as one native hem while inheriting the active material rule.

## Forge API

`Sketch.sheet_metal(...)` creates the blank and `Shape.hem(edges=..., length=..., gap=...)` adds the native feature.

## Forge model

An 80 × 40 × 2 mm sheet receives a 12 mm hem with a 4 mm gap on its selected right edge.

## How Forge builds it in SolidCraft

Forge reuses the existing sheet rule and emits one native hem feature from a fixed edge pick. Length and gap remain feature dimensions.

## SolidCraft result

One native sheet body contains the hem and keeps a recoverable developed flat pattern.

## Saved-design test

Mutate hem length from 12 to 16 mm and gap from 4 to 5 mm, then verify the rebuilt feature and flat pattern.

## Geometry evidence

> Geometry-rationale provenance: Forge #785 / #773 public capability promotion.
**Bounds sufficient:** `false`

Bounds alone do not prove native hem identity, inherited material rule or the developed result.

## Reference notes

- **Native SolidCraft history** — Native hem and sheet-rule evidence is authoritative; external shape-only references are optional.
