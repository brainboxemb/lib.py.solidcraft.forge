# Configuration API audit

Status: working design audit  
Tracking: #444

This audit reviews the current public Forge configuration surface against the
generic CAD-compiler architecture.

The test is deliberately stricter than compatibility:

> A public Forge API object must represent engine-neutral CAD/configuration
> meaning. Existing release history is not sufficient reason to keep it.

SolidCraft commands, UI mechanics and transport objects may remain in a backend
lowering, but they do not earn a public Forge abstraction merely because the
SolidCraft backend needs them.

The experimental compiler line provides the architecture direction: SCPF is a
frontend, typed Forge IR is the semantic contract, and SolidCraft and Mitcad
are independent lowerings. Configuration must converge on the same rule.

## Audit criteria

A public configuration object is legitimate only when all of the following are
true:

1. Its meaning can be stated without mentioning SolidCraft or Mitcad.
2. The meaning belongs to authored CAD/configuration intent rather than backend
   execution mechanics.
3. It can normalize to engine-neutral typed IR.
4. A backend may lower it differently, or fail explicitly when unsupported.
5. Native ids, command names, replay variables, helper parameters and UI
   implementation details are not part of its public contract.

## Current public objects

### `Configure(...)`

**Disposition: keep the semantic concept; public spelling is not protected.**

Legitimate generic meaning:

- one configuration owned by the final model/design;
- named rows;
- one active row;
- references to configurable semantic targets.

That maps naturally to engine-neutral `ConfigurationIR`.

What is not protected:

- the current wrapper-function shape;
- the requirement to pass the final design as the first positional argument;
- the current tuple-cell authoring format;
- the current `rules=` extension.

The eventual frontend may use `Configure(...)`, `design.configure(...)`, or
another spelling. The IR contract, not the current helper signature, owns the
semantics.

### `Param(parameter)`

**Disposition: keep parameter-target semantics; review/remove the wrapper if it
adds no semantic value.**

A configuration row assigning an expression to a model parameter is generic CAD
intent. A typed IR therefore needs a parameter target/reference.

The open question is only frontend syntax. If an existing `Parameter` handle
is already unambiguous in configuration authoring, wrapping it in `Param(...)`
may be redundant.

Do not retain `Param` merely because SolidCraft calls one native column
`param:<name>`.

### `Suppress(feature)`

**Disposition: keep the semantic concept.**

Feature suppression is generic parametric-CAD/history intent:

- identify one authored semantic feature;
- store active/suppressed state in a configuration.

The experimental IR already demonstrates the right architectural shape through
engine-neutral `FeatureRefIR`, `SuppressionColumnIR` and
`ConfigurationIR`.

The public spelling `Suppress(...)` may still be reviewed, but the semantic
operation is legitimate.

### `ConfigRule(...)`

**Disposition: remove from the intended public generic API unless an independent
generic rule-system requirement is established.**

The current object was introduced as a typed wrapper around SolidCraft
`config.rule`. Its initial use case was keeping Installed independent from
Small/Medium/Large rows.

That requirement is legitimate. The public object is not automatically
legitimate.

A generic Forge state may lower to a SolidCraft Configuration Rule, a Mitcad
driver, several native feature suppressions, or another backend mechanism.
Consumers should not author a SolidCraft-shaped rule object to request that
state.

The native rule capability remains valuable backend evidence.

### `Always()`

**Disposition: remove from the intended public API with `ConfigRule`.**

`Always` currently exists only as a condition object for the SolidCraft-shaped
rule API. There is no independent authored CAD concept in the qualified use
cases that requires consumers to say “always condition”.

If a future generic constraint/rule language is needed, it must be designed
from semantic requirements rather than preserving this object.

### `DriveParameter(parameter, expression)`

**Disposition: remove from the intended public API with `ConfigRule`.**

Driving a parameter can be a backend lowering effect, but the user-facing
intent in the current Installed case is a global state, not “execute a
drive-parameter rule”.

A generic state/configuration binding may internally drive parameters when a
backend needs that transport. Such a helper parameter/effect remains
backend-private.

### `Configure(..., rules=...)`

**Disposition: remove from the intended generic authoring contract.**

The current field exposes the native rule mechanism directly in the
configuration object. The valid semantic requirement is independent state or
conditional authored behavior; the backend mechanism is not part of the public
configuration model.

## Related feature handles

### `Shape.export_feature(name)` and `occurrence.feature(name)`

**Disposition: retain the generic requirement; review naming and scope.**

Reusable components need an engine-neutral way to publish authored semantic
feature identity to a parent/final model.

That requirement aligns with `FeatureRefIR`.

The current Forge export name is component-local API identity and does not
automatically become a native history/display name. That separation is valid,
but the eventual feature-handle API must make naming, default suppression and
component scope explicit enough for configuration use.

## Required generic model

The HUB75 reference use case requires semantic intent approximately like:

~~~text
final model configuration
├── size rows
│   ├── Small
│   └── Large
├── global state: Installed
│   └── bound to several participating component behaviors
└── optional authored positional state
    └── real feature when position is a history transition
~~~

This must normalize before backend lowering.

The generic IR therefore eventually needs to distinguish at least:

- configuration owner;
- named rows and active row;
- parameter target/reference;
- feature target/reference;
- suppression cells;
- independent semantic state;
- binding of one state to one or more semantic effects/interfaces.

It must not encode:

- `config.rule`;
- `always`;
- `drive_parameter`;
- SolidCraft feature ids;
- Mitcad uids;
- private driver parameters created only for lowering.

## Relationship to the experimental IR

The current experimental compiler line has already established the first
portable configuration slice:

- `FeatureRefIR`;
- `SuppressionColumnIR`;
- `ConfigurationRowIR`;
- `ConfigurationIR`;
- `ModelIR.configuration`.

That slice is intentionally bounded to one suppression-column case. Parameter
columns, rules, child-definition references and richer configuration/state
semantics are still separate expansion work.

That is the correct migration pattern: add semantic IR only after the generic
meaning is clear, then lower it independently per backend.

The stable SolidCraft compatibility path must not be used as evidence that its
current public wrappers belong in the future generic API.

## Immediate cleanup direction

Do not add new public configuration-rule helpers.

Continue qualification with probes at the backend boundary, but describe the
public requirement in generic terms:

- global state;
- semantic feature;
- parameter target;
- state-to-component binding;
- row configuration.

Once the global Installed fan-out semantics are qualified, replace the
SolidCraft-shaped public rule surface rather than extending it.
