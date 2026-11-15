# Occurrence placement and attachment design

> **Design decision.** This note records the native-lowering contract behind
> reusable occurrence placement and assembly attachment in Forge. The normative
> public API remains defined in `05-cad-api-design.md`.

## Problem

Forge exposes two different modelling intents:

- `.move(...)` places an occurrence;
- `.attach(...)` creates an assembly relationship between occurrences.

Those intents must stay distinct in the generated SolidCraft design. A placement
must not appear in SolidCraft's **Connections** browser as a fabricated joint.

Older Forge code used planar `joint.create` records named `Place ...` to keep
symbolic occurrence placement associative. That workaround was originally
needed for SolidCraft 0.30.1.

## SolidCraft 0.42 native capability

SolidCraft 0.42 accepts length expressions directly in
`occurrence.move.translate`.

Example:

```json
{"command":"parameters.add","params":{
  "name":"offset","expression":"40 mm"
}}
{"command":"occurrence.move","params":{
  "occurrence":"Block:2",
  "translate":["offset",0,0]
}}
```

SolidCraft stores the symbolic translation as an expressed occurrence move and
re-evaluates it when the referenced parameter changes. Therefore ordinary
parametric placement no longer needs a hidden placement joint.

## Public semantic contract

The Forge contract is:

```text
move(...)   = placement
attach(...) = relationship
```

Consequences:

1. `.move(...)` lowers to native `occurrence.move`.
2. Symbolic move coordinates remain native expressions.
3. `.move(...)` alone must not emit `joint.create`.
4. `.attach(...)` emits the explicit native joint that represents the authored
   relationship.
5. SolidCraft's Connections browser should therefore show authored assembly
   relationships, not Forge implementation machinery.

## SolidCraft 0.42 joint-solver boundary

A second constraint appears when an attached occurrence belongs to a rigid-joint
graph that does not reach grounded structure.

SolidCraft 0.42 distinguishes two concepts:

- an expressed `occurrence.move` is associative placement;
- a grounded occurrence is a fixed node for the joint solver.

An expressed move does **not** by itself ground a joint graph.

Grounding the occurrence is also not a valid replacement: SolidCraft deliberately
keeps a grounded occurrence fixed when the parameters behind an expressed move
change. Grounding would therefore destroy the placement associativity Forge is
trying to preserve.

This matters for assemblies with more than one disconnected attachment graph.
The HUB75 wood-frame model exposed the case directly: the left and right side
boards each own corner-bracket attachments, but the two side graphs are
independent. After removing hidden `Place ...` joints, the second graph could
retain an old child seed pose after a height change.

## Decision: preserve symbolic attachment seed placement

Forge already computes an attached child's initial placement from the selected
parent anchor and the parent's symbolic dimensions.

For reusable components, local model parameters are namespaced in the native
design. Symbolic anchor coordinates must therefore be rewritten at the same
semantic boundary: for example the Python component field `height` on
`Post` becomes native `Post_height` before the seed move is emitted. Forge
must not preserve an unnamespaced local expression that SolidCraft cannot
resolve.

That seed placement is not a second relationship. It is the initial/native pose
of the child occurrence.

Forge therefore keeps parameter-dependent seed coordinates symbolic when it
emits the child's `occurrence.move`, even if the child also has an explicit
attachment.

Conceptually:

```python
post = Post(height=self.height)
marker = Marker().attach(
    post,
    parent=Anchor.TOP,
    child=Anchor.BOTTOM,
)
```

lowers to the equivalent native intent:

```text
parameters.add(height)
occurrence.move(marker, z=<expression derived from height>)
joint.create("Attach Marker ...", rigid)
```

There is still only one relationship: the explicit attachment.

The expressed child move exists so the saved design retains the authored
parameter-dependent pose even if that particular joint graph is floating in
SolidCraft's solver.

## What Forge must not do

Forge must not solve this by:

- reintroducing hidden `Place ...` joints;
- silently grounding every parametrically placed occurrence;
- converting symbolic seed coordinates to numeric values before native
  lowering;
- treating `.move()` and `.attach()` as interchangeable API operations.

Those alternatives either leak implementation details into Connections or
break saved-design associativity.

## Qualification contract

The minimal native qualification is
`parametric-attachment-seed`.

It contains:

- two occurrences of one reusable `Post` definition;
- one `Marker` attached to the top of each Post;
- two disconnected rigid attachment graphs;
- one shared editable `height` parameter.

Initial state:

```text
Post_height = 100 mm
2 Post bodies
2 Marker bodies
2 Attach Marker... joints
0 Place ... joints
```

Saved-design mutation:

```text
parameters.change(Post_height = 140 mm)
```

Pass criteria:

- both Posts rebuild to 140 mm;
- both Markers move from Z=100..110 to Z=140..150;
- the Marker in the second floating graph follows as well;
- `joint.inspect` still reports exactly two authored attachment joints;
- no generated placement joint appears.

This case is intentionally small. It proves the native CAD semantics without
depending on the HUB75 model.

## Version scope

This decision is qualified against SolidCraft **0.42.0**.

If a later SolidCraft release changes the joint-solver model so that expressed
placement can directly act as an anchored/fixed solver reference while remaining
parameter-driven, Forge may simplify its lowering. Such a change must first be
proved by native qualification and then reflected in this design note.
