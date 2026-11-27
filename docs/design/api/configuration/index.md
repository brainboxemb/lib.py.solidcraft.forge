# Configuration API design

Status: proposed  
Tracking: #444

This document defines the current Forge-facing configuration direction.

Backend-specific SolidCraft behavior is recorded in
[SolidCraft configuration model](solidcraft.md). The current released public
surface is reviewed in [Configuration API audit](audit.md). The concrete
model-level Installed use case is recorded in
[Global Installed configuration contract](installed.md).

## 1. Design principles

Forge configuration belongs to the **final model**.

The intended flow is:

~~~python
model = panel + left + right

model.configure(
    ...
)

return model
~~~

Configuration does not create the model and should not require returning a
special wrapper object.

A final model owns one configuration definition. Reusable components own their
geometry, parameters and authored feature history; they do not automatically
own the final document's configuration presentation.

Forge public API should express CAD/configuration intent. SolidCraft commands,
rule objects, native ids and private transport parameters belong in lowering,
not in the public API.

## 2. Parameters and named rows

Ordinary dimensional configuration remains simple.

Conceptually:

~~~python
class Hub75:
    coupler_size = 40.0

    def build(self):
        left = Coupler(size=self.coupler_size, name="left")
        right = Coupler(size=self.coupler_size, name="right")

        model = left + right

        model.configure(
            active="Small",
            columns=(
                self.coupler_size,
            ),
            rows={
                "Small": ("40 mm",),
                "Large": ("60 mm",),
            },
        )

        return model
~~~

The exact final syntax is not implemented yet.

Two current API details are deliberately not protected:

- the released `Configure(model, ...)` wrapper should converge on
  `model.configure(...)`;
- `Param(parameter)` may be redundant when the Parameter handle itself is
  already an unambiguous configuration target.

The semantic requirement is only that named rows retain symbolic parameter
assignments and one active row.

## 3. Authored suppressible features

Installed, ServicePosition and similar transitions should first be modeled as
real CAD history when they are real CAD history.

A reusable component should always author the transition. A private Forge/build
input may choose its initial suppression state.

Conceptually:

~~~python
class Coupler:
    _installed = False

    def build(self):
        model = step_a()
        model = step_b(model)

        with feature(
            "Installed",
            suppressed=not self._installed,
        ):
            model = installed_motion(model)

        return model
~~~

The exact `feature(...)` spelling is proposal-level.

Required semantics:

- the Installed feature exists in both Free and Installed initial builds;
- `_installed` only selects the initial suppression state;
- `_installed` is not a saved CAD parameter;
- Forge must not use Python branching to omit one history path;
- the authored feature remains addressable/suppressible after Forge finishes.

This gives a history such as:

~~~text
StepA
StepB
Installed   [suppressed]
~~~

or:

~~~text
StepA
StepB
Installed   [active]
~~~

with the same history structure in both cases.

## 4. Global Installed behavior

The preferred mechanical shape is one authored Installed feature whenever the
real CAD transition can truthfully be one history operation:

~~~text
one authored feature: Installed
    ├── affects left coupler
    ├── affects right coupler
    └── may affect other participating geometry
~~~

SolidCraft proves that one native feature may act on several bodies. That keeps
the CAD history simple.

The configuration semantics still have two distinct cases.

### Row-owned Installed

Installed may be stored directly as a normal feature-suppression column:

~~~text
Configuration   Coupler size   Suppress: Installed
Small              40 mm              [x]
Large             100 mm              [ ]
~~~

This needs no Configuration Rule. The suppression value belongs to each row.

### Installed independent from Small/Large

If the requirement is instead:

~~~text
active row: Small

Installed: off | on
~~~

with Installed switchable without changing or rewriting the Small row, then
direct row-owned suppression is not the same semantic.

SolidCraft 0.49 can preserve that independent control by keeping the same one
real Installed feature as the suppression target and using a native
Configuration Rule to drive its suppression. That backend route was proven by
the single-feature rule variant before the direct row-owned probe.

The rule is a SolidCraft lowering mechanism. It does **not** justify public
`ConfigRule`, `Always`, `DriveParameter` or a new first-class `State`
object in Forge.

## 5. Configuration suppression

Feature suppression is a normal configuration target. Use it directly when the
suppression value is genuinely part of a named configuration row.

Do not describe a row-owned suppression cell as an independent global control.
Those semantics must remain separate even when both eventually operate on the
same authored Installed feature.

There is no need to synthesize separate Free/Installed rows merely to expose a
row-owned suppression value. A separate global Installed requirement is handled
at the final-model configuration level and may require backend-specific
lowering.

## 6. SolidCraft 0.49 evidence

