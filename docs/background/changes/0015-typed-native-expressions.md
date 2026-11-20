# Change 0015 — Keep parameter expressions separate from ordinary strings

Status: implementation  
SolidCraft target: **0.42.0**

## Problem

Reusable component-local parameters are renamed before their commands are
inserted into the assembly.

For example:

```text
width -> d1_Label_width
```

The current compiler applies that rename by running a regular expression over
every string value in every native command.

That means a user string can be changed accidentally when one word happens to
match a parameter name. Examples include:

- `Text2D("width")`;
- material names;
- sketch or feature names;
- font names;
- other ordinary SolidCraft string fields.

A parameter expression and user-authored text are different values even when
both are represented as JSON strings at the final SolidCraft boundary.

## Rule

Only strings created from Forge `Parameter` or `Expression` values are
eligible for parameter renaming.

Ordinary user-authored strings are opaque. Forge must copy them unchanged.

## Compiler representation

Forge keeps a small internal string subtype for a native CAD expression while
commands are still being compiled.

Conceptually:

```text
"width"                       ordinary string
NativeExpression("width")     CAD expression
```

Both become normal JSON strings in the final replay document. The internal type
exists only long enough for component parameter namespacing to distinguish
their meaning.

## Lowering

Given:

```python
class Label:
    width = 40.0

    def build(self):
        with Sketch() as sketch:
            Text2D("width", height=5)
        return Box(self.width, 10, 2)
```

and an explicitly published local `width`, Forge may rename the native
parameter:

```text
width -> d1_Label_width
```

The generated SolidCraft values must be:

```text
solid.box.length = "d1_Label_width"
sketch.text.text = "width"
```

The literal text is not rewritten.

The same rule applies to material names, feature names, font names and all
other ordinary strings.

## Scope

This change fixes parameter-expression typing and safe namespacing only.

It does not yet change:

- parameter-loss diagnostics;
- `@assembly` dependency metadata;
- `pv()` warnings;
- the public Parameter/Expression API.

Those dependency checks remain separate follow-up work in remediation Phase 6.

## Qualification

This change must prove:

- a local parameter reference is still renamed inside native expressions;
- composed expressions keep the renamed parameter;
- `Text2D("width")` stays exactly `"width"`;
- a material named `"width"` stays exactly `"width"`;
- a feature/sketch name containing `width` stays unchanged;
- final replay JSON contains only normal JSON strings;
- existing parameter-scope Q4/Q5 remains green.
