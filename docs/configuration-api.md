# Configuration API design proposal

Status: proposed  
Tracking: #444

## Purpose

This document defines the intended public SCPF configuration authoring model
before implementation changes are made.

The main design goal is that configuration remains intent attached to the final
model or Assembly. It is not a wrapper type that consumer code must return, and
it is not intrinsic state owned by a reusable `@component` class.

The public authoring flow should read as:

```text
build model
configure model
return model
```

rather than:

```text
build model
wrap model in Configure(...)
return wrapper
```

Forge may still use an internal configured-design object or ConfigurationIR.
That representation is an implementation detail and must not leak into the
public API.

## Ownership

Configuration belongs to the final model/document that is being authored.

A reusable component owns:
- geometry;
- parameters;
- explicitly exported feature references;
- attachment/topology intent that belongs to the component itself.

A reusable component does **not** automatically own:
- a configuration table;
- an active configuration row;
- a document-level checkbox state;
- a parent Assembly's configuration policy.

The same component may therefore be used in several final models with different
configuration policies.

A standalone model may configure a reusable component after instantiation. A
parent Assembly may configure its complete result after composing reusable
children.

## Core API shape

Every final configurable design result exposes:

```python
design.configure(...)
return design
```

The method is valid on the same final result categories currently accepted by
`Configure(...)`:
- Shape;
- component occurrence / ModelInstance;
- Assembly.

Calling `.configure(...)` attaches configuration intent to that result and
returns the same public design object for optional fluent use. Consumer code is
free to ignore that return value.

Both forms are therefore valid:

```python
design.configure(...)
return design
```

and:

```python
return design.configure(...)
```

The first form is preferred in examples because it keeps model construction and
document configuration visibly separate.

## Parameter columns

Existing parameter configuration remains a first-class column:

```python
frame.configure(
    active="Medium",
    columns=(
        Param(self.width),
        Param(self.height),
    ),
    rows={
        "Small": (60, 40),
        "Medium": (80, 60),
        "Large": (100, 80),
    },
)

return frame
```

`Param(...)` continues to refer to an existing native/public Forge Parameter.
Rows store expressions, not evaluated snapshots.

A parent may drive one shared parameter that is passed into several reusable
child occurrences. The configuration still belongs to the parent final model;
the children merely consume the shared parameter.

## Feature suppression columns

Existing explicit feature suppression remains a column:

```python
coupler.configure(
    active="Small",
    columns=(
        Param(self.width),
        Suppress(panel_pin),
    ),
    rows={
        "Small": (60, True),
        "Medium": (80, True),
        "Large": (100, False),
    },
)

return coupler
```

Reusable-child feature references continue to use explicit Forge feature
identity such as `occurrence.feature("panel_pin")`. Configuration must never
expose backend feature ids.

## Boolean configuration controls

Forge should add a first-class boolean configuration control for states that are
naturally presented as a checkbox.

Proposed spelling:

```python
Toggle(
    "Installed",
    default=False,
    off=DriveParameter(
        self.clamp_bore,
        self.tube_d - self.clamp_interference,
    ),
    on=DriveParameter(
        self.clamp_bore,
        self.tube_d,
    ),
)
```

`Toggle` is semantic configuration intent. It is not a user-visible numeric
model parameter and must not be emulated publicly as 0/1.

A toggle has:
- a stable authored name;
- a boolean default;
- an optional effect for the off state;
- an optional effect for the on state.

The first proposed effect type is the already-known typed
`DriveParameter(...)`.

### Standalone clamp example

A standalone Tube Clamp should be authored as:

```python
class Hub75TubeClampModel:
    tube_d = 10.0
    clamp_interference = 0.4
    clamp_bore = 9.6

    def build(self):
        clamp = Hub75TubeClamp(
            tube_d=self.tube_d,
            clamp_interference=self.clamp_interference,
            clamp_bore=self.clamp_bore,
        )

        clamp.configure(
            Toggle(
                "Installed",
                default=False,
                off=DriveParameter(
                    self.clamp_bore,
                    self.tube_d - self.clamp_interference,
                ),
                on=DriveParameter(
                    self.clamp_bore,
                    self.tube_d,
                ),
            ),
        )

        return clamp
```

