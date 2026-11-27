# Configuration API design

Status: proposed  
Tracking: #444

This directory owns the design proposal for the public Forge configuration API.
The SolidCraft-specific backend contract is documented separately in
[SolidCraft configuration model](solidcraft.md).

The current public surface is reviewed separately in the
[Configuration API audit](audit.md). The audit treats generic CAD/compiler
semantics as authoritative; existing SolidCraft-shaped public wrappers receive
no compatibility protection merely because they already shipped.

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

## 3. Canonical HUB75 use case

The configuration API must be judged against a realistic assembly rather than
only isolated table features.

A representative HUB75 design needs three user-visible concerns:

1. **Coupler size** — for example Small versus Large.
2. **Position** — for example Normal versus Service.
3. **Free / Installed** — a shared state that may affect more than one item.

The key design correction is that not every concern needs to become a separate
configuration-choice abstraction.

If Position or Installed is truthfully an authored CAD history transition, it
should first be modelled as a named suppressible feature. Coupler size remains a
normal configurable parameter.

Conceptually:

~~~text
HUB75 design
├── parameter: CouplerSize
├── feature: ServicePosition   (suppressed by default)
└── feature/state: Installed   (suppressed by default)
~~~

The configuration then references those already-authored model objects instead
of inventing them inside `Configure`.

A target direction is therefore closer to:

~~~python
coupler_size = Parameter("coupler_size", 40)

with Feature("ServicePosition", suppressed=True) as service_position:
    # author the real service-position transition
    ...

with Feature("Installed", suppressed=True) as installed:
    # author the real installed transition
    ...

Configure(
    columns=(
        Param(coupler_size),
        Suppress(service_position),
        Suppress(installed),
    ),
    rows={
        "Small": (...),
        "Large": (...),
    },
)
~~~

The exact `Feature(...)` spelling is still proposal-level. The required
semantics are:

- feature identity and default suppression belong to model authoring;
- `Configure` is final-design/top-level intent and only references handles;
- parameters remain top-level configurable values;
- a real positional transition may be a suppressible feature;
- a real Free/Installed transition may be a suppressible feature;
- configuration must not create fake state objects merely because SolidCraft
  has one configuration table.

### Position: authored move versus occurrence placement

The new `configuration-position-suppression` API probe establishes that
SolidCraft 0.49 accepts a named `solid.move` history feature as an ordinary
configuration suppression target:

~~~text
Normal  -> ServicePosition suppressed
Service -> ServicePosition active
~~~

This is a good fit when `ServicePosition` is genuinely an authored CAD history
step.

It is **not** the same as reusable assembly occurrence placement.
SolidCraft's `occurrence.move` stores an occurrence transform and does not
expose that move as a timeline feature. The already-qualified
`configuration-position` model therefore remains the current backend route
for true occurrence placement: configuration parameters are referenced by the
occurrence move/placement expression.

Forge must preserve this distinction. A public feature handle must only lower
to suppression when the backend really has an authored suppressible feature.

### Global Free / Installed

Free / Installed remains especially important because one user-visible state may
need to affect several participating items.

The desired final-design relationship is:

~~~text
global Installed intent
├── left coupler Installed behavior
├── right coupler Installed behavior
└── later participating item
~~~

There are two cases:

- if the final design can truthfully author one real history feature whose
  operation affects all participants, that one feature can be the configuration
  target directly;
- if separate reusable components each own their own Installed feature, Forge
  still needs a binding/composition mechanism so one global intent can control
  those multiple local features without exposing one checkbox per child.

That second case is still open and must be qualified separately. The current
probes prove feature suppression and exported child-feature addressing, but not
yet one shared control driving several independent child features.

### One SolidCraft row list remains the key constraint

A feature-suppression column is still **row-owned state**. Putting
`Installed` or `ServicePosition` beside `coupler_size` in the same table
does not make it an independent control.

For example:

~~~text
Configuration   Coupler size   Installed
Small              40          suppressed
Large              60          suppressed
~~~

stores the Installed suppression value *inside each row*. It does not provide
one global Installed switch that can be changed independently while Small or
Large remains active.

If the authored requirement is:

~~~text
size:       Small | Large
installed:  Free  | Installed
~~~

with both choices independent, flattening both into ordinary row cells would
require the Cartesian states:

~~~text
Small / Free
Small / Installed
Large / Free
Large / Installed
~~~

That is precisely the behavior the generic Forge model should avoid when the
user intent is one row choice plus one independent global state.

The correct semantic distinction is therefore:

~~~text
Configuration rows
    named variant sets such as Small / Large

Global state
    independent state such as Installed
    may bind to one or more semantic effects/features
~~~

SolidCraft may lower that global state through its native Configuration Rule
mechanism and a private shared dependency. That is a backend implementation
choice, not Forge public authoring vocabulary.

The same applies to a position transition when it must remain independently
switchable from the size row. A real `ServicePosition` feature is still the
right authored CAD effect, but the independent control that activates it is a
separate semantic state rather than a row-owned suppression cell.

