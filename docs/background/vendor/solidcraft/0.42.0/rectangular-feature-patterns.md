# SolidCraft 0.42.0 — rectangular feature pattern JSON contract

Pinned source: `tangency-labs/solidcraft` commit
`1b1e940cc48e4d1d5d01971a4be20e2e55647066`.

Relevant command:

```text
solid.pattern.rectangular
```

Feature-pattern fields:

- `features`: existing native history feature references;
- `dir1`: first direction vector;
- `count1`: count along direction 1, including the original;
- `spacing1`: spacing along direction 1;
- `dir2`, `count2`, `spacing2`: optional second direction;
- `alignment`, `alignment2`: native alignment policy;
- `reversed`, `reversed2`: independent direction reversal.

The command replays the referenced source feature. A cut source remains a cut
on the same target body.

Change 0026 is concerned with producing this JSON correctly from SCPF's feature
expression tree. It does not require the Python caller to know or repeat a
SolidCraft history label.