Expected UI intent when the standalone model is opened:

```text
Configuration

[ ] Installed
```

Default unchecked:
`clamp_bore = tube_d - clamp_interference`.

Checked:
`clamp_bore = tube_d`.

The public model does not need a visible `Free` row merely to represent the
unchecked state.

## Toggles inside named configuration rows

A parent configuration may store the value of the same kind of boolean control
per row.

Proposed authoring:

```python
frame.configure(
    active="Medium",
    columns=(
        Param(self.coupler_size),
        Toggle(
            "Installed",
            off=DriveParameter(
                self.clamp_bore,
                self.tube_d - self.clamp_interference,
            ),
            on=DriveParameter(
                self.clamp_bore,
                self.tube_d,
            ),
        ),
    ),
    rows={
        "Small":  (60, False),
        "Medium": (80, True),
        "Large":  (100, True),
    },
)

return frame
```

The semantic table is:

| Configuration | coupler_size | Installed |
| --- | ---: | :---: |
| Small | 60 | off |
| Medium | 80 | on |
| Large | 100 | on |

Switching rows changes the toggle value stored by that row. The toggle is
therefore not a global rule orthogonal to the table.

This is the key distinction from the current `ConfigRule(enabled=...)`
contract.

## Global rules versus row state

A global Configuration Rule and a row-owned boolean cell are different concepts
and must not share one public abstraction.

A global rule means:

```text
one enabled state
applies independently of whichever row is active
```

A row-owned toggle means:

```text
Small  -> Installed = false
Medium -> Installed = true
Large  -> Installed = true
```

Forge must not use a global rule as a substitute for row-owned state merely
because one backend exposes a rule checkbox.

If generic global rules remain useful for other consumers, they may stay as a
separate advanced API. They must not be prescribed as the normal way to model
Free/Installed child state.

## Parent and child configuration composition

The parent owns its final configuration.

If a child final model also has named configurations, future Forge API may expose
an explicit child-configuration selection column. Conceptually:

```python
frame.configure(
    active="Medium",
    columns=(
        ChildConfiguration(clamp),
    ),
    rows={
        "Small":  ("Free",),
        "Medium": ("Installed",),
        "Large":  ("Installed",),
    },
)
```

Exact spelling is intentionally not accepted yet. This capability requires a
real backend and IR contract before it becomes public API.

Do not emulate it with:
- a numeric 0/1 parameter;
- a fake suppression feature;
- Python branching per row;
- duplicated child bodies;
- a global rule that has different semantics.

Until child-configuration selection is qualified, a parent may explicitly own
and configure a shared published child parameter, because that is already a
real associative dependency.

## Reusable component example

The reusable clamp remains configuration-neutral:

```python
@component(include=("tube_d", "clamp_interference", "clamp_bore"))
class Hub75TubeClamp:
    tube_d = 10.0
    clamp_interference = 0.4
    clamp_bore = 9.6

    def build(self):
        ...
        return body
```

There is no `.configure(...)` call inside the reusable component class solely
because one particular catalog document wants an Installed checkbox.

The standalone catalog configures the resulting occurrence. A frame Assembly
may configure a shared parent parameter or, once supported, explicitly select a
child configuration.

## Method behavior

`design.configure(...)` may be called at most once for one final design
configuration owner.

A second call is rejected unless a future explicit extension API is introduced.
Forge must not silently merge unrelated tables or controls.

Configuration authoring is declarative. It must not immediately mutate geometry
by running Python branches for every row.

The active/default state affects the compiled initial document state, while all
other authored states remain editable native configuration state after save and
reopen.

## Proposed signatures

The exact Python implementation may refine type names, but the public contract
should remain approximately:

```python
design.configure(
    *controls,
    active=None,
    columns=(),
    rows=None,
)
```

Where:
- positional `controls` are standalone controls such as `Toggle(...)`;
- `columns` are row-table columns such as `Param(...)`, `Suppress(...)` and
  eventually `Toggle(...)`;
