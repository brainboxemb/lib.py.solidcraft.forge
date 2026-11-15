# 0004 — Three reference implementations per qualification case

Status: **tracked design change**  
Tracking issue: **#174**  
Applies to: Forge qualification cases and published comparison output

## 1. Decision

Every Forge qualification case should normally contain three independent
reference implementations:

```text
PythonSCAD
pyBOSL2
CadQuery
```

Each reference is executed by the qualification runner and must produce its
own measurable output:

```text
model.stl
model-front.png
model-right.png
model-iso.png
result.json
```

The Forge/SolidCraft result remains the native implementation under test. The
three external implementations are comparison references.

## 2. Why three

The libraries provide different useful viewpoints:

- **PythonSCAD** — direct Python constructive geometry;
- **pyBOSL2** — attachment/anchor-oriented modelling vocabulary;
- **CadQuery** — object/workplane/assembly/location-oriented modelling.

Using all three by default prevents qualification from silently becoming a
comparison against only the libraries that happen to be easiest for a
particular implementation.

The references compare modelling intent and visible/measurable geometry. Native
SolidCraft behaviour such as saved parameter mutation, persisted feature
history, topology identity and native joint solving is still proved only by
SolidCraft Q3-Q6 evidence.

## 3. Exception rule

A case may omit one reference implementation only when implementing a useful
comparison is technically unavailable or disproportionately complex.

The exception must be explicit in the case metadata and must state why.

Example:

```python
"reference_exceptions": {
    "cadquery": (
        "This case qualifies a SolidCraft-specific topology mutation for which "
        "a CadQuery model would only duplicate the final mesh and would not "
        "represent the relationship being compared."
    ),
},
```

An absent model file without an explicit exception is a qualification error.

"Not added yet", "not needed", or "selective reference" are not valid
exceptions.

## 4. Parameterized Box is the baseline

The `simple-box` / **Parameterized Box** case is the canonical minimum:

```text
SCPF / SolidCraft output
PythonSCAD example + output
pyBOSL2 example + output
CadQuery example + output
```

This is the smallest case and therefore must never use an exception.

## 5. Runner contract

The qualification runner uses:

```python
DEFAULT_IMPLEMENTATIONS = ("pythonscad", "pybosl2", "cadquery")
```

For each selected case it must:

1. start from all three required implementations;
2. remove only implementations named in that case's
   `reference_exceptions`;
3. verify that every remaining implementation has
   `examples/<slug>/<implementation>/model.py`;
4. execute it;
5. export STL;
6. measure against the independent expected envelope;
7. render front/right/iso output;
8. fail qualification if a required reference is missing or invalid.

## 6. Documentation

The phrase "CadQuery is used selectively" is superseded.

Replacement rule:

> PythonSCAD, pyBOSL2 and CadQuery are required qualification references by
> default. A case may omit one only through an explicit, documented technical
> exception.

The qualification site should show the exception reason when one exists.

## 7. Migration of existing cases

At the time this rule was recorded there were 27 qualification cases.

Only these already had all three references:

```text
parametric-move
parametric-placement-pair
```

All other cases must either:

- receive a CadQuery reference and output; or
- receive an explicit technical exception with rationale.

The migration must not silently mark all existing cases as exceptions merely
to keep CI green. Straightforward geometry, parameter, occurrence and assembly
cases should receive real CadQuery implementations.

## 8. Source-of-truth rule

This policy belongs in `docs/changes/` because it changes what "qualified"
means. The runner, qualification metadata, agent reference and website must
follow this record rather than independently inventing a different selection
rule.
