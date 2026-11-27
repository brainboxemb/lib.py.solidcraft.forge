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

## 6. Consequence for the tube-clamp use case

The standalone Tube Clamp needs two physical states:

~~~text
Free:
clamp_bore = tube_d - clamp_interference

Installed:
clamp_bore = tube_d
~~~

The current released Forge/SolidCraft baseline represents that as:

~~~text
one Configuration
├── Free row
│   └── clamp_bore = tube_d - 0.4 mm
└── Installed rule
    ├── enabled = false
    └── clamp_bore = tube_d
~~~

This is not two configuration tables. It is one configuration containing both
row state and a rule.

The public Forge API may later hide these native mechanics behind
`Toggle("Installed", ...)`, but the lowering remains valid only if the saved
SolidCraft design preserves the same semantics.

For a higher-level parent where Installed differs per named row, the same native
rule is insufficient because its enabled state is not row-owned.

## 7. Configuration-only parameter dependencies

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

## 8. Backend qualification questions

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
