# Foundational CAD model

Status: **normative design foundation**

This document defines the minimum CAD model Forge must support before another
public release is treated as a valid downstream baseline.

## 1. Three different concepts

Forge separates three concepts that must not be collapsed into one another.

### ModelDefinition

A model definition describes **what a reusable physical part is**.

Examples:

- Board dimensions;
- material;
- holes;
- fillets;
- local anchors.

A definition is shared by all occurrences of that part.

### Placement

A Placement describes **where and how one occurrence stands** in an assembly.

```python
left = Board(
    width=12,
    depth=100,
    height=362,
    placement=Placement(x=-428, y=0, z=12),
)

right = Board(
    width=12,
    depth=100,
    height=362,
    placement=Placement(x=428, y=0, z=12),
)
```

Placement is occurrence data. It is not a feature of the shared Board
definition and it is not an assembly relationship.

A Placement contains:

- absolute X/Y/Z position;
- optional absolute axis-angle orientation.

Position may be numeric or parameter/expression based. Rotation is a separate
capability and must only be considered qualified when its native lowering is
qualified.

### Attachment

An Attachment describes **a relationship between occurrences**.

Examples:

- this bracket is rigidly attached to this board corner;
- this panel face is mated to this frame face.

Attachments may lower to SolidCraft joints. Placement alone must not.

## 2. Public placement API

The primary explicit API is:

```python
Board(..., placement=Placement(x=100, y=0, z=20))
```

Convenience methods operate on Placement:

```python
part.at(x=100)       # absolute placement
part.move(x=20)      # relative placement change
part.rotate(Y, 90)   # absolute axis-angle orientation
```

These Python methods describe final model intent. They do **not** prescribe
same-named SolidCraft commands.

In particular:

> Python `move()` does not imply SolidCraft `occurrence.move`.

The compiler sees the final Placement and chooses the native representation
that best preserves it.

## 3. Foundational use cases

These use cases are release gates, not optional examples.

### U1 — one reusable component at origin

```python
Block()
```

Expected: one native component definition and one occurrence.

### U2 — one component with explicit absolute placement

```python
Block(placement=Placement(x=50))
```

Expected: the final occurrence is at X=50 without introducing a relationship.

**Implementation status:** Forge now compiles the root as a reusable occurrence,
binds the `component.create` result to a Forge logical occurrence handle, and
uses that runtime id for the later native placement operation. The compiler does
not predict `Block:1`.

This use case still requires dedicated native qualification before a new public
release is accepted as a downstream CAD baseline.

### U3 — one definition, two numeric occurrences

```python
left = Block(placement=Placement(x=-50))
right = left.copy().at(x=50)
return left + right
```

Expected:

- one shared definition;
- two occurrences;
- the second occurrence receives its numeric initial placement during native
  creation/copy where SolidCraft supports it;
- no placement joint;
- no required follow-up move of the second occurrence merely because Forge
  used `copy()`.

### U4 — relative convenience

```python
right = left.copy().move(x=100)
```

The final Placement is what matters. The compiler may fold the relative Python
operation into creation-time native placement.

### U5 — parameter-driven placement

```python
right = Block(placement=Placement(x=self.spacing))
```

The saved SolidCraft design must retain the parameter dependency and update
after `parameters.change` without rerunning Python.

This cannot be claimed from U3. It is a separate capability because
`occurrence.copy.translate` in SolidCraft 0.42 is numeric-only.

### U6 — rotation plus placement

Position and orientation must both survive save/reopen and parameter mutation
where applicable. Rotation is a separate qualification dimension.

### U7 — explicit attachment

```python
bracket = CornerBracket(...).attach(board, ...)
```

Expected: an explicit relationship/joint may appear.

### U8 — repeated parent definition with attached children

Two occurrences of one shared parent definition each receive their own
attached child. Saved-design parameter mutation must keep both graphs correct.

### U9 — replay

A model that requires a runtime-created occurrence id replays through the Forge
execution document. Logical `$ref` handles are rebound to fresh SolidCraft ids
during replay. A replay file must never freeze or guess a display label such as
`Board:2`.

## 4. Invariants

1. Placement and Attachment are separate concepts.
2. No hidden joint may be created only to implement Placement.
3. Generated SolidCraft display names are not Forge identity.
4. A public Python method does not dictate a same-named backend command.
5. A missing native capability is reported/design-reviewed, not silently
   replaced with another CAD concept.
6. Qualification must test the saved native design, not only generated JSON.
7. Release qualification must include U1-U9 as applicable to the release scope.

## 5. Current release status

SCPF v0.2.0 was published before this foundation existed and is **withdrawn as
a valid downstream CAD baseline**. Its code remains in Git history, but no CAD
repository should pin it as a qualified release.