### Generic compiler boundary

Configuration follows the same compiler architecture as geometry:

~~~text
SCPF authoring
    |
    v
engine-neutral Forge semantic IR
    |
    +--> SolidCraft lowering
    |
    +--> Mitcad lowering
~~~

SolidCraft is the current qualification backend for much of the configuration
surface, but its command vocabulary does not define the Forge semantic model.

The experimental compiler line already has a bounded portable
`ConfigurationIR` with `FeatureRefIR`, suppression columns, rows and an active
row. That is evidence for the architecture, not a reason to copy its current
bounded shape into the complete API.

An independent global state is a later generic IR capability. Conceptually it
must preserve:

- semantic state identity and display name;
- default boolean value;
- independence from the active named row;
- references/bindings to authored model behavior;
- shared use by several component occurrences.

It must **not** preserve:

- SolidCraft `config.rule` ids;
- `always` conditions introduced only by lowering;
- `drive_parameter` effects;
- private driver parameters such as `installed_offset`;
- Mitcad uids or equivalent backend handles.

A backend may synthesize those objects after semantic normalization.

A useful target shape for the HUB75 case is therefore conceptually:

~~~python
installed = State("Installed", default=False)

left = Coupler(
    size=self.coupler_size,
    installed=installed,
)

right = Coupler(
    size=self.coupler_size,
    installed=installed,
)

Configure(
    design,
    active="Small",
    columns=(Param(self.coupler_size),),
    rows={
        "Small": ("40 mm",),
        "Large": ("60 mm",),
    },
    states=(installed,),
)
~~~

The exact `State` and `states=` spelling is still proposal-level. The
important semantic property is that the **same state object** is passed to both
reusable components. That gives the compiler one shared state identity before
either backend is selected.

Inside a reusable component the state must control semantic authored behavior,
not inspect which backend will eventually run. The exact feature/state authoring
syntax remains to be qualified.

## 4. Public authoring direction

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

### Independent state intent

The public API needs a generic semantic representation for state that remains
independent from the active configuration row.

Conceptually:

~~~python
installed = State("Installed", default=False)

Bind(
    installed,
    left.interface("installed"),
    right.interface("installed"),
)
~~~

The exact `State` / `Bind` spelling is still proposal-level. The required
meaning is not:

~~~text
run an Always rule that DriveParameters something
~~~

but:

~~~text
one authored global state
    -> zero or more semantic bindings/effects
~~~

A backend may implement that state through a native rule, feature suppression,
a private driver parameter or another supported mechanism. Those lowering
objects must not become public Forge API merely because one backend needs them.

The state still belongs to the one final-design configuration definition; it is
independent of the active row, not a second configuration owner.

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

The probe result is positive for the feature-suppression approach, with one
important Forge naming gap:

- the SCPF probe compiles and replays successfully;
- `Free` stores the feature as suppressed and `Installed` stores it active;
- current Forge lowers the exported `installed` feature to the native history
  feature `Cylinder3`, so the native configuration target is currently
  `suppress:Cylinder3`;
- a second native SolidCraft probe renames that same history feature to
  `Installed` with `timeline.rename` before configuration and then
  successfully configures `suppress:Installed`.

Therefore SolidCraft 0.49 already has the backend capability needed for a
human-readable Installed feature checkbox. The remaining gap is Forge feature
naming/lowering, not a missing SolidCraft boolean widget.

The runnable clamp probe deliberately uses a simplified extra cutter only to
prove the configuration mechanism. It is **not** the intended mechanical model
of a flexible clamp. In a real clamp, switching from Free to Installed should
preserve the actual mechanism: for example the split clamp arms/halves should
move or deform to the installed position rather than simply replacing the bore
with a larger cylindrical cut.

The API consequence is that `Installed` should be understood as a real authored
CAD feature/state whose suppression controls the installed transformation. The
feature may drive movement, placement or other real model history; it does not
have to be a literal cutter. The important part is that the state is represented
truthfully in CAD history and can therefore use SolidCraft's native
feature-suppression checkbox.

For this Tube Clamp use case, a generic `Toggle` should **not** be introduced
merely to obtain a checkbox if `Installed` can be represented truthfully as a
real suppressible CAD feature. A generic boolean configuration semantic remains
a separate question for states that are not real feature suppression.

Both probes are backend evidence. Neither by itself defines a new public API.

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

- whether any generic `Toggle` API is required after feature-owned boolean
  states are handled through real suppressible features;
- how a Forge exported feature's public name should map to the native SolidCraft
  history/display name without leaking backend identity;
- whether `DriveParameter` remains the shared effect object for genuinely
  rule-driven state;
- eventual spelling for child-configuration selection.

Not open:

- one final design owns one configuration definition;
- reusable components do not implicitly own document configuration;
- public documentation does not treat "table" as a multi-owner Forge concept;
- row-owned state and global rules are different semantics;
- unsupported backend semantics fail explicitly.
