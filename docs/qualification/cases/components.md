# Reuse one component definition in two placements

## Use scenario

A model has one reusable block definition and needs two physical occurrences.
The second block is placed directly beside the first.

## Forge API

```python
left = Block()
right = left.copy(
    placement=Placement(x=Block.length),
)
return left + right
```

## Expected behaviour

- one reusable `Block` definition;
- two occurrences;
- the second occurrence has an ordinary `Placement`;
- the blocks touch face-to-face;
- no attachment or joint is created.

## SolidCraft mapping

Forge creates the first occurrence with the component definition and creates the
second with:

```text
occurrence.copy(component="Block", translate=[40, 0, 0])
```

There is no `joint.create` and no later `occurrence.move`.

## Why this case exists

This case qualifies component-definition reuse and multiple occurrences. Joint
behaviour belongs in the separate attachment qualification cases.
