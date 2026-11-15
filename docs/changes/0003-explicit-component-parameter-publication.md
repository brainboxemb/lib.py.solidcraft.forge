# 0003 — Explicit publication of reusable component parameters

Status: **active correction for SCPF 0.3.2**  
SolidCraft target: **0.42.0**  
Related historical implementation: commit `746b52f3dcc0d65f023c846270abbc0f8fb6278c`  
Conflicting later change: commit `0669e12d6e01760d7f552b7ad466ad060b703251`

## 1. Why this change record exists

Reusable child-component parameter publication already had an explicit API
decision before the numbered change-management directory existed.

On 2026-11-12 commit `746b52f` introduced and tested:

> **publish component parameters only when included**

Its commit message states:

```text
api: publish component parameters only when included

* model: distinguish public parameters from fixed component inputs
* api: hide component defaults unless explicitly included
* test: make component parameter publication explicit
* test: exercise included parameters in component geometry
```

The public contract implemented there was:

```python
@component
class Bracket:
    width = 24.0
    radius = 4.0
    chamfer = 2.0
```

used normally:

```python
Bracket()
```

publishes **no component-local parameters**.

Selected publication is explicit:

```python
Bracket = component(
    BracketModel,
    include=("radius",),
)
```

and publishes only:

```text
Bracket_radius
```

`include="*"` explicitly publishes all public component defaults.

A parent Parameter or Expression passed into a child remains symbolic
regardless of `include=` and reuses the parent dependency.

## 2. What later changed

On 2026-11-13 commit `0669e12` changed the contract to:

```text
public lower_case component defaults become editable native parameters
```

and removed `include=` from the public API.

That change also rewrote qualification and guide text so the new implicit rule
became internally consistent:

```text
lower_case child default -> automatically editable namespaced parameter
```

For example a component with seven lower-case implementation dimensions began
publishing seven extra user parameters even when the parent assembly had not
asked to expose them.

The change was substantial API behaviour, but it did **not** receive a numbered
design/change record because `docs/changes/` did not yet exist.

This record resolves that history explicitly instead of treating whichever
implementation happens to be newest as the design source of truth.

## 3. Why this surfaced now

The HUB75 WoodFrame creates a reusable CornerBracket like this:

```python
bracket = CornerBracket(
    arm_width=self.bracket_width,
    inside_corner_radius=self.corner_radius,
)
```

The intended visible model parameters are the parent parameters:

```text
bracket_width
corner_radius
```

The remaining CornerBracket defaults are implementation dimensions of that
reusable component:

```text
horizontal_arm_length
vertical_arm_length
arm_height
outer_corner_chamfer
arm_end_chamfer
side_edge_chamfer
elephant_foot_relief
```

Under the implicit-publication rule these appeared in the top-level SolidCraft
parameter list as:

```text
CornerBracket_horizontal_arm_length
CornerBracket_vertical_arm_length
CornerBracket_arm_height
CornerBracket_outer_corner_chamfer
CornerBracket_arm_end_chamfer
CornerBracket_side_edge_chamfer
CornerBracket_elephant_foot_relief
```

That is parameter-list pollution. The assembly did not request those child
defaults as user-editable model parameters.

The geometry and AnchorFrame/attach behaviour are unrelated and must not be
changed to solve this problem.

## 4. Decision

Restore the original explicit reusable-component publication contract.

### Root model

Public lower-case numeric fields on the **root model** remain normal editable
model parameters:

```python
class WoodenHub75Box:
    opening_width = 844.0
    opening_height = 362.0
    corner_radius = 4.0
```

These are intentionally visible to the user.

### Reusable child component defaults

Public lower-case numeric defaults owned by a **reusable child component** are
fixed component inputs unless explicitly included.

```python
@component
class CornerBracket:
    horizontal_arm_length = 60.0
    arm_height = 12.0
    inside_corner_radius = 4.0
```

A normal `CornerBracket()` does not publish those defaults.

This does **not** make the fields private Python API. They remain ordinary
constructor inputs and can still define distinct reusable component
definitions.

### Parent Parameter / Expression binding

Passing a parent symbolic value into a child always preserves that dependency:

```python
bracket = CornerBracket(
    arm_width=self.bracket_width,
    inside_corner_radius=self.corner_radius,
)
```

Expected native parameter list contains:

```text
bracket_width
corner_radius
```

and does **not** contain:

```text
CornerBracket_arm_width
CornerBracket_inside_corner_radius
```

The child geometry still uses those values symbolically.

### Explicit child publication

A reusable component can deliberately expose selected own defaults:

```python
PublishedBracket = component(
    CornerBracketModel,
    include=("outer_corner_chamfer",),
)
```

This publishes:

```text
CornerBracket_outer_corner_chamfer
```

Use:

```python
component(CornerBracketModel, include="*")
```

only when all public component defaults are intentionally user-editable.

An explicit alias mapping remains valid where a child default itself should
become a chosen shared model parameter:

```python
component(
    CornerBracketModel,
    include={"inside_corner_radius": "corner_radius"},
)
```

An explicit parent Parameter/Expression passed at construction takes precedence
over such a component default publication and must reuse the passed dependency.

## 5. Naming rules are not publication rules

The following naming rules still have value:

```text
UPPER_CASE        fixed class constant
_private_lower    Forge/build-time input
lower_case        normal model/component input
```

But for reusable child components, `lower_case` by itself does **not** mean
"publish this in the top-level SolidCraft parameter list".

Publication scope and Python field naming are separate concerns.

This distinction is important because changing a reusable component field to
`_private` merely to hide it from a parent assembly would incorrectly change
its Python API semantics.

## 6. Required Forge behaviour

For:

```python
class Bracket:
    width = 24.0
    radius = 4.0
    chamfer = 2.0

    def build(self):
        ...
```

these contracts are required.

### Default reusable component

```python
BracketObject = component(Bracket)
BracketObject()
```

Native component-local parameters:

```text
[]
```

All three numeric values remain part of the reusable definition identity as
fixed inputs.

### Selected publication

```python
BracketObject = component(Bracket, include=("radius",))
```

Native component-local parameters:

```text
Bracket_radius
```

### Publish all

```python
BracketObject = component(Bracket, include="*")
```

Native component-local parameters:

```text
Bracket_width
Bracket_radius
Bracket_chamfer
```

### Parent dependency

```python
shared = Parameter("corner_radius", 5.0)
BracketObject = component(Bracket)
BracketObject(radius=shared)
```

Native parameters:

```text
corner_radius
```

There must be no `Bracket_radius` duplicate.

## 7. Qualification

The release gate must explicitly test all four cases above.

Additionally, add a CornerBracket-shaped integration fixture:

```python
class Display:
    bracket_width = 24.0
    corner_radius = 4.0

    def build(self):
        return Bracket(
            width=self.bracket_width,
            radius=self.corner_radius,
        )
```

Expected parameter names:

```text
bracket_width
corner_radius
```

No unused child defaults may appear.

Saved-design Q5 must prove that changing the parent `corner_radius` updates
the child fillet without rerunning Forge.

## 8. Source-of-truth and process failure

This issue exposed a documentation/process failure as well as an API
regression.

The original explicit-publication behaviour existed in code, tests and commit
history, but there was no numbered design record at the time. A later change
then rewrote implementation, qualification and API-guide text together to the
opposite implicit-publication rule.

Because all *current* artifacts agreed with one another, reading only the
latest implementation/tests/guide made the changed behaviour look normative.

During this work the assistant made that exact mistake:

1. it inspected the current implementation and current qualification;
2. it treated those as the design truth;
3. it proposed changing CornerBracket fields to private/build-only inputs;
4. only after the user pointed back to the earlier API agreement was the
   historical source commit inspected;
5. commit `746b52f` then showed that explicit publication was already a
   deliberate, tested API contract.

The correct workflow is therefore:

```text
docs/changes
    -> normative design history
    -> public API docs
    -> qualification
    -> implementation
```

not:

```text
current implementation
    -> infer API
```

If a current guide, test or implementation conflicts with a numbered change
record, the conflict must be resolved explicitly with a **new** numbered change
record. Existing design history must not be silently overwritten.

For pre-change-management decisions such as this one, the originating commit is
recorded here so future work does not need to rediscover the history.

## 9. Documentation correction

The current wording:

> If a reusable component owns a public lower-case numeric default itself, that
> default automatically becomes an editable, namespaced component parameter.

is superseded by this change.

The replacement wording is:

> Reusable component defaults stay fixed unless explicitly published with
> `include=`. Passing a parent Parameter or Expression into a child input
> always preserves and reuses that parent dependency.

The API Guide, Reference, Cheatsheet and agent API must be regenerated from
this restored contract.
