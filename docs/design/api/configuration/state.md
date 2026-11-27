# Configuration state semantic contract

Status: proposed  
Tracking: #444

This document defines the generic meaning required for configuration state.
It deliberately does not define SolidCraft Configuration Rules as Forge API.

## Purpose

A final model may need state that is independent from its active named
configuration row.

Canonical example:

~~~text
size row:
    Small | Large

global state:
    Installed = false | true
~~~

Changing Installed must not require changing or duplicating the active size
row.

The same state may be consumed by several reusable components.

## Ownership

A configuration State is owned by the final model configuration.

It is not:

- a property of one Coupler occurrence;
- a second configuration table;
- a numeric model parameter disguised as boolean;
- a SolidCraft Configuration Rule;
- a backend feature id.

A reusable component may **consume** a state input and author behavior that
depends on it. Several occurrences may consume the same state object.

Conceptually:

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
~~~

The exact frontend spelling remains proposal-level. The required property is
shared semantic identity: `left` and `right` receive the same authored state,
not two unrelated booleans with the same label.

## State is not a row cell

A suppression cell in a configuration row means:

~~~text
Small -> feature suppressed
Large -> feature active
~~~

That value belongs to the selected row.

A State means:

~~~text
active row = Small
Installed = false

or

active row = Small
Installed = true
~~~

without changing the active row.

These are different semantic dimensions and must remain different in IR.

## Component behavior

A component consuming a State may use it to author semantic behavior such as:

- selecting between Free and Installed dimensional/placement values;
- activating an authored Installed transition;
- selecting a service/normal position;
- controlling another explicitly supported state-aware CAD behavior.

The component must not inspect the selected backend or author
`config.rule`/Mitcad transport itself.

An eventual frontend may provide state-dependent value expressions or
state-controlled feature authoring. Those APIs must be designed from this
semantic contract rather than from one backend command vocabulary.

## Generic IR requirement

The complete engine-neutral configuration IR needs a representation for an
independent state.

The final type names are not fixed here, but the semantic data must contain at
least:

~~~text
state identity
display name
default boolean value
configuration ownership
semantic uses/bindings
~~~

A use/binding must reference semantic model identity such as a parameter/value
dependency, authored feature or component state interface. It must not contain a
native backend id.

The state representation is orthogonal to:

~~~text
ConfigurationIR.rows
ConfigurationIR.active
~~~

The current experimental `ConfigurationIR` is intentionally a bounded
suppression-row slice. Adding state must extend the semantic model; it must not
reinterpret a row suppression cell as independent state.

## Backend lowering

A backend may use any native mechanism that preserves the state semantics.

For SolidCraft 0.49 the qualified fan-out probe demonstrates one possible
lowering:

~~~text
semantic Installed state
        |
        v
native Configuration Rule          backend-private
        |
        v
private installed_offset           backend-private
        |
        +--> left authored motion
        |
        +--> right authored motion
~~~

Neither the rule nor `installed_offset` belongs in public Forge API or
engine-neutral IR.

The experimental Mitcad configuration lowering already demonstrates the same
ownership principle for row suppression: it synthesizes a private driver
parameter that is absent from semantic `ConfigurationIR`.

A backend that cannot preserve a particular State use must fail explicitly.
It may not silently turn the state into duplicated rows or expose a private
numeric flag as public model intent.

## HUB75 acceptance use case

The minimum reference design is:

~~~text
HUB75 assembly
├── size row
│   ├── Small
│   └── Large
├── Installed state
│   ├── left coupler reacts
│   └── right coupler reacts
└── optional ServicePosition state
    └── display/assembly position reacts
~~~

The required observable behavior is:

1. Small and Large remain the only size rows.
2. Installed can toggle without changing the active size row.
3. Both participating couplers react to the same Installed state.
4. Save/reopen preserves both the active row and state.
5. The public model contains no backend-private driver parameter.
6. Backend-specific rule/driver objects do not appear in semantic IR.
7. A second independent state such as ServicePosition does not force a
   Small/Large Cartesian row expansion.

## Consequence for the current public API

The semantic requirement supports adding a first-class State concept.

It does not support retaining the current public rule vocabulary:

~~~text
ConfigRule
Always
DriveParameter
Configure(..., rules=...)
~~~

Those objects describe one SolidCraft lowering path and should be removed from
the intended public generic API when the semantic State path replaces their
qualified use case.
