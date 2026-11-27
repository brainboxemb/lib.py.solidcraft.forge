# Global Installed configuration contract

Status: proposed  
Tracking: #444

This document records the concrete Installed use case. It does **not** introduce
a public `State` object.

## 1. Component authoring

A reusable component always authors its real Installed history step. A private
Forge/build input may choose only the initial suppression state.

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

The exact `feature(...)` spelling is still proposal-level.

The required semantics are:

- the Installed history feature exists whether the initial state is Free or
  Installed;
- `_installed` is only a Forge build/default input;
- `_installed` is not a saved CAD parameter and does not remove either
  history path through Python branching;
- the authored Installed feature remains suppressible after Forge has finished.

So this is intentionally **not**:

~~~python
if self._installed:
    build_installed_variant()
else:
    build_free_variant()
~~~

Both initial states produce the same history structure; only the initial
suppression differs.

## 2. Final-model authoring

Configuration belongs to the final model after its parts have been assembled.

Conceptually:

~~~python
left = Coupler(name="left")
right = Coupler(name="right")
panel = Hub75Panel(name="panel")

model = panel + left + right

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

The current `Configure(model, ...)` wrapper and `Param(...)` helper are not
treated as protected final syntax. In particular, if
`self.coupler_size` is already an unambiguous Parameter handle, an extra
`Param(...)` wrapper may be unnecessary.

## 3. Global Installed requirement

The saved final model should expose one Installed choice for the whole model:

~~~text
Size:
    Small | Large

Installed:
    off | on
~~~

Changing Installed must not require changing the active Small/Large row.

When Installed changes, every participating authored Installed transition must
follow:

~~~text
Installed = off
├── left Installed feature suppressed
├── right Installed feature suppressed
└── any later participating Installed behavior suppressed/free

Installed = on
├── left Installed feature active
├── right Installed feature active
└── any later participating Installed behavior active/installed
~~~

This is a final-model configuration requirement. It does not imply a public
`State`, `Bind`, `ConfigRule` or `DriveParameter` object.

## 4. SolidCraft 0.49 result

The direct timeline-folder idea was tested because it matches the authoring
model closely:

~~~text
Installed folder
├── LeftInstalled
└── RightInstalled
~~~

The `configuration-installed-group` probe proves:

- SolidCraft can create this timeline folder when its features form one
  contiguous history run;
- SolidCraft can manually suppress the folder as one group;
- SolidCraft cannot register the folder as a configuration feature;
- a Configuration Rule cannot use that folder as one
  `drive_suppression` target.

The decisive runtime errors are retained in the probe README:

~~~text
rule 'Installed' target is not configured
no feature 'Installed'
~~~

Therefore a Forge `with feature("Installed", ...)` scope must not be assumed
to lower directly to one SolidCraft configuration target when it contains
several native history features.

## 5. Working SolidCraft fallback already proved

The earlier `configuration-installed-fanout` probe proves one SolidCraft 0.49
mechanism that does provide one independent Installed control:

~~~text
Installed native rule
        |
        v
private shared driver
        |
        +--> left Installed behavior
        +--> right Installed behavior
~~~

That shared driver is backend transport. It is not public Forge model intent.

The public authoring problem and the SolidCraft lowering problem therefore stay
separate:

~~~text
Forge authoring:
    real named Installed features + final-model Installed intent

SolidCraft 0.49 lowering:
    use a supported native mechanism that preserves one global control
~~~

If SolidCraft later supports configuration suppression of timeline folders or a
multi-feature suppression target, the lowering may become simpler without
changing the Forge authoring model.

## 6. Open API work

The remaining API work is deliberately narrow:

- define the scoped/named authored feature API and its initial suppression;
- decide how reusable component feature identity is exported to a final model;
- define the final-model `model.configure(...)` spelling for one global
  Installed intent without exposing SolidCraft rule mechanics;
- decide whether `Param(...)` remains useful or is redundant.

Do not add a separate first-class `State` abstraction unless a later use case
demonstrates semantics that cannot be represented by authored features,
parameters and final-model configuration intent.
