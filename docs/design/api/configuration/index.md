# Configuration API design

Status: implementation in progress  
Tracking: #444

Forge configuration belongs to the **final model**.

The public flow is:

~~~python
model = panel + left + right

model.configure(
    active="Small",
    columns=(
        self.coupler_size,
        right.feature("installed"),
    ),
    rows={
        "Small": ("40 mm", True),
        "Large": ("60 mm", True),
    },
)

return model
~~~

There is no public configuration wrapper object.

## Public semantics

A configuration column is an existing semantic handle:

- a `Parameter` means a parameter-value column;
- an authored Shape/component feature handle means feature suppression.

Forge therefore does not need public wrappers such as:

~~~text
Param(...)
Suppress(...)
~~~

and configuration itself does not need:

~~~text
Configure(...)
ConfigRule(...)
Always()
DriveParameter(...)
State(...)
Toggle(...)
Bind(...)
~~~

The backend may use native machinery internally, but that is not Forge
authoring vocabulary.

## Reusable component features

Reusable components deliberately export history features that a final model may
configure.

Current qualified authoring:

~~~python
@component(include=("width",))
class Coupler:
    width = 40.0

    def build(self):
        body = Box(self.width, 20, 10)
        installed = (
            Hole(d=5)
            .at(0, 0, 10)
            .export_feature("installed")
        )
        return body - installed
~~~

The final model refers to that identity with:

~~~python
coupler.feature("installed")
~~~

Feature identity belongs to the component **definition**. Copies of the same
definition therefore share the same authored feature identity in the native
component history.

The exact future syntax for naming a feature and setting its initial
suppression outside a configuration row remains a separate feature-authoring
question. It must not block or complicate the configuration API.

## Configuration rows

Rows store values for the declared columns.

For example:

~~~text
Configuration   Coupler size   Suppress: Installed
Small              40 mm               [x]
Large              60 mm               [x]
~~~

SolidCraft exposes the feature column as a normal suppression checkbox.

The suppression value is configuration data. No Configuration Rule is required.

## Final-model ownership

Configuration is attached only after the model has been composed:

~~~python
model = left + right
model.configure(...)
return model
~~~

A reusable component cannot own the final document configuration.

This keeps reusable geometry separate from application/model presentation.

## Current implementation direction

The normal `dev` API is being changed to:

- `Shape.configure(...)`;
- `ModelInstance.configure(...)`;
- `Assembly.configure(...)`;
- direct `Parameter` columns;
- direct Shape/component-feature suppression columns.

The former public helper surface is being removed.

## Generic compiler boundary

This API work does not redesign the `exp` IR.

The architecture remains:

~~~text
Forge authoring intent
        |
        v
generic semantic compiler boundary
        |
        +--> SolidCraft lowering
        +--> Mitcad lowering
~~~

The `exp` lane owns typed IR evolution. This `dev` work supplies clean
semantics and backend evidence without exposing SolidCraft command vocabulary
as public Forge API.

## Remaining feature-authoring work

Configuration itself is now small.

The remaining separate question is how Forge should author a named history
feature with an initial suppression state, for example conceptually:

~~~python
with feature("Installed", suppressed=True):
    ...
~~~

That syntax is not part of the configuration API until its history semantics
are proven. The existing `export_feature(...)` path remains the qualified
feature-identity mechanism in the meantime.
