# Global Installed fan-out probe

## Why this probe exists

A realistic HUB75-style design needs one user-visible `Installed` state that
can affect several participating items while the normal configuration row still
selects a size such as Small or Large.

The public Forge API should not expose SolidCraft rule mechanics merely to make
that possible. Before replacing the current rule API, this probe establishes
what the SolidCraft backend can actually preserve in one saved design.

## Question

Can one independent native `Installed` control drive one shared dependency
while several separately authored model operations react to that dependency?

The important UI requirement is one Installed control, not one checkbox per
participating item.

## Model

The probe creates:

- a base plate whose width follows `coupler_size`;
- a left coupler body;
- a right coupler body;
- one shared parameter `installed_offset`;
- a left move that uses `installed_offset`;
- a right move that uses the same parameter with the opposite sign.

The normal configuration rows are:

| Row | coupler_size | installed_offset |
| --- | ---: | ---: |
| Small | 40 mm | 0 mm |
| Large | 60 mm | 0 mm |

One independent native Configuration Rule named `Installed` drives
`installed_offset = 4 mm` when enabled.

Both coupler motions therefore follow the same one control.

## What success proves

A green probe proves that SolidCraft can preserve this structure in one native
configuration:

~~~text
size row: Small | Large

Installed rule: off | on
        |
        +--> shared installed_offset
                 |
                 +--> left motion
                 +--> right motion
~~~

This is backend evidence for one global semantic state fanning out to multiple
participants.

## What this probe does not prove

It does **not** make `ConfigRule`, `Always` or `DriveParameter` good Forge
public API. Those names describe the SolidCraft lowering used by this probe.

It also does not yet prove the final reusable-component interface spelling.
The probe deliberately uses two bodies in one document so the backend fan-out
semantics can be isolated first.

## API consequence

If this probe succeeds, Forge needs a first-class global state concept whose
backend may lower to a SolidCraft rule plus a private shared dependency.

The consumer should author the semantic state and bind participating component
interfaces to it. The consumer should not author `config.rule` mechanics,
`Always()`, or a backend transport parameter.

A later reusable-child probe should qualify the exact component interface and
binding syntax.
