# Post-Extrude geometry edits as suppressible configuration history

Status: Proposed  
Tracking: #669  
Motivating consumer: brainboxemb/2026-011-02.cad.solidcraft#281

## Required history

The HUB75 clamp must use the same history principle already qualified for
position changes:

~~~text
base geometry
    |
    +-- later CAD history operation      [suppressible]
~~~

For the clamp:

~~~text
Free profile
    |
    +-- Extrude -> physical Free clamp
    |
    +-- Installed geometry adjustment    [suppressed in Free]
~~~

The Installed adjustment is one real later CAD history feature.

## Configuration model

There is no Free/Installed row axis and no Configuration Rule.

Use one ordinary configuration row and configure the real Installed feature
directly:

~~~text
Configuration     Suppress: Installed
Normal                    [x]
~~~

The checkbox is the native suppression cell for the feature.

~~~text
checked     -> Installed feature suppressed -> Free geometry
unchecked   -> Installed feature active     -> Installed geometry
~~~

If another row axis exists later, for example Small / Medium / Large, the same
suppression column is simply present on those rows. No Cartesian row expansion
and no rule/effect layer is required.

Conceptually the Forge authoring remains the existing configuration contract:

~~~python
with feature("installed", suppressed=True) as installed:
    body = body.<generic_post_extrude_edit>(...)

body.configure(
    active="Normal",
    columns=(installed,),
    rows={
        "Normal": (True,),
    },
)
~~~

The boolean is the direct suppression cell:

~~~text
True   -> suppressed
False  -> active
~~~

There is no drive_suppression, condition, effect, rule id or secondary state object.

## Existing evidence

`configuration-position-suppression` already proves that a later native history
feature can be configured through suppression.

The first #669 qualification run, 46166188263, then separated two geometry
cases against SolidCraft 0.50.0.

### Source Sketch edit

`sketch.edit` + `sketch.move_points` after an Extrude does not create a later
history feature.

The saved design still contains only:

~~~text
1  FreeProfile   sketch
2  ClampExtrude  extrude
~~~

The edited coordinates are written back into `FreeProfile` and downstream
geometry rebuilds. Therefore this cannot be the independently suppressible
Installed step.

### Post-Extrude solid edit

A real `solid.offset_face` after the Extrude is stored as:

~~~text
1  FreeProfile   sketch
2  ClampExtrude  extrude
3  Installed     offset_face
~~~

That is the correct history shape. It can be targeted directly by the normal
suppression column.

`offset_face` is only evidence for history behavior. It is not accepted as the
HUB75 clamp operation because a single face offset does not preserve the
required 2.0 mm wall while opening the clamp.

## Remaining geometry question

Configuration is no longer an open problem.

The only remaining design question is which generic post-Extrude solid-edit
operation can express the clamp's Installed geometry as one normal history
feature.

Forge must:

1. keep `feature(...)` and `.configure(...)` unchanged;
2. identify the smallest generic geometry operation that produces the required
   Installed result;
3. expose that operation as a normal Shape modifier if SolidCraft already owns
   it;
4. keep semantic selection replay-bound;
5. require the operation to produce exactly one native history feature.

Do not solve the geometry gap with:

- another parameter row;
- a Configuration Rule;
- drive_suppression;
- a clamp-specific flex abstraction;
- an oversized bore cut;
- hidden multiple history operations presented as one feature.

## Newer SolidCraft candidate

Current SolidCraft `main` contains `solid.transform_face`, a normal direct
modelling feature that translates/rotates one face and extends/trims adjacent
faces.

That command is not in the pinned SolidCraft 0.50.0 runtime used by Forge
v0.27.0, so it is only a candidate for later qualification. It must not be
added to Forge until available in the versioned runtime/reference and proven
suitable for the clamp.

## Acceptance

This change is accepted when:

1. one-row direct feature suppression is qualified;
2. the saved design contains exactly one configurable Installed history feature;
3. no rule/effect/drive mechanism is involved;
4. the geometry operation chosen for the clamp is generic and produces one
   native history feature;
5. the downstream clamp can use that feature directly as its suppression column.