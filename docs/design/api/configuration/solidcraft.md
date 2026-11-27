# SolidCraft configuration model

This document records the SolidCraft backend model that constrains the Forge
configuration API design.

Baseline:

- SolidCraft application/API: **0.49.0**
- runtime image: **ghcr.io/brainboxemb/cad-solidcraft:v0.3.6**
- Forge consumer baseline: **v0.24.0**

The retained `docs/reference/solidcraft/0.49.0/commands.json` and
`describe/config.rule.json` files are the authoritative evidence used here.

## 1. One configuration surface

SolidCraft's command vocabulary is singular:

- `config.configure` — Configure;
- `config.column` — Configuration Column;
- `config.row` — Configuration Row;
- `config.activate` — Activate Configuration;
- `config.rule` — Configuration Rule;
- `config.rules` — Configuration Rules;
- `config.table` — Display Configuration Table.

These commands operate on **the configuration of the current design**. The
registry does not expose a create/select/delete-table identity and does not
expose several independent configuration owners.

The useful mental model is therefore:

~~~text
Design
└── Configuration
    ├── Columns / targets
    ├── Rows
    ├── Active row
    └── Rules
~~~

The native command name `config.table` is potentially misleading when read as
an architectural noun. It is the command that displays/returns the current
configuration state. Forge documentation should therefore use **configuration**
or **configuration list** for the public concept and mention `config.table`
only when discussing SolidCraft's native command surface.

## 2. SolidCraft command roles

The commands do not form a mandatory one-shot transaction. They are mutation
and inspection commands for the same configuration. A typical authoring flow is
nevertheless useful to understand.

### Step 1 — establish configurable targets

`config.configure` adds selected parameter, feature, material or appearance
targets to the configuration.

Its retained 0.49 contract says that when columns are added while there are no
rows yet, SolidCraft creates a **Default** row using the current values.

`config.column` is the lower-level edit command for an individual target. It
can add or delete one parameter, feature, material or appearance column.

So `config.configure` is convenience/setup for the one configuration;
`config.column` edits that same target list.

### Step 2 — define named rows

`config.row` creates or edits one named row.

A row may:

- use the current values;
- copy another row;
- set values by column key;
- be renamed;
- be reordered;
- be deleted.

Parameter cells contain expressions. Feature cells contain suppression state.
Material and appearance targets have their corresponding native values.

### Step 3 — define rules when required

`config.rule` adds, replaces, moves or deletes typed Configuration Rules.

Rules belong to the same configuration but are **orthogonal to the active row**.
The retained rule contract includes an `enabled` boolean. That enabled state is
global rule state; it is not a boolean cell stored separately in every named
row.

Current effect types include driving a parameter and driving suppression, plus
parameter restriction effects exposed by SolidCraft.

`config.rules` returns the ordered rule state together with rows and active
state for inspection.

### Step 4 — activate a row

`config.activate` selects a row by name or fixed row id and applies that row's
parameter values and suppressions.

Activation changes the design to the selected saved configuration state. Rules
then remain part of the same configuration semantics; they are not another
configuration list.

### Step 5 — inspect/display the configuration

`config.table` returns/displays the current configuration state:

- column keys;
- target descriptions;
- ordered rows;
- active row;
- whether the design still matches the active row;
- rule state;
- style state where applicable.

This is why Forge should not read `config.table` as evidence that several
tables can exist. The response is the aggregate state of the one configuration.

## 3. Current native column capabilities

SolidCraft 0.49 exposes configuration targets for:

- parameters;
- features / suppression;
- materials;
- appearances.

The retained command registry does **not** expose:

- a row-owned boolean/toggle target;
- a child-configuration-selection target.

A suppression cell is boolean, but it has feature-suppression meaning. Forge
must not reuse that target as a generic boolean just because its storage happens
to be true/false.

## 4. Configuration Rules are not row-owned booleans

A Configuration Rule has one `enabled` state.

Conceptually:

~~~text
Installed rule enabled = true
~~~

means the rule is enabled independently of whether Small, Medium or Large is the
active row.

That is different from:

~~~text
Small   -> Installed = false
Medium  -> Installed = true
Large   -> Installed = true
~~~

The second form requires boolean state owned by each row. SolidCraft 0.49 does
not expose such a target in the retained command registry.

Therefore:

