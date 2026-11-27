# Installed configuration example

Status: qualified backend pattern; Forge API migration in progress  
Tracking: #444

This document records the concrete Installed pattern that drives the current
configuration API cleanup.

## Desired model

A final model contains reusable couplers and ordinary size configurations.

~~~text
final model
├── Small / Large configuration rows
├── left Coupler
├── right Coupler
└── Coupler definition feature: installed
~~~

The Coupler definition owns its real Installed history transition.

Copies of that Coupler reuse the same component definition and therefore the
same authored feature identity.

## Forge authoring

The final configuration should read approximately:

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

The boolean cells are suppression values:

~~~text
True  -> Installed feature suppressed
False -> Installed feature active
~~~

There is no public rule object and no synthetic boolean State object.

## SolidCraft result

SolidCraft receives a normal configuration with:

~~~text
parameter column: coupler_size
feature column:   Suppress: Installed
~~~

The existing UI displays such a feature column as:

~~~text
Suppress: <feature name>
~~~

or its localized equivalent.

## Qualification

The `configuration-installed-single-feature` probe proves that one native
feature can affect more than one body and can be configured directly as a
suppression target without `config.rule`.

The direct rule-free probe passed in run 971.

## Separate concern: initial suppression

A reusable component may later need to say that an authored feature starts
suppressed even before a final configuration is attached.

That is a feature-history authoring concern, not a reason to expand the
configuration API.

A scoped syntax such as:

~~~python
with feature("Installed", suppressed=True):
    ...
~~~

remains proposal-level until its native history semantics are qualified.
