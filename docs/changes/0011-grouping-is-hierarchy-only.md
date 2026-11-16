# Change 0011 — group() changes hierarchy only

Status: design and native qualification  
SolidCraft target: **0.42.0**

## Problem

Forge currently creates every named group as a SolidCraft component with:

```json
{"command": "component.create", "params": {
  "name": "PanelGroup",
  "activate": false,
  "grounded": true
}}
```

That means `.group("PanelGroup")` changes the mechanical model. The empty
browser container becomes a grounded occurrence.

That is not what the Forge API says. `group()` is for browser hierarchy. It
must not decide which physical part is fixed.

There is a second SolidCraft detail that matters: if `grounded` is omitted,
`component.create` grounds the first part in a new design by default.
Therefore Forge must explicitly create a group with `grounded=false`. Merely
removing the current `grounded=true` argument is not enough.

## SolidCraft 0.42 behaviour

The pinned 0.42 source says:

- `component.create` defaults `grounded` to true for the design's first part
  and false for later parts;
- the joint solver starts from the design root and grounded occurrences;
- if a joint chain contains no grounded occurrence, the solver uses the A side
  of the first joint as that chain's fixed starting point;
- a nested occurrence that no joint moves stays where its parent places it.

These are SolidCraft rules. Forge must not turn the first rule into a hidden
meaning of `group()`.

## Forge rule

`group(name)` changes only native hierarchy.

A group component is always created with:

```text
grounded = false
```

Grounding is decided from the physical Forge assembly, separately from
`group_name`.

The existing Forge root rule is kept for this change:

> If the first physical Forge occurrence is not attached to another occurrence,
> that physical occurrence is the fixed root occurrence.

Grouping that occurrence must not change this decision. The group stays
ungrounded; the physical occurrence keeps the same grounded state it would
have without the group.

This change does not add a public grounding API.

## Native test before compiler change

Before changing `compile_assembly()`, prove this SolidCraft 0.42 case:

1. Create two physical parts at the root. Ground the first and join the second
   to it.
2. Create the same two parts under an empty group.
3. In the grouped version, set the empty group to `grounded=false` and the
   same first physical part to `grounded=true`.
4. Compare the solved body positions and joint references.
5. Confirm with `component.list` that the group itself is not grounded.

Also test a grouped physical part joined to a physical part outside the group.

If those cases differ mechanically, do not patch them by grounding the group.
Find the SolidCraft cause first.

## Reusable definitions under different groups

Forge currently rejects this:

```python
part = Panel()
assembly = part.group("A") + part.copy().group("B")
```

because one SolidCraft component definition is currently created under exactly
one native parent.

Do not remove that check as part of the grounding fix.

First determine whether SolidCraft 0.42 has a replay-first way to place
occurrences of one reusable definition under different parent components.
A runtime occurrence id returned by a previous command is not available to the
normal static Forge document.

If SolidCraft cannot express this safely, keep the restriction and document it
plainly. Do not duplicate geometry or use guessed occurrence names only to make
the example compile.

## Tests required for this change

Python command tests:

- every group `component.create` contains `grounded=false`;
- grouping the first physical occurrence does not remove its own
  `grounded=true`;
- grouping a non-root occurrence does not make it grounded;
- `Assembly.group()` still remaps attachment targets and assembly-owned anchor
  targets by Forge `occurrence_id`;
- no test describes grouping as mechanical fixing.

Native SolidCraft tests:

- grouped and ungrouped versions of the same two-part attachment solve to the
  same body bounds;
- an externally attached grouped child keeps the same solved position;
- independent grouped parts keep their declared Placement;
- saved parameter changes keep the same relationships.

## Exit condition

Adding or removing `.group(...)` may change the SolidCraft browser tree. It
must not change which physical occurrence is grounded, where a joint places a
part, or the resulting body geometry.
