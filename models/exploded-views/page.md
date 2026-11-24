# Native exploded assembly views

**Group:** `components`
**Saved-design required:** `true`

> Documentation provenance: Forge #751 publishes native SolidCraft exploded assembly presentation as public Verification.

## Goal

Verify that Forge can store persistent native exploded presentations for a reusable component assembly without changing the occurrences' normal design placements.

## Forge API

```python
assembly = first + second + third
assembly = assembly.with_exploded_view("Automatic", scale=1.25)
assembly = assembly.with_exploded_view(
    "Instructions",
    moves=[
        (second, (0, 25, 0)),
        (third, (0, 50, 10)),
    ],
)
assembly = assembly.show_assembled()
```

## Forge model

Three occurrences of one reusable `ExplodeBlock` component are placed at X=0, 40 and 80 mm. The completed Assembly owns two presentation views: one automatic scale-based view and one explicit instruction view.

## How Forge builds it in SolidCraft

Forge creates the reusable component and all three normal occurrence placements first. It then emits two native `explode.create` commands. Explicit moves reference the actual replay-bound occurrence ids derived from the Forge occurrence objects. Finally `explode.show(view=None)` selects assembled presentation. No exploded translation is lowered as `occurrence.move`.

## SolidCraft result

The saved SolidCraft design retains three normally placed component occurrences plus two persistent exploded views. Showing either view changes presentation only; the authored occurrence placements remain unchanged.

## Saved-design test

Without rerunning Forge Python, reopen the saved design and show the stored `Automatic` view. Separately show the `Instructions` view and then return to assembled presentation with `explode.show(view=None)`. Both operations must succeed while model verification continues to see the original occurrence envelopes.

## Geometry evidence

> Geometry-rationale provenance: Forge #751 native exploded-view qualification.

**Bounds sufficient:** `false`

The three assembled body envelopes prove that normal occurrence placement is retained, but bounds alone cannot prove persistence of named presentation views. Saved-design replay of `explode.show` is therefore required evidence.

## Reference notes

- **Native SolidCraft presentation** — `explode.create` and `explode.show` own persistent exploded-view state independently of occurrence placement.
- **Forge occurrence identity** — Explicit exploded moves use Forge occurrence objects and are resolved to replay-bound native occurrence ids during assembly lowering.
