# Change 0012 — Definition identity includes every build input

Status: design and implementation  
SolidCraft target: **0.42.0**

## Problem

Forge decides whether two occurrences may share one native component definition
from `ModelDefinition.key`.

The current key contains:

```python
(
    class_name,
    parameters,
    fixed_inputs,
    input_bindings,
    anchors,
)
```

That is incomplete.

### Parent parameter defaults can disappear

A reusable component may bind one of its inputs to a parent parameter:

```python
Panel(width=Parameter("opening_width", 800))
```

`external_parameters` records the parent parameter name and default value, but
it is not part of `ModelDefinition.key`.

Two `Panel` objects can therefore have the same binding text
`width -> opening_width` while one was built with default 800 and the other
with default 900. Forge may merge those definitions before it gets a chance to
report the conflicting defaults.

The key must include `external_parameters`.

### Non-numeric dataclass inputs are ignored

For a dataclass component, Forge currently records numeric inputs only.

This is unsafe:

```python
@dataclass
class Bracket:
    mirrored: bool = False

    def build(self):
        return left_shape() if self.mirrored else right_shape()
```

`Bracket(mirrored=False)` and `Bracket(mirrored=True)` can produce different
geometry while receiving the same definition key.

For reusable component definitions Forge must record fixed non-numeric inputs
that it can represent safely.

Supported fixed identity values in this change:

- `None`;
- `bool`;
- `str`;
- Enum members;
- tuples made only from supported fixed identity values.

The stored identity value includes a type tag, so `True`, `1` and `"True"`
cannot compare as the same input.

An unsupported mutable or arbitrary object is rejected when it is used as an
input to a reusable component definition. Forge must not silently omit it from
identity.

Root models and reusable assembly classes are not deduplicated as component
definitions, so this rule applies when `component(...)` builds a reusable
physical part.

### Plain object-reference fields

Plain model classes may declare a `None` field and receive an object through
that field. For a reusable `@component`, such a value can affect the produced
Shape.

If the supplied value is one of the supported fixed identity values, Forge
records it. Otherwise Forge rejects the reusable component input. Passing an
arbitrary object and then pretending two results are the same definition is not
allowed.

## Definition key

After this change the definition key contains:

```text
class name
native/local numeric parameters
fixed build inputs, including supported non-numeric values
external parent parameters and their defaults
input bindings
named anchors/topology
```

Two occurrences share a native component definition only when these values are
equal.

The Shape object itself is not used as a hash key. The component class plus all
recorded build inputs must determine that Shape. Unsupported inputs fail before
deduplication instead of being hidden.

## Conflicting inherited defaults

Including `external_parameters` in the key deliberately makes two conflicting
parent defaults separate definitions.

When the compiler then sees both definitions using the same native parent
parameter name with different defaults, it must raise a clear conflict. It must
not pick whichever definition happened to be compiled first.

## Compiler parameter namespace

Forge currently turns the display component name into a parameter prefix.

For example:

```text
display name "Foo 2" -> Foo_2
display name "Foo_2" -> Foo_2
```

Those are different definitions but their local native parameter names can
collide.

While compiling an assembly, Forge assigns each distinct definition an internal
number in first-definition order:

```text
definition 1
definition 2
definition 3
...
```

Local native parameter prefixes include that number plus the readable component
name. The number is compiler-internal; it is not a user occurrence id and not a
SolidCraft browser name.

Example:

```text
d2_Foo_2_width
d3_Foo_2_width
```

The display component names may remain `Foo 2` and `Foo_2`; only the local
parameter namespace needs the definition number.

Parent/external parameter names are not rewritten. If a component intentionally
depends on `opening_width`, that native parameter stays `opening_width`.

## What this change does not do

This change does not:

- add a public definition-id API;
- put Python object ids in command output;
- hash arbitrary Python objects;
- treat display/browser names as identity;
- change occurrence identity from change 0008;
- change parameter expression parsing; typed expression work remains Phase 6.

## Required tests

- same component class + same inputs -> one native definition;
- same component class + different fixed numeric input -> two definitions;
- same inherited parameter name + different default -> explicit conflict;
- dataclass `bool` variant -> distinct definition;
- dataclass `str` variant -> distinct definition;
- dataclass Enum variant -> distinct definition;
- unsupported mutable/object input to a reusable component -> clear error;
- deliberate `Foo 2` / `Foo_2` display-name slug collision -> unique local
  native parameter names;
- external parent parameter names remain unchanged.

## Exit condition

If two reusable component objects can build different native geometry or use
different inherited parameter defaults, Forge must not silently give them the
same definition key.

Different definitions must not share a compiler-generated local parameter name
only because their human-readable component names normalize to the same text.