- Forge may map a genuinely global Installed control to a native rule only when
  that preserves the authored meaning;
- Forge must not claim per-row Toggle support through one global rule;
- unsupported row-owned boolean semantics fail explicitly.

## 5. Named suppressible feature result

Forge-owned API probes now establish a more direct route for the Tube Clamp
case.

The SCPF probe exports one component feature as `installed` and configures it
through `Suppress(clamp.feature("installed"))`. SolidCraft 0.49 accepts the
configuration and stores:

~~~text
Free      -> suppress native feature = true
Installed -> suppress native feature = false
~~~

The probe geometry uses an extra cylindrical cutter only as a minimal way to
make the two states visibly different. That is probe transport, not the intended
mechanical model of the clamp. A production clamp should model the real
installed motion/state, for example by moving the split clamp arms/halves into
their installed position. The configuration contract only requires that this
real authored Installed history feature can be suppressed in Free and active in
Installed.

Current Forge does not propagate the exported feature name to the native
SolidCraft history name. The retained replay evidence therefore shows the
native feature as `Cylinder3` and the configuration target as
`suppress:Cylinder3`.

A separate native SolidCraft probe performs:

~~~text
timeline.rename Cylinder3 -> Installed
config.configure feature Installed
~~~

and succeeds with row cells addressed as `suppress:Installed`.

This proves that SolidCraft already supports the required human-readable native
feature name. The remaining limitation is Forge's feature-name lowering.

## 6. Position suppression result

The `configuration-position-suppression` probe tests a real named
`solid.move` feature:

~~~text
base geometry
└── ServicePosition move feature
~~~

SolidCraft 0.49 accepts that move as a normal configuration feature target:

~~~text
Normal  -> suppress:ServicePosition = true
Service -> suppress:ServicePosition = false
~~~

This proves that a positional transition can use ordinary suppression when the
transition is genuinely a CAD history feature.

That result must not be generalized to assembly occurrence placement.
`occurrence.move` is documented as changing an occurrence transform and its
reply contains `occurrence`, `transform` and `pending`; it does not expose
a timeline feature. True occurrence placement is therefore still driven
through parameter expressions, as qualified by the existing
`configuration-position` model.

Forge must distinguish:

~~~text
authored move feature
    -> suppressible feature target

occurrence placement
    -> parameter/expression-driven transform
~~~

The public API may make both feel coherent, but the SolidCraft lowering must not
pretend they are the same capability.

## 7. Consequence for the tube-clamp use case

The standalone Tube Clamp needs two physical states, but the important design
result is no longer the diameter workaround itself.

The released rule-based probe remains useful as a baseline:

~~~text
one Configuration
├── Free row
└── Installed rule
~~~

The feature probes show a more direct route when Installed is truthfully an
authored CAD history transition:

~~~text
base/free geometry
└── Installed feature
    ├── suppressed -> Free
    └── active     -> Installed
~~~

The actual production feature should model the real mechanical transition, not
merely swap a bore diameter.

A generic Toggle should therefore not be introduced merely to obtain a checkbox
when the state is already a real suppressible feature. Generic state remains a
separate problem only where no truthful history feature exists.

For a higher-level design where one global Installed intent must drive several
independent child-owned Installed features, the direct SolidCraft route is now
known: a timeline folder can group and suppress several contiguous features,
but that folder is **not** a configuration feature target. The detailed result
is recorded below.

## 8. Global state fan-out result

The `configuration-installed-fanout` probe qualifies one important native
SolidCraft transport pattern for the HUB75-style use case.

The saved design contains:

~~~text
rows:
    Small
    Large

one independent native rule:
    Installed [off/on]

private transport:
    installed_offset

consumers:
    LeftInstalledMotion  <- installed_offset
    RightInstalledMotion <- installed_offset
~~~

When the native Installed rule is enabled it drives only the shared
`installed_offset` parameter. Both authored move features already depend on
that parameter, so one UI control changes both participants.

This proves that SolidCraft can preserve one global state independently from
the active Small/Large row while several model operations react to it.

It does **not** make `ConfigRule`, `Always` or `DriveParameter` semantic
Forge concepts. They describe this backend's transport. A generic Forge state
may lower to this pattern on SolidCraft while another backend uses a different
mechanism.

The private driver parameter is likewise not public model intent and must not
appear in engine-neutral configuration IR.

