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

The final HUB75-style model needs one user-visible Installed choice:

~~~text
Size:
    Small | Large

Installed:
    off | on
~~~

Installed is independent from the active Small/Large row.

When it changes, every participating Installed transition follows:

~~~text
Installed = off
├── left coupler Installed suppressed
├── right coupler Installed suppressed
└── later participating Installed behavior free/suppressed

Installed = on
├── left coupler Installed active
├── right coupler Installed active
└── later participating Installed behavior installed/active
~~~

This requirement does **not** by itself justify a public `State`,
`Toggle`, `Bind`, `ConfigRule` or `DriveParameter` object.

It is final-model configuration intent.

## 5. Row suppression is different

A normal suppression column in a configuration table is row-owned:

~~~text
Small -> Installed feature suppressed
Large -> Installed feature active
~~~

That is not the same as:

~~~text
active row = Small
Installed = off | on
~~~

If both size and Installed were flattened into rows, the model would require:

~~~text
Small / Free
Small / Installed
Large / Free
Large / Installed
~~~

The HUB75 requirement explicitly avoids that Cartesian expansion.

## 6. SolidCraft 0.49 evidence

The current probes establish five separate facts.

### One feature can be configured through suppression

A real named history feature can be a SolidCraft configuration feature target.
This is proven for normal geometry features and for a named `solid.move`
history feature.

### One real feature may operate on several bodies

The `configuration-installed-single-feature` probe uses one native
`solid.move` feature named `Installed` with two bodies as participants.

SolidCraft accepts that one history feature as the configured suppression target
and one independent Installed rule can switch it without changing the
Small/Large row. The corrected probe passed on run **959**.

So when the mechanical Installed transition is truthfully one native operation,
the preferred backend shape is simply:

~~~text
one Installed control
        |
        v
one Installed history feature
        |
        +--> body A
        +--> body B
~~~

No grouping or shared driver is needed for that case.

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

### Several genuinely different native features need another backend mechanism

The `configuration-installed-fanout` probe proves one working SolidCraft 0.49
fallback:

~~~text
Installed native rule
        |
        v
private shared driver
        |
        +--> Installed behavior A
        +--> Installed behavior B
~~~

Small/Large remain normal rows.

That is backend evidence only. A private driver parameter and SolidCraft
Configuration Rule are not public Forge model intent.

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
5. the saved final model exposes one Installed control;
6. that one control affects every participating Installed transition;
7. toggling Installed does not change the active size row;
8. save/reopen preserves both active size and Installed behavior;
9. no SolidCraft rule object or private driver appears in public Forge
   authoring.

## 11. Open questions

Still open:

- exact `with feature(...)` API and whether one scope represents exactly one
  CAD history feature or may represent a semantic group of several operations;
- how a reusable component exports the authored Installed feature identity;
- exact `model.configure(...)` syntax for the one global Installed intent;
- whether `Param(...)` and `Suppress(...)` remain useful public wrappers;
- the best SolidCraft lowering for the global Installed intent given that
  timeline folders are not configuration targets.

Not open:

- configuration belongs to the final model;
- the model is built before `.configure(...)`;
- real Installed behavior should be authored as real history, not removed by
  Python branching;
- a private `_installed` value selects initial build/default suppression only;
- one global Installed control must not require Small/Large Cartesian rows;
- SolidCraft-specific rule mechanics are not the target public Forge API.
