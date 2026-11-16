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

SolidCraft 0.42 `occurrence.copy` has a `parent` parameter. It accepts a
component id or component name.

The native probe proved both of these static command sequences:

```text
Panel first occurrence -> GroupA
occurrence.copy(component="Panel", parent="GroupB")
```

and:

```text
Panel first occurrence -> GroupA
occurrence.copy(component="Panel", parent="root")
```

SolidCraft keeps one `Panel` component definition and creates the second
occurrence under the requested parent. Forge therefore does not need a runtime
occurrence id, duplicated geometry or a generated `Panel:2` name for this
case.

Forge may remove the old "one reusable definition cannot currently be placed
under multiple assembly parents" restriction for ordinary copies.

## Native evidence

Research branch: `qualification/0011-grouping-probe`.

Native SolidCraft 0.42 run `43790998050` passed these checks:

- an ungrouped two-part rigid attachment;
- the same two parts inside an ungrounded group;
- a grounded grouped part attached to a root-level part;
- one `Panel` definition with occurrences under `GroupA` and `GroupB`;
- one `Panel` definition copied from `GroupA` back to `root`;
- one `Panel` definition copied from `root` into `GroupB`.

The grouped attachment variants produced the same solved body bounds as the
ungrouped baseline. `component.list` showed the group occurrences as
`grounded=false` and the physical fixed part as `grounded=true`.

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