## 9. Single-feature multi-object result

The `configuration-installed-single-feature` probe tests the simplest native
history representation of Installed: one real feature acts on several bodies.

The probe creates two separate coupler bodies and one `solid.move` feature
named `Installed` whose `bodies` input contains both couplers.

SolidCraft 0.49 accepts that one feature as one configuration suppression
target. Two configuration semantics were tested separately.

### Row-owned suppression

The current direct probe stores `suppress:Installed` in the Small/Large rows
with no Configuration Rule. That probe passed on CI run
**46018699506** (run 971).

This proves a normal configured feature column is enough when Installed is
genuinely a value of each named row.

### Independent Installed control

An earlier variant kept the same single `Installed` feature suppressed in the
rows and used one independently enabled native Configuration Rule whose
`drive_suppression` effect targets that feature.

That variant passed on runs **959** and **966**.

This proves SolidCraft can also preserve:

~~~text
active row: Small | Large

Installed: off | on
    |
    v
one real Installed history feature
    |
    +--> body A
    +--> body B
~~~

without changing the active row.

The rule is a SolidCraft lowering mechanism. It does not justify public
`ConfigRule`, `Always` or `DriveParameter` objects in Forge.

The important stable conclusion is the **history** model: when the Installed
transition is truthfully one native multi-object CAD operation, one real
Installed feature is sufficient. The configuration lowering depends on whether
Installed is row-owned or independently switchable.

## 10. Timeline-folder suppression result

The `configuration-installed-group` probe tests the most direct mapping for
the desired model-level Installed behavior:

~~~text
Installed
├── LeftInstalled
└── RightInstalled
~~~

SolidCraft 0.49 accepts this as one timeline folder when the two history
features form one contiguous run. The positive baseline passed on CI run
**46016413339** (run 943), and the saved design contains:

~~~text
Installed folder id 5
├── feature 3: LeftInstalled
└── feature 4: RightInstalled
~~~

SolidCraft can also suppress that folder as one manual history operation through
`timeline.suppress(groups=[5])`.

The configuration boundary is different. Two focused runtime attempts establish
that the folder is not a native configuration target:

- run **46016605146** (run 944) used folder id 5 as one
  `drive_suppression` target; SolidCraft rejected it because the rule target
  is not configured;
- run **46016766466** (run 945) tried
  `config.configure(features=["Installed"])`; SolidCraft rejected it with
  `no feature 'Installed'`.

Therefore SolidCraft 0.49 treats timeline folders and configuration features as
different kinds of object:

~~~text
timeline folder
    -> may contain several contiguous history features
    -> may be manually suppressed as a group
    -> cannot be a configuration feature target

configuration feature target
    -> one actual history feature
~~~

This closes the direct “one configuration checkbox suppresses one folder of
many Installed features” route for SolidCraft 0.49.

The previously qualified shared-driver fan-out remains a working SolidCraft
backend pattern for one independent Installed control affecting several
operations. That transport must not dictate the Forge authoring API.

## 11. Configuration-only parameter dependencies

The executable probe exposed another SolidCraft/Forge boundary.

A Forge Parameter referenced only by a configuration row or rule effect is not
automatically materialized as a native SolidCraft Parameter by the current
compiler path.

The first probe attempted:

~~~text
clamp_bore = tube_d - clamp_interference
~~~

where `clamp_interference` existed as Forge model state but had no independent
geometry dependency. Replay then lacked that native parameter and SolidCraft
rejected the expression.

The current baseline probe uses the literal `0.4 mm` only to isolate native
configuration behavior.

That workaround must **not** become public API policy. A parameter referenced by
configuration is a real semantic dependency and Forge IR/compiler state must
retain it even when ordinary geometry does not otherwise read it.

## 12. Backend qualification questions

For each proposed Forge configuration capability, qualify these questions
against the saved SolidCraft design:

1. Does it remain inside the single native configuration definition?
2. Does save/reopen preserve the authored state?
3. Does row switching preserve row-owned values?
4. Does rule enable/disable preserve genuinely global rule state?
5. Are all expression dependencies retained as native parameters?
6. Does the backend preserve meaning without fake numeric flags, duplicated
   bodies or Python reruns?

If the answer is no, the SolidCraft backend must fail explicitly for that
semantic capability.
