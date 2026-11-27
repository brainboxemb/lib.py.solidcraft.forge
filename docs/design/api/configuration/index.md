# Configuration API design

Status: proposed  
Tracking: #444

This directory owns the design proposal for the public Forge configuration API.
The SolidCraft-specific backend contract is documented separately in
[SolidCraft configuration model](solidcraft.md).

## 1. Core constraint: one configuration per final design

A final SolidCraft design exposes **one configuration definition**. Forge must
therefore model configuration as one design-owned concept as well.

That one configuration may contain:

- configurable targets such as parameters or feature suppression;
- named rows such as Small, Medium and Large;
- one active row;
- configuration rules;
- future typed state only when the backend can preserve it.

It is **not** a collection of independent configuration tables and it is not a
set of unrelated controls that Forge may attach beside each other.

This is why the public API should use the word **configuration** rather than
promoting **table** to a Forge ownership concept. SolidCraft has a native command
named `config.table`, but that command reads/displays the one configuration
definition; it does not imply that a design owns several tables.

The public ownership rule is therefore:

~~~text
final design
└── configuration
    ├── targets
    ├── rows
    ├── active row
    └── rules / supported typed state
~~~

A design may be configured once. A second independent `.configure(...)` call
must not silently create or merge another configuration definition.

## 2. Use cases and the SolidCraft boundary

### Standalone tube clamp

The physical intent is simple:

- **Free**: `clamp_bore = tube_d - clamp_interference`
- **Installed**: `clamp_bore = tube_d`

The desired authoring API should express Installed as boolean configuration
intent. It must not expose a fake numeric 0/1 parameter.

However, this use case is constrained by the current SolidCraft configuration
model. SolidCraft 0.49 does not expose a loose boolean configuration item beside
its one configuration definition. The native boolean-like UI state currently
available is the `enabled` state of a Configuration Rule, which belongs to that
same configuration.

The current executable baseline therefore stores the standalone clamp as one
configuration with a Free/base row plus an Installed rule. A future Forge
`Toggle("Installed", ...)` may provide cleaner public authoring, but it still
belongs to that single configuration owner. It must not be documented as a
second independent configuration surface.

### Parent with named configurations

A parent may have named rows such as:

~~~text
Small   -> size 60, Installed false
Medium  -> size 80, Installed true
Large   -> size 100, Installed true
~~~

Here Installed is **row-owned state**. That is different from one global rule
checkbox that remains enabled or disabled regardless of which row is active.

SolidCraft 0.49 has native row columns for parameters, feature suppression,
materials and appearances. The retained command contract does not expose a
row-owned boolean/toggle column. Forge therefore may define that semantic intent,
but the SolidCraft backend must fail explicitly until it can preserve it.

This distinction is central:

- standalone/global Installed state may potentially lower through one rule;
- per-row Installed state requires a real row-owned boolean capability;
- Forge must not pretend those two meanings are equivalent.

## 3. Public authoring direction

Configuration belongs to the final design result.

Preferred model flow:

~~~python
design = build_design(...)

design.configure(
    ...
)

return design
~~~

The supported final result categories remain:

- Shape;
- component occurrence / ModelInstance;
- Assembly.

The API should make one configuration owner obvious. It should not expose
multiple public configuration-table objects.

### Parameter rows

~~~python
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
~~~

`Param(...)` refers to an existing Forge Parameter. Row cells remain
expressions, not evaluated snapshots.

### Feature suppression rows

~~~python
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
~~~

Feature identity remains Forge-authored identity. Backend feature ids are not
public API.

### Boolean intent

Proposed semantic spelling remains:

~~~python
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
~~~

`Toggle` is configuration intent inside the one design configuration. The word
"standalone" only means that the consumer did not author several named
configuration rows; it does **not** mean that the toggle exists outside the
configuration definition.

Whether SolidCraft 0.49 can lower a particular Toggle shape is a backend
capability question documented in `solidcraft.md`.

## 4. Parent and child ownership

A reusable component owns geometry, parameters and explicitly exported
component-local references. It does not automatically own the application-level
configuration presentation of every document in which it is used.