The current probes establish five separate facts.

### One feature can be configured through suppression

A real named history feature can be a SolidCraft configuration feature target.
This is proven for normal geometry features and for a named `solid.move`
history feature.

### One real feature may operate on several bodies

The `configuration-installed-single-feature` probe uses one native
`solid.move` feature named `Installed` with two bodies as participants.

SolidCraft accepts that one history feature directly as the configured
suppression target. The rule-free direct configuration probe passed on run
**971** and proves the row-owned case.

The earlier single-feature rule variant also passed (runs **959** and **966**)
and proves that the same one native feature can be controlled independently
from the active Small/Large row through SolidCraft's rule mechanism.

So the preferred **history** shape is the same in both cases:

~~~text
one Installed history feature
        |
        +--> body A
        +--> body B
~~~

Only the configuration lowering differs between row-owned suppression and an
independent Installed control.

### A timeline folder can contain several Installed features

The `configuration-installed-group` baseline proves:

~~~text
Installed timeline folder
├── LeftInstalled
└── RightInstalled
~~~

SolidCraft can suppress that folder manually as one history operation.

### A timeline folder is not a configuration target

The same probe also establishes the important negative result.

SolidCraft 0.49 rejects:

~~~text
config.configure(features=["Installed"])
~~~

with:

~~~text
no feature 'Installed'
~~~

and rejects using the folder id as one `drive_suppression` target because the
target is not a configured feature.

Therefore Forge must **not** assume that a scoped/nested Installed feature group
can lower directly to one SolidCraft configuration checkbox.

## 7. Position behavior

Position has two distinct cases.

A genuine authored move/history transition may be modeled as a named
suppressible feature:

~~~text
ServicePosition
    -> real history feature
    -> suppressible
~~~

A reusable occurrence placement is different. SolidCraft `occurrence.move`
stores an occurrence transform and is not itself a timeline feature.

Forge should provide coherent authoring where possible, but lowering must not
pretend these are the same backend capability.

## 8. Public API direction

Current disposition:

~~~text
keep semantic concept                 review/remove public wrapper

final model configuration             Configure(model, ...)
parameter configuration target        Param(...)
feature suppression                   exact Suppress(...) spelling
authored feature identity             current export/name spelling

remove from intended public API

ConfigRule(...)
Always()
DriveParameter(...)
Configure(..., rules=...)
~~~

`ConfigRule`, `Always` and `DriveParameter` were introduced around a
SolidCraft mechanism. They may remain temporarily in the released compatibility
path while replacement authoring is developed, but they do not define the
target Forge API.

## 9. Generic compiler boundary

The normal `dev` API work should not redesign the experimental IR in this
issue.

The architectural requirement is only:

~~~text
Forge authoring intent
        |
        v
generic semantic compiler boundary
        |
        +--> SolidCraft lowering
        +--> Mitcad lowering
~~~

The `exp` lane owns the typed IR work and its migration sequence.

This configuration work should supply clear semantic requirements and backend
evidence. It should not copy SolidCraft command structure into future IR or
pre-empt the current `exp` design.

## 10. Required concrete example

Before this API is finalized, one realistic model must prove the whole flow:

~~~text
HUB75 final model
├── Small / Large size rows
├── left reusable coupler
│   └── real Installed history transition
├── right reusable coupler
│   └── real Installed history transition
└── one model-level Installed control
~~~

The acceptance behavior is:

1. the model is built first and configured afterward;
2. Small/Large remain the only size rows;
3. each coupler always contains its Installed history transition;
4. initial Free/Installed can select suppression at Forge build time;
5. the saved final model exposes one `Suppress: Installed` configuration column;
6. that one feature affects every participating Installed geometry operation;
7. the configuration stores the Installed suppression value directly;
8. save/reopen preserves active configuration and suppression value;
9. no SolidCraft rule object or private driver is involved.

## 11. Open questions

Still open:

- exact `with feature(...)` API and whether one scope represents exactly one
  CAD history feature or may represent a semantic group of several operations;
- how a reusable component exports the authored Installed feature identity;
- exact `model.configure(...)` syntax for the Installed suppression target;
- whether `Param(...)` and `Suppress(...)` remain useful public wrappers;
- whether the final Forge syntax needs an explicit `Suppress(...)` wrapper or
  can accept an authored feature handle directly.

Not open:

- configuration belongs to the final model;
- the model is built before `.configure(...)`;
- real Installed behavior should be authored as real history, not removed by
  Python branching;
- a private `_installed` value selects initial build/default suppression only;
- Installed is represented directly by configured feature suppression;
- SolidCraft-specific rule mechanics are not needed for this example.