- `rows` is an ordered mapping of row name to cells;
- `active` is required when explicit named rows are authored;
- a standalone Toggle does not require the consumer to author a fake one-row
  table.

For consistency, a `Toggle` may be accepted either as a standalone control or
as a row-table column. Its meaning remains boolean configuration state in both
places.

## Backend-neutral compiler contract

Public configuration intent should normalize to engine-neutral semantic IR
before backend lowering.

The semantic model must distinguish at least:
- named configuration table;
- active row;
- parameter column;
- suppression column;
- boolean/toggle column or standalone control;
- row cells;
- typed effects such as driving a parameter;
- future child-configuration selection.

It must not contain:
- SolidCraft command names;
- SolidCraft row ids;
- Mitcad feature uids;
- replay variables;
- backend-private transport parameters.

Backends may use private transport constructs when necessary, but only when they
preserve the exact semantic behavior.

## SolidCraft 0.49 capability boundary

The retained SolidCraft 0.49 command registry currently exposes configuration
columns for:
- parameters;
- features/suppression;
- materials;
- appearances.

It does not expose a native per-row boolean/toggle column or a child
configuration-selection column in the retained command contract.

SolidCraft does expose Configuration Rules with a global `enabled` checkbox.
That checkbox is sufficient evidence for a standalone global rule, but it does
not prove row-owned Toggle semantics.

Therefore:

1. Forge must not claim per-row Toggle support on SolidCraft 0.49 until exact
   saved-design behavior is proven.
2. Forge must not silently lower a row Toggle to a global Configuration Rule.
3. If standalone Toggle can be lowered faithfully to a native rule checkbox,
   that backend slice may be implemented and qualified separately.
4. A Toggle used as a row column must fail explicitly on a backend that cannot
   preserve row-specific values.
5. A future SolidCraft version may remove this limitation; the semantic public
   API should not change merely because backend capability improves.

## Migration from current Configure(...)

The current public wrapper:

```python
return Configure(
    design,
    active="Medium",
    columns=(...),
    rows={...},
)
```

should be treated as compatibility API during migration.

Preferred new authoring:

```python
design.configure(
    active="Medium",
    columns=(...),
    rows={...},
)
return design
```

A compatibility period may implement `Configure(...)` by attaching the same
internal configuration intent and returning the design. New documentation and
new models should use `.configure(...)` after the method is released.

Removal or deprecation timing must be handled through the normal Forge release
policy; this proposal does not require an immediate breaking removal.

## Acceptance criteria for implementation

Before this proposal becomes normative public API, Forge-owned verification must
prove:

1. `.configure(...)` works on Shape, ModelInstance and Assembly final results.
2. Configuration is attached to the final design without changing reusable
   component ownership.
3. Parameter and suppression rows retain current saved-design behavior.
4. Existing `Configure(...)` models remain compatible during migration.
5. Standalone Toggle renders/stores one native checkbox state with the authored
   default and survives save/reopen.
6. Toggle effects update real native dependencies without rerunning Forge
   Python.
7. A backend may not claim row-owned Toggle support until two named rows with
   different boolean values survive save/reopen and row switching.
8. Multiple child occurrences sharing one parent Parameter continue to follow
   the parent configuration.
9. Unsupported child-configuration selection fails explicitly.
10. No public configuration semantic depends on backend ids or command spelling.

## Decision points still open

This proposal intentionally leaves only a small number of naming decisions open:

- `Toggle` versus another concise name such as `Bool`;
- whether `DriveParameter` remains the effect object used by both Rules and
  Toggles or receives a more general configuration-effect name;
- the eventual public spelling for child-configuration selection.

The following points are not open in this proposal:
- configuration belongs to the final model/document;
- reusable components do not implicitly own configuration tables;
- preferred public authoring is `design.configure(...); return design`;
- Installed is naturally a boolean checkbox;
- per-row Installed state is row-owned state, not a global rule;
- unsupported backend semantics fail explicitly rather than being approximated.