The final standalone model or higher-level Assembly owns its one configuration.

A parent may drive a shared published child parameter. Future explicit
child-configuration selection is a separate capability and must not be emulated
with:

- numeric 0/1 parameters;
- fake suppression features;
- Python branching per row;
- duplicated child bodies;
- a global rule with different semantics.

## 5. Method behavior

`design.configure(...)` may be called at most once for one final design.

Configuration authoring is declarative. It must not build every variant through
Python branching.

The active/default state affects the compiled initial document state. Other
authored states must remain editable native configuration state after save and
reopen.

The current wrapper remains compatibility API during migration:

~~~python
Configure(
    design,
    active="Medium",
    columns=(...),
    rows={...},
)
~~~

New authoring should converge on `design.configure(...)` only after the new
contract is qualified and released.

## 6. Forge IR contract

Public configuration intent should normalize to engine-neutral semantic IR
before backend lowering.

The semantic model must distinguish at least:

- one configuration owner for the final design;
- named rows and active row;
- parameter targets;
- suppression targets;
- boolean/toggle intent when supported;
- row cells;
- typed effects such as driving a parameter;
- future child-configuration selection.

It must not contain:

- SolidCraft command names;
- SolidCraft row ids;
- Mitcad feature uids;
- replay variables;
- backend-private transport parameters.

Backends may use private transport constructs only when they preserve the exact
semantic meaning.

## 7. SolidCraft lowering boundary

The current SolidCraft 0.49 model and command flow are described in
[solidcraft.md](solidcraft.md).

Forge must not:

- create a second configuration owner because the public API has several
  controls;
- lower row-owned Toggle state to one global rule;
- expose a numeric boolean merely because the backend lacks a boolean row
  target;
- claim saved-design support until state survives save/reopen and switching.

Unsupported semantics fail explicitly.

## 8. Executable probe

The design is paired with two Forge-owned API probes:

~~~text
api-probes/configuration-installed-current/
api-probes/configuration-installed-feature/
~~~

`configuration-installed-current` records the released baseline:

~~~text
one configuration
├── Free/base row
└── Installed rule, enabled = false
~~~

`configuration-installed-feature` tests the alternative suggested by the
native SolidCraft suppression UI:

~~~text
one configuration
├── Free row      -> Installed feature suppressed
└── Installed row -> Installed feature active
~~~

The component exports one real Forge feature named `installed`. In the probe
that feature is the additional cutter which widens the free 9.6 mm clamp bore
to the installed 10.0 mm bore. The final document configures that exported
feature through `Suppress(clamp.feature("installed"))`.

This probe must answer whether a real suppressible component feature gives the
native checkbox behavior we want without inventing a generic boolean API.
The Forge export name is component-local API identity; the probe must also
record what label SolidCraft actually presents for the native feature column.

Both probes are backend evidence. Neither by itself defines the final public
API.

## 9. Acceptance criteria

Before this proposal becomes normative public API, Forge-owned verification must
prove:

1. `.configure(...)` works on supported final design result types.
2. Exactly one configuration owner exists per final design.
3. Existing parameter and suppression rows retain saved-design behavior.
4. Existing `Configure(...)` models remain compatible during migration.
5. Standalone Installed intent survives save/reopen with the authored default.
6. Toggle effects update real native dependencies without rerunning Forge Python.
7. Parameters used only by configuration remain native dependencies.
8. Row-owned Toggle support is claimed only after different boolean values in
   different rows survive save/reopen and row switching.
9. Multiple child occurrences sharing one parent Parameter continue to follow
   the parent configuration.
10. Unsupported child-configuration selection fails explicitly.
11. No public configuration semantic depends on backend ids or command spelling.

## 10. Open design decisions

Still open:

- final naming of `Toggle`;
- whether `DriveParameter` remains the shared effect object;
- eventual spelling for child-configuration selection.

Not open:

- one final design owns one configuration definition;
- reusable components do not implicitly own document configuration;
- public documentation does not treat "table" as a multi-owner Forge concept;
- row-owned state and global rules are different semantics;
- unsupported backend semantics fail explicitly.
