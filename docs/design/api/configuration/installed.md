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

## 5. Preferred SolidCraft lowering when possible

The `configuration-installed-single-feature` probe proves a simpler native
route when Installed can truthfully be authored as one multi-object history
operation:

~~~text
one Installed control
        |
        v
one real Installed feature
        |
        +--> left body
        +--> right body
~~~

The corrected probe passed on CI run **46017873210** (run 959).

For example, one native `solid.move` feature can move several bodies in the
same history step. SolidCraft can configure and suppress that one feature
directly.

This should be preferred over invented driver parameters when the actual CAD
operation is genuinely one feature.

## 6. Fallback when several native features are genuinely required

The earlier `configuration-installed-fanout` probe proves another SolidCraft
0.49 mechanism:

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

The direct timeline-folder experiment does **not** replace this fallback:
SolidCraft 0.49 cannot use a folder containing several native features as one
configuration suppression target.

The public authoring problem and the SolidCraft lowering problem therefore stay
separate. A later backend may gain a simpler multi-feature mechanism without
changing the Forge authoring model.

## 7. Open API work

The remaining API work is deliberately narrow:

- define the scoped/named authored feature API and its initial suppression;
- decide how reusable component feature identity is exported to a final model;
- define the final-model `model.configure(...)` spelling for one global
  Installed intent without exposing SolidCraft rule mechanics;
- decide whether `Param(...)` remains useful or is redundant.

Do not add a separate first-class `State` abstraction unless a later use case
demonstrates semantics that cannot be represented by authored features,
parameters and final-model configuration intent.
