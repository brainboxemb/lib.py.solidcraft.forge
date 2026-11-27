# Forge design

## Purpose

Forge is a clean consumer of the corrected `template.cad.library` architecture.

```text
cadlib/                     public scpf package
models/                     physical CAD model owners
modules/
  ci/                       selection/runtime orchestration
  builder-*                 standard CAD adapters
  solidcraft-reference/     canonical runtime command-registry evidence
  verification/             local generic cad_verification
  preview/                  deterministic presentation rendering
  build/                    durable generated-output publication
  release/                  stable release-evidence qualification
  pages/                    Hugo projection/publication
site/                       Hugo/Hextra source
docs/                       repository contract and migration record
```

## Physical model boundary

The model owner is the same concept used by `template.cad.model-project`.

```text
models/simple-box/
  ci.yml
  model.yml
  scpf/model.py
  cadquery/model.py
  build123d/model.py
  pythonscad/model.py
  pybosl2/model.py
  verification/geometry.json
```

CI selects `simple-box` once. Its `ci.yml` expands the implementations required by that model. The build branch groups all implementation evidence below `models/simple-box/`.

`model.yml.purpose` is a list-like policy field and may contain `example`, `verification`, or both.

## SCPF boundary

The template role `cadlib` is the actual `scpf` package. Forge-specific compilation is consumer-owned logic.

The intended Forge compiler path is:

```text
models/<id>/scpf/model.py
        ↓ one SCPF evaluation / semantic normalization
typed engine-neutral Forge ModelIR
        ├── SolidCraft lowering -> SolidCraft commands/replay
        └── Mitcad lowering     -> Mitcad commands/replay
```

SCPF is the current authoring frontend, while `ModelIR` is the compiler
contract. Native backends lower that semantic representation independently;
they do not re-interpret model source or raw portable `Shape.data`.

Reference implementations use the standard PythonSCAD, pyBOSL2, CadQuery and build123d builders directly inside the same physical owner.

Native feature inputs keep native identity where SolidCraft provides it. For
example, an associative sheet fold stores the finished one-line Sketch Shape in
the Forge feature tree. Lowering emits that Sketch as
`sketch.create -> sketch.line -> sketch.finish`, then emits
`sheet.fold {sketch, curve}`. The older fixed two-point form remains a
compatibility path and lowers to `sheet.fold.points`. This avoids baking a
symbolically driven bend line into coordinates that stop following later
parameter edits.

## Symbolic CAD math boundary

Forge exposes non-linear native expression intent through the `cadmath`
namespace rather than shadowing Python built-ins or exposing raw SolidCraft
expression strings:

```python
mid_g = cadmath.min(self.mid_round, self.mid_wall / 2 - 0.05)
mid_tip = cadmath.sqrt(
    (self.mid_outer_r - mid_g) ** 2
    - (self.mid_outer_r - self.mid_wall + mid_g) ** 2
)
lane = cadmath.round(self.mid_z / 2 / self.ref_lane_grid) * self.ref_lane_grid
angle = -cadmath.atan((self.ref_d - self.ref_tip_d) / (2 * self.ref_tip_h))
```

`cadmath.min/max/sqrt/abs/round/floor/atan` return ordinary numbers when all
inputs are numeric and a typed `Expression` when any input is symbolic.
Expression arithmetic retains every contributing `Parameter`; command lowering
emits the native SolidCraft expression and the existing dependency audit sees
the same source parameters. `cadmath.atan` follows SolidCraft CAD semantics and
evaluates in degrees.

This is expression authoring, not a general Python symbolic algebra system.
Forge only exposes operations that have a qualified native SolidCraft spelling
and current-value evaluation.

## Native multi-profile Sketch extrusion boundary

Standalone Sketch compilation preserves one authored Sketch even when it
contains several closed loops. Every supported profile is lowered between the
same `sketch.create` / `sketch.finish` pair; Forge does not manufacture one
Sketch per loop.

Extrusion keeps SolidCraft's native region model. For ambiguous/nested loops,
consumer code uses the existing typed selection:

```python
with Sketch(name="Tube profile", plane="XY") as profile:
    Circle2D(d=outer_diameter)
    Circle2D(d=inner_diameter)

tube = profile.extrude(
    length,
    profiles=[(4.5, 0)],
    exact_regions=True,
)
```

The fixed point is authoring intent only. SolidCraft resolves the exact region
and retains the surrounding native curves so the selected annulus can survive
saved-design diameter changes. No native profile index or generated curve id is
part of the public API.

The compiler's base-shape metadata remains intentionally conservative for
multi-profile Sketches: profile-specific edge selectors such as
`Edges.from_profile(...)` continue to require their already-qualified single
Polygon2D extrusion. Multi-profile support is an extrusion-region capability,
not a blanket expansion of every Sketch consumer. `Sketch.revolve()` retains
its one-closed-profile limit.

## Native axis-line and shifted revolve boundary

`AxisLine(direction, origin=...)` is the public typed line contract for native
features that need a fixed direction through an explicit, optionally symbolic
XYZ point. Principal `Axis.X/Y/Z` remains the concise world-origin form.

For Sketch revolve, the first shifted-axis contract is deliberately bounded:
- one standalone unrotated XY/XZ/YZ Sketch;
- optional symbolic standalone plane offset;
- one closed profile;
- `AxisLine` direction lies in that plane;
- the axis origin's normal coordinate matches the Sketch plane offset;
- lowering emits SolidCraft `solid.revolve.axis = {origin, dir}` directly.

The Shape returned by `Sketch.revolve(...)` remains the authored feature
identity. When used as `body - revolve`, lowering emits one native
`solid.revolve(operation="cut")`; `Suppress(revolve)` therefore binds that
one history feature rather than an approximation made from multiple primitives.

`AxisLine` is also accepted by circular-pattern axis authoring so shifted axis
intent has one public vocabulary. Topology-selected/construction axes and
rotated Sketch frames remain separate future contracts.

## Native two-distance chamfer boundary

Chamfer remains one Shape feature and one SolidCraft `solid.chamfer` history
operation. The public form extends the existing equal-distance API without
introducing a second edge-selection path:

```python
body.chamfer(
    0.18,
    distance2=0.65,
    flip=True,
    edges=Edges.from_profile("top"),
)
```

Internally the existing edge-selection intent stays in the same Shape-data
position used by current Forge code. Optional `distance2` and `flip` are
additional feature intent. Lowering always emits `distance`; it emits
`distance2` only when authored and emits `flip` only when true. Therefore
an existing equal-distance call keeps the same generated command document.

SolidCraft owns adjacent-face ordering. `flip=True` maps directly to native
`solid.chamfer.flip`; Forge does not infer a new face vocabulary from the
selected edge. Both distance expressions preserve normal parameter
dependencies. Named profile/vertex, cardinal Box, face-boundary and explicit
edge picks all continue through the existing resolver before the same chamfer
command is emitted.

The first qualification uses a named top segment from an XZ Polygon2D
extrusion. This deliberately proves asymmetric chamfer intent composes with the
existing semantic profile-edge selector and remains one native ChamferFeature
after saved-design parameter changes.

## Native configuration-table boundary

Configuration is final design intent rather than a Python model variant. The
public authoring boundary is:

```python
Configure(design, active=..., columns=(...), rows={...})
```

The configured `design` may be a single `Shape`, one component occurrence or
an `Assembly`. `Param(...)` points at an existing native model parameter, so
the same column type can drive dimensions, occurrence `Placement`, attachment
offsets and other native associative dependencies. A parameter explicitly published from a reusable child component is one of those native dependencies: when the parent passes one shared Parameter into the child, a root configuration table may address that parent parameter and every occurrence using the same component definition follows it. `Suppress(feature)` points
at the exact Forge-authored feature object; consumer code never names or predicts
SolidCraft history ids.

Lowering is deliberately two-stage:

```text
Forge configuration intent
        ↓
compile normal Shape / component / Assembly design
        ↓
bind replay-returned native feature names and configuration row ids
        ↓
config.configure / config.row / config.activate / config.table
        ↓
saved SolidCraft .sc owns editable configs + native row identities
```

Forge assigns a deterministic replay row reference from each authored row name,
binds it to the actual native row id returned by SolidCraft and activates by
that bound id. Reordering rows therefore does not change Forge's logical row
reference. SolidCraft persists its own `row_identities` map in the saved
document. The SolidCraft command API does not accept caller-chosen native row
ids, so Forge does not patch or predict them.

Configuration Rules are authored on that same final table:

```python
Configure(
    assembly,
    active="Medium",
    columns=(Param(self.frame_width), Param(self.fit_diameter)),
    rows={
        "Small": ("60 mm", "20.4 mm"),
        "Medium": ("80 mm", "20.4 mm"),
        "Large": ("100 mm", "20.4 mm"),
    },
    rules=(
        ConfigRule(
            "installed",
            "Installed",
            enabled=True,
            condition=Always(),
            effect=DriveParameter(self.fit_diameter, self.tube_d),
        ),
    ),
)
```

The first public rule slice deliberately exposes only typed `Always()` and
`DriveParameter(...)` intent. Lowering emits native `config.rule` after row
authoring and before `config.activate`. The rule's `enabled` field is the
SolidCraft Configuration Rules checkbox; Forge does not manufacture a boolean
user parameter. A drive target must already be a `Param(...)` column, so
disabling the rule lets SolidCraft restore the selected row's stored value.
Rules therefore remain orthogonal to Small / Medium / Large rather than
expanding those rows into a Cartesian state table.

`Configure` never rewrites Python model structure for each row. A row may only
change native configuration columns. Whole-component presence, alternate
attachment graphs and arbitrary Python branching therefore require a separate
native contract rather than being hidden behind configuration syntax.

Native material and appearance columns also exist in SolidCraft's configuration
model. They are intentionally not exposed by #216 until a typed Forge authoring
contract and verification case exist for them.

## Configuration verification cases

Configuration qualification is Forge-owned and independent of downstream
consumer repositories. The verification catalog has its own
**Configurations** section and uses focused cases:

| Case | Contract proved |
| --- | --- |
| `configuration-table` | named rows, active row, multiple parameter columns, two independent feature-suppression columns, saved native table and row switching |
| `configuration-position` | one configuration table around a complete Assembly, with parameter-driven occurrence positions for Front, Below and Service |
| `configuration-installed-state` | two reusable flexible-fit child occurrences share one published fit parameter; Small/Medium/Large remains the row axis while an independent native Installed rule drives or releases that parameter after saving |
| replay row identity | Forge-generated name-stable row references bind to SolidCraft-returned native row ids; activation uses the bound id |
| saved-design switching | rows are switched after reopening the generated `.sc`, proving configurations are native document state rather than Python presets |

The use-case boundary is intentional:

| Use case | #216 public contract |
| --- | --- |
| product sizes / dimensional presets | `Param(...)` |
| front/below/service assembly positions | `Param(...)` driving associative `Placement` |
| optional authored feature | `Suppress(feature)` |
| dimensions plus suppression in one row | supported by the same table |
| parent size table + published reusable-child parameter | supported by the same `Param(...)` contract; shared child occurrences follow one parent native parameter |
| flexible-fit free/mounted state | use `Free` / `Installed` rows when fit is the only axis; when size rows already exist, use one independent native `Installed` `ConfigRule` driving the same `Param(...)` target |
| material or appearance variants | native SolidCraft supports them, but Forge waits for a typed, separately verified column contract |
| whole component present/absent | not silently mapped to feature suppression |
| alternate attachment/joint graph | not a configuration cell; requires explicit relationship authoring |
| arbitrary Python branches per row | rejected as a configuration-table substitute |

A suppression reference must be an actual Forge-authored feature identity
available to the configured design. Direct Shape-owned configuration keeps the
existing exact-object `Suppress(feature)` contract.

Reusable child definitions add one explicit interface layer rather than exposing
SolidCraft history names. Inside the child, the author marks the exact applied
Shape with `feature.export_feature("panel_pin")`. The final component definition
retains that export as Forge metadata. Parent code asks an occurrence for
`child.feature("panel_pin")`; the returned typed reference contains the reusable
definition identity plus the component-local export name, not an occurrence id
and not a native feature id.

During Assembly configuration lowering, Forge resolves that reference against
the canonical compiled component definition, obtains the exact exported Shape
from that definition, compiles the history prefix and binds the replay-returned
native feature name in the same way as an ordinary `Suppress(feature)` column.
Because the reference is definition-level, two separately constructed
occurrences and `.copy()` occurrences of the same reusable definition all point
at the same native child history. Missing exports, missing definitions and
ambiguous/duplicate native targets fail explicitly.

For flexible parts, `Free` and `Installed` name physical/model states:
`Free` is the uninstalled shape used for manufacturing or print output;
`Installed` is the mounted working shape. A render may choose to show
`Installed`, but rendering is presentation policy and does not redefine the
configuration. The current generic preview consumes the built artifact, so an
owner whose active row is `Free` publishes a Free-state manufacturing preview
unless a future presentation feature explicitly selects another saved row.

The HUB75 display and frame-coupler models remain downstream consumers. They are
useful adoption tests after a Forge release, but they do not define or special
case the public API.

## Native revolute-relationship boundary

Revolute motion stays inside the existing occurrence-attachment model. A
consumer selects the same parent/child attachment references used by rigid and
planar relationships, then explicitly requests `kind="revolute"`.

The lowering path is:

```text
Occurrence.attach(kind="revolute", value=60, limits=(0, 180))
        ↓
Attachment(kind/value/limits/flip/name)
        ↓ existing Anchor / AnchorFrame / AnchorTopology resolution
joint.create(type="revolute", values=[60], limits=[[0, 180]])
        ↓
native SolidCraft joint solver
```

Forge does not rotate the moving occurrence to imitate a hinge. The occurrence
gets only the seed placement needed to bring the two authored joint origins
together; SolidCraft stores and solves the revolute degree of freedom. Existing
calls without `kind` keep the established automatic rigid/planar lowering.

The first public moving-joint contract is deliberately narrow: fixed numeric
degree value/limits plus native `flip` and `name`. Slider, cylindrical,
pin-slot and ball authoring wait for demonstrated consumers rather than sharing
an unqualified generic abstraction.

## Display-appearance boundary

Display color is intentionally separate from physical material authoring.

```text
Shape.with_appearance("#FFD21A")
        ↓
Shape("appearance_assignment", ...)
        ↓
appearance.assign(bodies=[final_body], color="#FFD21A")
        ↓
native SolidCraft appearance chain
```

Forge does not create a synthetic material merely to carry display color.
`with_material(...)` remains the physical-material path with density/BOM
semantics; `with_appearance(...)` changes only visual presentation.

The initial contract is deliberately narrow: one opaque fixed body-wide color.
Face-level looks, library recipes, opacity and PBR controls wait for concrete
consumers.

## Native topology-selection boundary

Forge uses one world-cardinal `Faces` vocabulary for within-component surface
intent. `Edges.from_faces(...)` derives an edge selection from that same
surface intent instead of introducing a chamfer-specific selector language.

The lowering path is replay-driven:

```text
Faces.FRONT / Faces.BACK
        ↓
model.faces(body=...)
        ↓ bind native face record returned by SolidCraft
model.edges(body=...)
        ↓ select edges lying on that returned planar face
{body, index} edge references
        ↓
solid.chamfer / solid.fillet
```

Forge never predicts native face or edge ids. Replay bindings carry the
SolidCraft records returned in the current run, and the final modify feature
receives native `{body, index}` edge references. Multiple faces accumulate and
deduplicate those returned edge references.

The cardinal convention is fixed in world axes: TOP/BOTTOM are +/-Z,
LEFT/RIGHT are -/+X and FRONT/BACK are -/+Y. An XZ-authored profile is extruded
along Y, so its two broad end faces are FRONT and BACK regardless of camera
orientation.

`shell()` resolves its `Faces` through the same native `model.faces`
query and passes the returned native face names to `solid.shell`.
`Shape.on()` accepts the same six `Faces` as public intent. Existing
TOP/BOTTOM placement remains qualified; a side-face placement reaches the
shared placement lowering and reports the explicit native topology limitation
until that backend path is separately qualified.

Legacy selectors (`Edges.VERTICAL`, direction-pair Box edges,
`Edges.from_profile()`, `Edges.from_vertices()`, and explicit XYZ picks)
remain compatibility paths.

## Native component drawing boundary

Component drawings are Assembly-owned presentation state. A reusable component
definition remains geometry/feature intent and does not own a drawing, because
one definition may have many physical occurrences and many downstream drawing
layouts.

The public authoring objects are deliberately small intent records:

- `DrawingView(at=..., scale=..., visual_style=...)` controls one native front/top/right/iso view; `visual_style="shaded"` is the qualified pictorial override while omission keeps SolidCraft's normal line presentation;
- `DrawingDimension.linear(...)` resolves two model corners/points;
- `DrawingDimension.faces(...)` resolves two parallel planar faces and is the
  stable overall-size form for filleted parts;
- `DrawingDimension.radial(...)` resolves one circular edge and may request a
  diameter/callout override;
- `DrawingNote(...)` authors native sheet text;
- `DrawingRevision(...)` authors one native revision row;
- drawing `properties={...}` and `title_block={...}` populate native drawing
  metadata/title cells;
- `title_block_style="compact"` lowers to native `drawing.sheet.set(title_block="compact")`, using SolidCraft's compact 49 mm block rather than Forge-rendered replacement graphics. The builder confirms the replayed sheet reports a 49 mm native title-block height before publishing drawing artifacts.

Forge lowers that intent to native `drawing.create`, `drawing.sheet.set`,
`drawing.properties.set`, `drawing.revision.add`,
`drawing.view.standard`, `drawing.view.edit`,
`drawing.dimension.add`, `drawing.note.add`, `drawing.inspect` and
`drawing.close`. It does not draw dimension lines, leaders, notes or a title
block itself.

The default path still delegates standard view grouping and initial fitted scale
to SolidCraft. A consumer may then author explicit paper positions and view
scales through `DrawingView`; independent projected-view scale automatically
unlinks that native projected view. A consumer may also request the qualified
native `visual_style="shaded"` on an individual view, allowing normal line
orthographics with a shaded isometric without Forge rendering the picture
itself. A4 is the default and the first sheet is explicitly landscape. A3
remains an explicit native template choice.

All component, occurrence, drawing, drawing-source, sheet, view, dimension and
note identities come from replay-bound SolidCraft command results. Forge never
predicts browser names or native ids. Model-space dimension picks remain input
intent only; SolidCraft must resolve them to saved native topology or reject
them. This deliberately exposes invalid picks (for example a filleted-away
corner or a point inside a through-hole) instead of silently manufacturing a
measurement.

The replay document declares safe implementation-relative PDF, PNG and native
inspection JSON paths plus the replay-bound drawing/sheet/orientation variables.
After native replay, `builder-scpf` takes the last fully-authored
`drawing.inspect` result for each declared drawing and validates it against
the compiled authoring intent: landscape orientation, four standard views,
dimension/note counts, drawing properties, title-block overrides and revision
fields. That exact inspection is retained as `drawings/<name>.json`.

The builder then reopens the saved `model.sc`, opens the replay-bound native
drawing id and uses SolidCraft `drawing.export` for both the vector PDF and
the exact replay-bound sheet PNG at 144 dpi. Neither artifact is reconstructed
by Python.

Visual sheet qualification is separate from drawing production. The generic
`image-regression` verifier consumes the generated PNG and compares it with an
approved encoded baseline using the released `cad_verification` image
comparison primitives. It neither invokes SolidCraft nor understands drawing
semantics. This catches layout regressions that a structure-only inspection
would miss.

The `sample-plate-drawing` owner is the Forge-owned consumer simulation. It
uses only the public API to author explicit view layout/scale, a shaded native
isometric alongside line orthographics, overall face-to-face dimensions,
radial callouts, notes, drawing properties,
title-block overrides and one revision row. The owner therefore proves the
same class of authoring an external CAD model such as Wall Hook will need,
without importing or modifying that downstream repository.

The pinned SolidCraft 0.49 registry does not expose native centre-mark or
centre-line authoring. Forge therefore does not fake those graphics. Balloons
and parts lists are also outside the qualified consumer slice until a native
backend path exists and a real consumer requires them.

For a component selected from a larger Assembly, SolidCraft currently computes
the standard view group's fitted scale before Forge narrows the base views to
that occurrence subtree. Projected top/right views inherit the main view source.
The result remains native and safe, but the scale can be conservative for a
small component inside a much larger Assembly; explicit `DrawingView(scale=...)`
is the consumer override.

Drawing presentation is projected from the same owner/evidence architecture as
other examples. The `sample-plate-drawing` owner has
`purpose: [example, verification]`: Examples teaches the workflow, while the
Drawings verification section exposes the same native evidence. Pages discovers
implementation-local `drawings/*.pdf` plus sibling PNG/JSON evidence. Pages
loads only the static PNG preview and exposes explicit PDF open/download links;
generated drawing artifacts remain on `build/<scope>` and are never copied
into `gh-pages`.

## SolidCraft command-reference boundary

The canonical SolidCraft command registry is a Forge-owned engineering
reference, not a CAD model and not generated Pages content.

```text
root ci.yml immutable SolidCraft runtime pin
        ↓ modules/solidcraft-reference
solidcraft-cli --version + commands
targeted engine.describe for typed contracts that gate Forge API design
        ↓
docs/reference/solidcraft/<version>/
  commands.json
  commands.md
  describe/<command-id>.json
  SOURCE.md
```

`modules/solidcraft-reference` validates registry completeness, captures and
normalizes the exact runtime registry, renders the human catalog/provenance, and
compares the checked snapshot back to the same immutable runtime. When a typed
native contract gates Forge API design, the same module may additionally retain
the exact read-only `engine.describe` result for that command below
`describe/<command-id>.json`. Those targeted schemas are evidence, not a
second hand-maintained native API catalog, and are compared byte-semantically
as JSON against the same root-pinned immutable runtime. Its item watch includes
`docs/reference/solidcraft/**`, so reference changes select their own verifier.
Historical version directories remain immutable evidence.

## Runtime graph

Reference implementations build and verify in one `reference` container batch. SCPF-generated SolidCraft commands execute in `solidcraft`; their STL then enters the `reference` verification role.

The scheduler understands capabilities and runtime dependencies, not Forge engine names.

## Durable output

```text
build/<scope>/models/<owner>/
  result.json
  source.json
  model.stl
  model.png
  drawings/
    <drawing>.pdf
    <drawing>.png
    <drawing>.json
  scpf/
  cadquery/
  build123d/
  ...
```

Owner-level canonical artifacts come from the configured primary implementation. Each implementation retains its own result and verification evidence.

Pages reads the durable scope and links generated files on the build branch. Generated CAD artifacts are not copied into `gh-pages`.

Workflow roles follow `template.cad.library`: pull requests run only the central `ci` qualification job; permanent `dev`/`main`/`exp` events run one `build` job that executes selected project work and publishes the durable scope. After publication that build dispatches the independent `pages.yml` workflow and finishes without waiting for Pages.

The schema-2 `build-plan.json` also records whether the independent `cadlib` owner was selected and qualified. Stable release qualification requires `library: true`, a full build, all active owners selected, and owner-local successful evidence whose source provenance matches the exact release commit.

## Experimental development line

Forge consumes the qualified optional `exp` contract from `template.cad.library`. `exp` is a permanent integration branch for research that must not destabilize normal `dev` or stable `main`. Temporary work branches may squash into `exp`; `dev -> exp` synchronization and completed `exp -> dev` integration use merge commits with full PR qualification. `exp -> main` and releases from `exp` are rejected.

Permanent experimental builds keep durable evidence under `build/exp/`. Pages assembles `/exp/` only while the branch exists and marks that projection as experimental. The same single serialized Pages publication continues to own the complete `gh-pages` tree.

## Manufacturing-output visual boundary

Some native CAD capabilities intentionally do not alter the display B-rep.
For those cases, visual verification follows the authoritative manufacturing
representation. `sheet.perforate` is the first explicit example: SolidCraft
stores the field in flat-pattern/DXF/volume semantics while the regular model
snapshot remains a plain sheet.

The `solidcraft-sheet-flat-pattern-visual` adapter opens the saved native
`.sc`, exports `sheet.export_dxf`, reads native `CIRCLE` entities on layer
`PERFORATION`, compares centres/diameters to the approved owner contract and
retains DXF plus Actual/Goal/Overlay SVGs. Pages projects only these durable
artifacts and never executes CAD.

## Verification evidence boundary

Verification evidence is selected from the contract a physical owner is meant
to prove rather than from one repository-wide screenshot rule.

- visible geometry/state combines deterministic review views with an approved
  expectation and structural checks where a wrong topology/shape could still
  look superficially plausible;
- native feature/history behavior uses saved-design mutation or inspection so a
  successful replay is not mistaken for proof of editability or stored intent;
- manufacturing-only behavior uses its authoritative exported/manufacturing
  representation instead of altering the display B-rep for verification;
- negative or runtime-divergence behavior records the expected failure/result
  explicitly rather than inferring it from a missing output.

Model-specific expectations remain owner-local below `models/<id>/verification`.
Generic adapters in `modules/verification` consume those expectations and
produce durable evidence below `build/<scope>/models/**`. Pages only projects
that retained evidence. `docs/verification/evidence-audit.md` records the
current owner-by-owner classification; concrete missing evidence is repaired in
separate owner-focused follow-up issues rather than inside the audit itself.

## Pages projection

Verification detail pages identify their role with **What this verifies** and
collapse detailed measured checks by default using the same
`cad-collapsible` interaction as generated command sequences. Owner-local
`page.md` remains **Engineering explanation** and is shown directly after the
primary Forge/source code, before generated commands and detailed evidence.

These behaviors are owned generically by `template.cad.library#82` and
`template.cad.library#84`; Forge adopts them and only owns case-specific
explanation such as `models/configuration-position/page.md`.


`models/<id>/` remains the single physical owner. Pages creates views from that owner according to `model.yml.purpose`:

- `example` → `/examples/<id>/`;
- `verification` → `/verification/<id>/`;
- `[example, verification]` → both routes.

The two routes are presentation views over the same owner and durable `build/<scope>/models/<id>/` evidence. They are not separate model owners and do not duplicate CAD artifacts into `gh-pages`.

The reusable Hextra model presentation is consumed from the accepted `template.cad.library` design: expected setup, featured native/primary result, primary source and generated commands, independent reference source/result pairs, image/check overviews and raw verification evidence.

The Forge homepage follows the generated homepage contract established by
`template.cad.library#63`. Repository-owned `site/home.yml` declares the
ordered hero, flow, navigation and catalogue blocks. Pages validates that
source with `homepage.py`, resolves Forge-owned generated values from
`landing_metadata()`, and writes temporary `data/home.json`. Hugo then
renders that manifest with the Forge-specific presentation classes in
`site/layouts/home.html`. The layout owns structure and styling only; Forge
copy, routes and external destinations are not hardcoded there. The SolidCraft
model website is therefore one normal generated navigation destination rather
than a template exception.

Verification keeps its Forge-owned presentation taxonomy in `docs/verification/sections.yml`. During Pages preparation that declaration is validated, sorted by section priority and projected into a temporary Hugo resource catalogue. Every owner projected to Verification must name one known section through `model.yml.section`; the Verification list renders those sections in declared order and sorts the model cards inside each section by model priority. This is presentation metadata only and does not create additional model owners or CAD build scopes.

Forge-specific documentation is projected separately:

```text
docs/guide/                         authored Guide chapters
docs/cheatsheet.yml                authored Cheatsheet data
docs/api-reference.json            retained rich public API reference contract
docs/api.md                        API design contract
docs/verification/                 coverage + joint-anatomy authored sources
docs/pages-parity.json             fixed historical route/content gate
        ↓ modules/pages
site/content/...                    temporary Hugo projection
        ↓ Hugo
rendered Pages
```

`api_reference.py` uses Python AST to validate the retained public reference contract against `cadlib/src/scpf` without importing the package. `verification_special.py` reads authored coverage/joint documentation and durable build evidence without executing CAD. The final Pages verifier consumes `docs/pages-parity.json` so route and identifying-content regressions fail CI before publication.

## Migration comparison

Before moving historical code, classify it as:
- **SCPF product behavior** → `cadlib/`;
- **physical-model expectation** → `models/<id>/`;
- **generic verification** → `modules/verification/`;
- **generic runtime/builder behavior** → standard module;
- **presentation** → Hugo/Pages;
- **obsolete orchestration/duplication** → remove after parity.

Expand migration only after accepted A/B evidence: 1 → 5 → 10 → remaining graph.

## Central PR CI freshness in merge policy

Forge consumes the generic stable template rule that merge policy validates
the newest `pull_request` run of `.github/workflows/ci.yml` for the exact
head SHA and pull request. GitHub can re-associate historical check-runs when
a replacement PR reuses a permanent-branch head, so old red checks must not
permanently poison a later successful qualification.

The newest matching run remains fail-closed: pending blocks, failure blocks,
and no current-PR CI blocks. Permanent `workflow_dispatch` runs are not PR
qualification. Forge owns no consumer-specific variant of this rule.

## Reviewed permanent-branch conflict recovery

The branch topology remains authoritative even when GitHub cannot merge a
direct permanent PR automatically. A conflict must not turn a permanent merge
into a temporary squash.

For the exact merge-commit directions `dev -> main`, `main -> dev`,
`dev -> exp` and `exp -> dev`, Forge uses the generic template-owned
reviewed recovery boundary:

```text
conflicted permanent PR: base=A, head=B
        |
        +-- resolve/<name>
        |      -> separate PR to same base A
        |      -> mergeable + green central CI
        |      -> exact commit R / tree T
        |
        +-- /merge-resolved
               base A
               head B
               resolution-pr N
               resolution resolve/<name> R T
                    |
                    -> revalidate both PRs and A/B/R/T
                    -> create tree=T, parents=[A,B]
                    -> read back exact merge object
                    -> revalidate refs again
                    -> non-force advance permanent base
                    -> normal permanent CI + cleanup dispatch
```

The resolution PR is review evidence only and is never integrated. The
temporary resolution commit is therefore not a third parent of permanent
history. A moved parent/ref/tree, fork review, non-green review,
non-`resolve/*` head or non-permanent original direction fails closed. If the
original PR becomes normally mergeable, ordinary `/merge` is required.

A genuinely conflicted direct permanent PR may have no `pull_request` CI run
because GitHub cannot synthesize its merge ref. For `/merge-resolved` only,
Forge therefore uses the stable template-owned durable original-head gate: the
permanent head ref must still equal the reviewed SHA and
`build/<head>/build-plan.json.source_sha` must equal that same SHA. The
separate `resolve/*` review PR remains mergeable and green through ordinary
PR-specific central CI. Missing, stale or malformed durable evidence fails
closed.

Forge adopts this behavior from stable
`template.cad.library@4f5e7451a07607691fb6b54230b5569ff29b053b`; it does not
own a second conflict-recovery design.

## Main-owned governance merge boundary

Normal product work still integrates through `dev` or `exp`. A repository
may keep its small volatile governance entrypoints directly on stable `main`
without using the development lane as a staging copy.

The merge-policy route is deliberately narrow:

- the source branch uses the existing `docs/` temporary prefix;
- the target is `main`;
- the merge method is squash;
- changed paths are exhaustively read from the pull request and may contain
  only `AGENTS.md`, `docs/plan.md` and `docs/handoff.md`;
- any other path fails closed before merge;
- ordinary `docs/* -> dev|exp` work keeps its existing behavior.

Branch cleanup accepts a successfully merged `docs/* -> main` PR as a valid
temporary-branch completion, but this does not make stable a valid target for
issue/fix/feature/chore branches.

## Release boundary

Forge consumes the generic stable-main release boundary from
`template.cad.library@7049d34bf34a4303331f3f17608eaa75febe34fc`.

Product qualification and release metadata are deliberately separate. A
product-changing stable source still receives a normal full Forge qualification
and becomes the durable `build/main` product baseline. A later release commit
does not rebuild unchanged model owners merely because version/changelog
metadata changed.

The accepted release path is:

```text
qualified main product source
  -> release/vX.Y.Z from main
  -> CHANGELOG.md + cadlib/pyproject.toml:project.version only
  -> semantic delta preflight
  -> library + modules/release only; zero models
  -> squash to main through /merge
  -> release-only stable check, preserve prior build/main product evidence
  -> /release exact-main-sha
  -> main -> dev synchronization
```

CI records such candidates with `release_only: true`. Stable classification
uses the single-parent source delta itself and is identical for a normal
`push` or the merge-policy `workflow_dispatch` used for permanent integration
runs. A metadata-only delta selects `release` + library and zero models; a
merge commit or any product path remains full/fail-closed. Build publication
validates source freshness but deliberately does not replace the prior durable
full stable scope.

`modules/release` validates that retained product scope and then validates the
exact requested release source history. The full baseline must remain a
library + all-owner PASS. Every first-parent stable commit between that baseline
and the release target must be single-parent and may change only
`CHANGELOG.md` and the `project.version` value in
`cadlib/pyproject.toml`. Any product/source/model/dependency/build-config
change requires a new normal full stable qualification.

`.github/workflows/release.yml` checks out the exact requested source with
history, performs this repository/template-owned evidence validation, and then
delegates publication to released `tool.py.lib.ci v0.2.1`. The shared
publisher still requires the requested SHA to equal current `main` HEAD.

Forge-specific release metadata remains consumer-owned in
`cadlib/release.py`: package version, dated changelog section, active
release-blockers and `TESTED_SOLIDCRAFT_VERSION`. It emits release notes but
owns no generic build, tag or GitHub Release mechanics.

`release/*` is a first-class temporary branch whose valid integration target
is stable `main`; other temporary branches may target `dev` or `exp`. Branch cleanup uses
the same target mapping so cleanup cannot legitimize an invalid branch
integration.

Pages and `gh-pages` are not release evidence.


## Permanent dispatch source identity

Permanent `workflow_dispatch` qualification explicitly checks out `github.ref_name`, resolves that HEAD once, uses it as `CAD_SOURCE_SHA` for selection, and publishes against the same SHA. This avoids stale event-SHA races immediately after policy merges while keeping publisher freshness validation fail-closed.


## Experimental native backend boundary (#192, #253)

The second native backend established the need for an explicit Forge compiler
boundary. SCPF source is evaluated exactly once into Forge model objects.
Those objects are then normalized into typed, engine-neutral semantic IR before
any backend performs native command lowering.

```text
unchanged scpf model source
        ↓
one Forge frontend / model evaluation
        ↓
Forge semantic ModelIR
        ├── SolidCraft backend lowering -> SolidCraft replay/headless
        └── Mitcad backend lowering     -> Mitcad replay/MCP
```

`Shape` remains the authoring/frontend representation used while Python model
code is evaluated. `ModelIR` is the compiler boundary. Native backends do not
interpret portable raw `Shape.kind` / `Shape.data` payloads independently.

### IR completion versus backend completion (#525)

IR completion and backend completion are independent dimensions.

An **IR-ready** semantic family or slice has a backend-neutral CAD contract,
normalizes unchanged public SCPF source into typed IR rather than
`LegacyShapeIR`, has pure IR tests for its accepted and rejected boundaries,
preserves symbolic/history/topology dependencies, and retains the stable
SolidCraft behavior through typed lowering. A backend without support for that
typed node must fail closed.

A backend is tracked independently as unsupported, lowered, contract-tested or
native-qualified. Mitcad may deliberately lag the IR layer and catch up in
backend-focused batches. Exact Mitcad runtime qualification is therefore no
longer a per-capability gate for declaring IR semantics ready on permanent
`exp`.

This keeps backend transport from pacing or shaping the compiler contract.
Experimental coverage is recorded in `docs/ir-coverage.md`; that inventory is
evidence/status for `exp`, while the canonical work order remains
`main:docs/plan.md`.

The typed IR began with the first qualified portable slice:
`BoxIR`, standalone Circle2D Sketch+Extrude intent, `ChamferIR` and semantic
`FaceBoundaryIR` selection intent. #246 extends the same boundary with
`CylinderIR`; #343 later replaces the initial bounded Box-Cylinder boolean proof
with recursive `BooleanIR` plus `SphereIR`. #282 splits the former fused
Circle+Extrude node into `SketchIR`, `CircleProfileIR`, `RegionIR` and
`ExtrudeIR`. #351 adds `PolygonProfileIR` composition, initially qualified for
strict-convex profiles; #424 generalizes semantic region validation to finite
simple non-self-intersecting polygons so concave authored profiles do not need a
backend workaround. #381 adds `RevolveIR` over the same
Sketch/profile/region semantics rather than introducing a second
revolve-specific frontend. Symbolic Forge `Parameter` / `Expression`
values remain semantic values until backend lowering.

For the #381 checkpoint, the existing `native-revolve` source evaluates once
to a parameterized XZ polygon plus `RevolveIR`. #389 refactors its principal
world axis through `AxisLineIR(direction="X", origin=(0, 0, 0))`, so principal
and shifted axis intent use one semantic reference-geometry form. #440 moves the
bounded rectangle's Sketch solver meaning into that same compiler boundary:
`SketchRelationsIR` carries four semantic points, four connected straight
lines, V/H/V/H orientation constraints and symbolic `radius` / `length`
line dimensions. Sketch-local tuple positions are compiler references only;
they are not SolidCraft curve ids, Mitcad p/c/k ids, replay names or command
indexes.

`PolygonProfileIR` and `RegionIR` remain complementary closed-profile and
region semantics. The relation graph describes editable Sketch entities and
constraints; it does not replace region intent.

SolidCraft and Mitcad lower the same relation graph independently. SolidCraft
can preserve the authored symbolic point expressions directly in its existing
closed `sketch.line` native form, so it validates/consumes the relation graph
and coalesces it to that compact equivalent representation rather than emitting
redundant solver commands. Mitcad needs native solver relations, so it maps the
same semantic graph to backend-owned point/curve/constraint ids plus horizontal,
vertical and length relations. Fixing the first native point at the origin is a
Mitcad solver transport detail and never enters Forge IR. Once this rectangle
slice is typed, neither backend may infer those relations again from Polygon
coordinate relationships.

The point used to resolve the closed native region is still derived at lowering
time and is not retained in `RegionIR`.

#447 removes the remaining backend-owned semantic reconstruction for the
already-qualified non-rectangular parameterized Polygon Revolve path.
`SketchCoordinateDimensionIR` records one signed Sketch-local X or Y coordinate
for a semantic point relative to the Sketch origin, retaining the exact authored
Parameter/Expression value. A general parameterized simple Polygon therefore
normalizes semantic points, cyclic straight-line connectivity and two coordinate
dimensions per point before either backend runs.

The #440 rectangle keeps its stronger V/H plus edge-length graph. For the
generic coordinate graph, SolidCraft validates that every semantic point
coordinate is represented and then coalesces the graph to its existing symbolic
closed `sketch.line` command. Mitcad creates an extra fixed native origin point
and lowers each semantic coordinate to a signed horizontal/vertical distance
dimension. That origin entity and all p/c/k ids are solver transport only; they
are not Forge IR. The former Mitcad `_parameterized_polygon_sketch(...)`
semantic helper is therefore removed.

#451 proves that this Sketch relation layer is feature-independent rather than
Revolve-specific. The existing symmetric single-region Polygon Extrude
normalization now accepts authored parameterized point coordinates and attaches
the same relation graph to `SketchIR`. An origin-based rectangle uses the
stronger #440 V/H + edge-length graph; other accepted parameterized simple
polygons may use the #447 coordinate-dimension graph.

`ExtrudeIR` itself does not gain a relation field. Profile closure remains
`PolygonProfileIR`, selected area remains `RegionIR`, editable Sketch meaning
remains `SketchRelationsIR`, and the feature node owns only extrusion intent.
SolidCraft consumes the relation graph and can still emit its compact symbolic
closed polyline. Mitcad routes the same graph through its generic Sketch solver
transport before creating the native Extrude. Fixed-coordinate Polygon Extrude
continues to use fixed native Sketch points without inventing redundant relation
IR.

#456 separates selected-region semantics from total Sketch profile count. A
multi-profile concentric Circle Sketch retains every authored
`CircleProfileIR` in `SketchIR.profiles`, while one exact-region pick resolves
only the adjacent profile boundaries of the selected connected face. For the
three-circle 10/8/6 example and pick radius 4.5, the semantic result is
`RegionIR(outer=0, holes=(1,))`; profile 2 remains in the Sketch but is not a
boundary of that annulus.

Current radii are evaluated only to resolve which concentric interval contains
the authored pick. The typed result retains profile indexes, not the pick point
or any engine region identity. Region validation likewise checks adjacency of
the referenced boundaries rather than requiring the Sketch to contain exactly
two profiles. This permits unrelated circles strictly inside the selected hole
or outside the selected outer boundary without changing region membership.

Both backends draw all typed Circle profiles. SolidCraft emits an exact-region
selector whenever a Circle Sketch has multiple profiles, including a no-hole
innermost disk. Mitcad uses the deterministic selector derived from the same
`RegionIR`. Neither backend re-sorts diameters or re-decides outer/hole
membership.

#389 extends that compiler boundary rather than adding a Mitcad-specific model
path. `AxisLineIR` records only a principal semantic direction and symbolic
XYZ origin. A subtractive public composition such as `body - profile.revolve(...)`
normalizes to one `RevolveIR(operation="cut", target=...)`, retaining the
authored feature identity required by later suppression/configuration work.

SolidCraft lowers the shifted semantic axis directly to its native axis-line
form. Mitcad v0.70.0 needs a Sketch curve reference for the same shifted axis,
so the Mitcad backend alone derives a construction line and native dimensions
from `AxisLineIR`. The construction curve id never enters Forge IR. For the
cut, Mitcad replay binds the already-created target body at runtime and supplies
that returned body as the native Revolve participant; Forge never predicts the
body uid. The first qualified transport slice is deliberately bounded to an
unshifted XY Sketch, principal X/Y shifted axis and one Box target.

#417 extends reference geometry from axes to standalone Sketch planes. A typed
`PlaneIR(orientation, origin)` carries principal XY/XZ/YZ plane intent and
retains a symbolic normal-axis offset such as `axis_z`. Existing world-origin
Sketch/Profile/Extrude/Revolve slices use the same node; typed IR no longer
stores a backend-shaped plane string.

The semantic plane does not describe how a native engine constructs that
support. SolidCraft lowers the qualified principal plane directly through its
existing `sketch.create` plane/offset contract. Mitcad uses an origin plane
directly when the offset is zero; for a symbolic shifted plane the Mitcad
backend creates a native construction-plane feature and references the uid
returned by that command when it creates the Sketch. That helper feature and
uid are lowering transport only and never enter `PlaneIR`.

For the focused shifted Revolve cut, `PlaneIR` and `AxisLineIR` retain the
same authored `axis_z` dependency and the compiler checks their bounded
principal-plane coplanarity without replacing it with the current numeric
value. Rotated/arbitrary planes and attached Sketch supports remain later
compiler layers.

#424 adds the first semantic feature-reference and configuration layer rather
than teaching each backend to interpret public `Configure(...)` authoring.
`FeatureRefIR` names a feature by its normalized semantic path; the first
qualified path is the final/root `RevolveIR(operation="cut", target=...)`.
The reference contains no SolidCraft history id, Mitcad feature uid, replay
variable, command index or retained Python object id. Source-object identity is
used only while the frontend resolves the authored `Suppress(pass_through)`
reference to that semantic feature.

`ModelIR.configuration` carries a bounded `ConfigurationIR`: one semantic
suppression column, named rows, an explicit active row and boolean cells. This
is final CAD design state, not a Python variant. Stable SolidCraft lowering
binds the actual native Revolve feature returned by replay and emits the same
editable native configuration table contract as before. Mitcad v0.70.0 lowers
the same intent with a backend-private Unitless driver because its
configuration rows drive parameters: rows set only that private value, the
actual native Revolve uid returned by the command array is bound to
`suppress_feature`, and the feature follows an expression of the private
driver. Neither the driver nor the returned uid exists in Forge IR.

The `shifted-axis-revolve` owner is the end-to-end proof. Its stepped profile
also exercises a simple concave `PolygonProfileIR`. Forge validates the
current evaluated polygon only to reject degenerate/self-intersecting loops and
derive a deterministic interior region selector. Symbolic coordinates remain
in IR. Mitcad retains them in the saved Sketch by driving each point coordinate
from native dimensions whose expressions are the original Forge values.

Native qualification saves the Mitcad design in the authored `Cut` row,
reopens that same `.mitcad` file without rerunning Forge Python, applies
`Suppressed`, verifies the uncut target geometry, then applies `Cut` again
and verifies the cut returns. The reopen/apply helper belongs to native
qualification infrastructure; it is not public SCPF or semantic IR.

#433 generalizes semantic feature identity through already-typed Boolean
history. A reference such as `("root", "tool")` means the authored tool of
the root `BooleanIR`; `("root", "target", "tool")` descends through the
target history and selects its authored tool. These segments are Forge semantic
roles, not indexes into a backend command stream.

Normalization resolves the path while both the authored Shape tree and typed IR
tree are available, using source-object identity only during that frontend
step. After normalization, `FeatureRefIR` retains only semantic roles.
SolidCraft lowering maps the path to its replay-returned native feature, while
Mitcad attaches an `as` result binding to the corresponding native command;
those backend mappings are deliberately independent.

The existing `primitive-csg` owner proves the boundary without adding another
model. Its active `Clipped` row preserves the established geometry and
reference-engine comparisons. `Unclipped` suppresses the exact final
intersection tool: reopening the saved native design must restore the negative-Z
geometry hidden by the clip and increase volume, then reapplying `Clipped`
must return the original bounds and volume. A deeper bore reference is also
resolved in backend-independent tests so the model does not merely special-case
the final tool.

Parameter physical role is semantic compiler data, but it belongs to each
typed use rather than to one globally physical source variable. `ParameterIR`
therefore retains canonical use roles such as `length` and `angle`. A
single-role `sweep` keeps the accepted degree-native spelling and a
single-role Sketch dimension keeps the accepted millimetre spelling.

#469 qualifies the first mixed-role case: one direct Forge `Parameter` drives
both a Sketch length and the Revolve extent. The IR retains one source
parameter with roles `("length", "angle")`; neither backend creates two
editable aliases. SolidCraft and Mitcad instead publish one unitless/Number
native parameter and apply units at the typed use site: the Sketch relation or
coordinate uses `shared * 1 mm`, while the Revolve extent uses
`shared * 1 deg`. Those coercions are selected from `SketchRelationsIR` /
profile-coordinate and `RevolveIR.angle` meaning, not from backend command
names.

This slice deliberately does not dimension arbitrary symbolic expression
trees. A mixed-role source nested inside an authored `Expression` stays
behind `LegacyShapeIR` until the compiler owns expression-level dimensional
typing. The unchanged single-role parameter tests protect existing native
command spelling and the Mitcad v0.70.0 runtime smoke proves the mixed-role
source remains one editable native dependency.

The stable SolidCraft surface is larger than this first migration slice. A
temporary `LegacyShapeIR` therefore wraps not-yet-migrated stable intent so
the SolidCraft backend can delegate it to the historical lowering without a
whole-product rewrite. That node is an explicit transition boundary, not a
second frontend: Mitcad must reject it, and new multi-backend capabilities
must be introduced as typed IR rather than by adding new raw-shape parsing to
each backend.

The stable default remains SolidCraft. The Mitcad path is experimental and
explicitly rejects IR nodes, assemblies and selection modes that have not been
qualified. Forge must not silently replace unsupported native behavior with
geometry approximations.

Backend responsibilities are:

1. **lowering** — convert typed Forge IR to one engine's native command
   document while preserving symbolic parameter dependencies;
2. **native-result binding** — bind identities returned by that engine instead
   of predicting topology ids;
3. **topology resolution** — translate semantic IR selectors such as a
   top-face boundary into engine-native queries and references;
4. **execution** — run only that engine's native command/replay protocol and
   retain its native document/export artifacts;
5. **capability refusal** — raise a backend-specific `ModelError` before
   execution when intent is outside the qualified slice.

For SolidCraft, native topology remains replay-bound `model.faces` /
`model.edges` records. For Mitcad v0.70.0, the equivalent face-boundary path
queries the runtime's native `faces` list by cardinal planar normal, reads the
selected face's native names, queries the body's native edge names, and uses
Mitcad's own `E{faceA|faceB}` adjacency identity as the chamfer input. Forge
does not substitute XYZ edge picks.

The first qualified portable slice is deliberately small:

- centered/bottom-anchored Box primitive;
- standalone Circle2D Sketch + positive/negative distance Extrude;
- Box face-boundary Chamfer through `Edges.from_faces(...)`.

The experiment keeps `run_script(..., backend="solidcraft")` as the stable
default and permits `backend="mitcad"` only as an explicit experimental
choice. #212 formalizes this as an internal `BackendAdapter` registry and
#253 moves its shape boundary from `compile_shape` to `compile_ir`. Each
adapter declares `id`, display name, `compile_ir`, optional
`compile_assembly`, document family, executor and a capability set. The
runner evaluates model source, normalizes final Shape intent to `ModelIR`,
then hands that same semantic representation to the selected backend.

SolidCraft declares the stable Forge surface plus assemblies/native
topology/drawings. Typed portable nodes lower directly in the SolidCraft
backend; `LegacyShapeIR` delegates only not-yet-migrated stable surface to the
historical compiler. Mitcad declares only the already-qualified experimental
slice: `primitive.box`, `primitive.cylinder`, `primitive.sphere`,
`boolean.subtract`, `boolean.join`, `boolean.intersect`,
`placement.primitive`, `sketch.circle`, `sketch.polygon`, `profile.region`,
`feature.extrude.distance`, `feature.extrude.symmetric`,
`feature.revolve.angle`, `feature.revolve.cut`,
`reference.axis-line.shifted-principal`, `reference.plane.principal`,
`configuration.suppress.feature`, `modify.chamfer.face-boundary` and
`native-topology`; its assembly compiler is absent, so assembly intent fails
explicitly at the boundary. This registry is intentionally internal: it does
not rename `scpf`, expose a new public backend API or imply feature parity.

Mitcad command knowledge is versioned evidence under
`docs/reference/mitcad/<version>/`. Source reference identity, runtime MCP
reference/catalog capture and native AppImage identity are all pinned
independently so backend changes can be reviewed against a concrete engine
version.

Portable geometry is verified with the same generic mesh contract used by
normal Forge owners. The native smoke retains the Mitcad STL and feeds it to
`cad_verification.geometry` with the owner-local `geometry.json`; native
Mitcad body properties remain additional engine-specific evidence, not a
replacement verifier.

### Experimental recursive primitive CSG IR (#246, #343)

#246 first proved that new multi-backend CAD semantics belong in Forge IR by
migrating one Box-minus-Cylinder case. #343 generalizes that proof without
adding a second boolean model:

```text
SCPF primitive CSG
        ↓
BooleanIR(
  operation="intersect",
  target=BooleanIR(
    operation="cut",
    target=BooleanIR(
      operation="join",
      target=PlacementIR(SphereIR(...)),
      tool=PlacementIR(BoxIR(...))
    ),
    tool=PlacementIR(CylinderIR(...))
  ),
  tool=PlacementIR(BoxIR(...))
)
        ├── SolidCraft
        │     primitive(new) → primitive(join)
        │     → primitive(cut) → primitive(intersect)
        └── Mitcad
              primitive(new_body) → primitive(join)
              → primitive(cut) → primitive(intersect)
```

`BooleanIR` owns only semantic `join`, `cut` and `intersect` intent.
Its current qualified form is deliberately left-associated: the target may be a
previous `BooleanIR`, while each tool is one placed typed primitive. This
covers the existing public `primitive-csg` owner and the earlier
`cylinder-subtract` owner through one representation. The old
`BooleanSubtractIR` special case is removed rather than retained beside the
generic tree.

`SphereIR` stores Forge's radius semantic directly. SolidCraft lowers that to
its native radius field; Mitcad derives its native diameter during lowering.
Only the centered Sphere placement needed by the existing owner is qualified.
Translated/tangent-anchor Sphere intent remains legacy/fail-closed until a
separate placement slice proves it.

The typed SolidCraft lowering deliberately reproduces the existing stable CSG
command order and spelling. This is checked against the legacy compiler for
both the focused Box-Cylinder subtraction and the complete primitive CSG
source.

Pinned Mitcad v0.70.0 gives Box, Cylinder and Sphere the same primitive
operation vocabulary. Forge therefore emits one native Sphere `new_body`,
then the translated Box as `join`, Cylinder as `cut` and final translated
Box as `intersect`. Empty participants remain engine-owned meaning for the
existing component body set; Forge predicts no body id and does not import
BRep or use a generic geometry fallback.

The two translated centered Boxes in `primitive-csg` have their semantic
bottom faces exactly on the XY origin plane. Mitcad may therefore lower those
equivalent solids as one-sided Boxes on XY instead of pretending arbitrary
axial placement is portable. Other axial Box offsets remain fail-closed.

The existing `primitive-csg` physical owner adds `scpf-mitcad` beside its
SolidCraft-primary implementation and reuses the same SCPF source plus the
existing engine-neutral geometry contract. That contract distinguishes the
surviving spherical material, joined box extension, cylindrical bore and final
intersection clip plane, so simple bounds are not enough to pass.

### Experimental primitive placement IR (#268)

Primitive geometry and absolute placement are separate compiler concepts:

```text
Box(...) / Cylinder(...)
        ↓ geometry
BoxIR / CylinderIR
        ↓ placement
PlacementIR(
  primitive=...,
  point=(x, y, z),
  anchor=(ax, ay, az)
)
```

Direct primitives use `point=(0, 0, 0)`; `.at(...)` and qualified
translations change the same `PlacementIR` instead of introducing a second
backend-specific interpretation path. `BooleanIR` therefore combines
placed semantic solids, not raw authoring payloads.

SolidCraft lowers the full qualified world-space point through its established
native Box corner / Cylinder base calculations and must retain the exact
pre-#268 command form. Mitcad lowers transverse placement directly into the
primitive's parametrically editable plane `corner` / `center` values. The
origin-plane frames are mapped explicitly: XY=(+X,+Y), XZ=(+X,-Z),
YZ=(-Z,+Y).

The first Mitcad placement qualification deliberately requires the primitive's
axial placement coordinate to remain on its origin plane. This keeps
transverse X/Y-style coordinates symbolic without pretending that arbitrary
axial offsets or general frames are already portable. Unsupported axial
placement fails before native execution.

The focused `cylinder-subtract` owner moves its bore to X=8, Y=-5. Both
SolidCraft and Mitcad consume the same SCPF source; the generic mesh contract
moves its bore probe to that off-centre axis. This proves placement semantics
survive frontend → IR → two independent native lowerings.

#461 extends that same `PlacementIR` contract to standalone Sphere placement
instead of adding a Sphere-specific IR node. The semantic point remains the
world-space point of the selected Sphere anchor; the actual centre is derived
from that point, the anchor vector and `SphereIR.radius`. A top-anchor Sphere
at world Z therefore retains a symbolic centre-Z expression such as
`sphere_top_z - sphere_radius` rather than baking its current value.

SolidCraft already lowers this meaning directly to its native 3D Sphere centre.
Mitcad v0.70.0 represents a Sphere by a support `GeomRef` plane plus a
plane-local centre. Forge therefore reuses the backend's principal offset-plane
transport: a zero centre-Z stays on origin XY, while a non-zero or symbolic
centre-Z emits one private offset `construction_plane` and references its
returned uid from the Sphere feature. That helper feature and binding are
lowering transport only and never enter `PlacementIR`.

#473 extends the same Sphere placement semantics into recursive primitive CSG
without adding support geometry to Forge IR. The semantic tree remains only
`PlacementIR(SphereIR)`, `BooleanIR` and optional `FeatureRefIR` history.

Mitcad lowering now treats one semantic primitive as a private command group:
zero or more helper commands followed by exactly one command representing that
semantic feature. Box, Cylinder and an origin-plane Sphere still lower to one
command. A shifted or tangent-anchor Sphere may lower to an offset
`construction_plane` followed by the Sphere operation. The helper plane gets
a deterministic backend binding derived from the semantic history path, but
that binding never becomes a Forge feature reference.

Boolean lowering therefore keeps a private semantic-path → native-command
index map while flattening the tree. The map records the Sphere/Box/Cylinder
operation command rather than the first command in its group. Root, target,
tool and nested `FeatureRefIR` paths keep their existing meaning even when
native helpers change raw command positions. Configuration suppression uses the
same map, so `Suppress(shifted_sphere)` binds the Sphere cut/join feature and
never the construction plane.

SolidCraft needs no helper command and consumes the widened `BooleanIR`
through its existing CSG spelling. The exact Mitcad runtime proof cuts a
30 × 30 × 30 bottom-anchored Box with a radius-5 Sphere centred at world Z=15;
the resulting volume is `27000 - 500π/3` and the outer Box bounds are
unchanged.

#477 migrates the standalone Cone/frustum surface through the same primitive
geometry/placement split. `ConeIR` stores only height, base diameter, top
diameter and principal axis; the existing `PlacementIR` stores the selected
axial anchor point. The frontend therefore does not expose a Mitcad plane or
invent a Cone-specific placement representation.

SolidCraft derives the same base point with `_cone_base_from_anchor` and emits
the accepted `solid.cone` spelling, so typed lowering remains command-compatible
with the stable legacy compiler.

Mitcad v0.70.0 represents a Cone by a principal support plane, plane-local
centre, base radius, top radius and height. Forge derives the semantic base
first. If its axial coordinate is zero the Cone uses the origin principal plane;
otherwise lowering emits one private offset construction plane at that base and
references it from the Cone feature. Plane-local coordinates use the same
X/Y/Z mapping as Cylinder. This preserves CENTER and both axial-end placement
without adding support geometry to Forge IR.

The bounded runtime proof is a Ø18→Ø10 × 8 frustum whose BOTTOM anchor is at
world Z=18. It must remain one solid with volume `1208π/3`, XY base radius 9
and Z bounds [18, 26]. Cone participation in `BooleanIR` remains separate
because the existing `cone-boolean` owner also contains Fillet history and
would combine two migrations.

#481 adds a second, semantic channel to authored symbolic arithmetic. The
existing `Expression.expression` text remains the compatibility/debug spelling
used by already-qualified paths. Forge authoring operators now additionally
capture an immutable scalar-expression tree made from literals, parameter
references and bounded arithmetic nodes. Normalization and backends never parse
the compatibility text to reconstruct meaning.

`ParameterIR.roles` continues to summarize where one authored source parameter
is used. Physical units are still assigned by typed semantic fields rather than
by the scalar tree itself: Sketch coordinates/dimensions request the `length`
role and Revolve extent requests the `angle` role. Both native backends consume
the same scalar tree through their central role-aware value boundary. A mixed
parameter leaf therefore becomes `name * 1 mm` in a length use and
`name * 1 deg` in an angle use while remaining one editable native Number
parameter. Geometry features do not perform their own expression rewriting.

The first portable arithmetic subset is intentionally affine. Addition,
subtraction and unary negation preserve the surrounding use-site role;
multiplication/division are accepted only with a numeric scalar. A numeric
literal that participates in addition/subtraction inherits the use-site unit,
so the authored `shared + 1` Sketch coordinate lowers equivalently to
`(shared * 1 mm) + (1 mm)`. Numeric scale factors remain unitless. Expressions
without semantic-tree metadata, parameter×parameter arithmetic, inverse
parameter division and powers stay fail-closed for mixed-role portability.
Single-role paths bypass this renderer and keep their previously accepted
command spelling.

The runtime proof reuses the #469 mixed-role Revolve shape but changes its
radial Sketch height to `shared + 1`. With `shared=4`, the native design has a
5 mm radial height, 10 mm axial length and 4 degree sweep. Mitcad v0.70.0 must
produce one solid with volume `25π/9` and X bounds [0, 10] while retaining one
unitless editable source parameter.

#485 widens the existing `ChamferIR` rather than adding a second feature
kind. `distance` remains the primary chamfer distance; optional `distance2`
and `flip` carry the already-public two-distance semantics. Equal-distance
models continue to normalize to the same fields with `distance2=None` and
`flip=False`.

The first asymmetric portable boundary is intentionally narrower than the
public SolidCraft API: one typed Box and exactly the semantic TOP face boundary.
This is the orientation for which both engines can be made equivalent without
inventing an engine-specific face-order rule. SolidCraft documents the first
two-distance face as the most-upward adjacent face by default, with `flip`
swapping sides. For `Faces.TOP`, the semantic selected face is therefore the
unambiguous primary face.

SolidCraft keeps the accepted topology replay and emits the same
`solid.chamfer` command as the stable compiler, adding `distance2` and
`flip=true` only when authored.

Mitcad v0.70.0 represents a chamfer with an explicit reference face only in the
general `sets` form. Forge therefore keeps `FaceBoundaryIR(("top",))` as the
semantic contract while replay privately resolves both the selected TOP
boundary edges and one valid native name for that exact face. The native set
contains `size={type: two_distances, distance1, distance2}`,
`reference_face=<replay binding>` and optional `flip`. Native topology names
remain backend transport and never appear in `ChamferIR`. Equal-distance
Chamfer continues to use the existing short `edges + equal_distance` document
and requires no reference-face binding.

The exact runtime proof uses a 60×40×12 bottom-anchored Box and chamfers all
four TOP boundary edges with primary 0.18 mm and secondary 0.65 mm. The outer
bounds remain unchanged. The removed top-perimeter wedge is
`100*d1*d2 - (4/3)*d1^2*d2`, so the expected remaining volume is
28788.32808 mm³. A separate backend contract test proves `flip=True` changes
side ordering without changing the authored distances.

#496 proves that a portable primitive remains generic when it enters feature
composition. `ConeIR` already owns principal-axis frustum geometry and
`PlacementIR` already owns its world-space anchor point; recursive `BooleanIR`
therefore widens its bounded primitive operand set from Box/Cylinder/Sphere to
Box/Cylinder/Sphere/Cone without introducing `ConeBooleanIR` or another CSG
path.

SolidCraft lowers the Cone operand with the same `_cone_command` used by the
standalone #477 slice. The Boolean layer supplies only `new`, `join`, `cut` or
`intersect`, so the emitted `solid.cone` remains compatible with stable Forge
CSG spelling and keeps the existing Boolean source order.

Mitcad uses the same helper-aware command group introduced for shifted Sphere.
`_cone_commands` may emit a backend-private principal offset construction plane
before one native Cone feature. `_boolean_command_plan` records the feature
index returned by that command group, so `FeatureRefIR(("root", "tool"))`
continues to mean the authored Cone tool rather than the support plane. The
helper binding is derived deterministically from the semantic path (for example
`csg_plane_root_tool`) but remains transport only.

The runtime proof cuts a fully internal d10→0 × 20 Cone from a 30×30×30
bottom-anchored Box. The Cone BOTTOM is at world Z=5, so Mitcad must emit an
offset XY support plane at 5 mm followed by one native Cone with `operation=cut`.
The outer Box bounds remain [-15,-15,0]..[15,15,30] and the remaining volume is
`27000 - 500π/3`. A separate backend test exercises `join`; configuration
mapping tests prove a suppressible Cone tool binds the native Cone feature even
when its helper precedes it. The existing `cone-boolean` owner remains outside
this checkpoint because it also contains Fillet history.

#504 fills that remaining Fillet boundary without making native topology part of
Forge semantics. Public `Edges.VERTICAL` becomes
`ParallelEdgeSetIR(axis="Z")`: a statement about straight world-Z-parallel
edges, not four precomputed XYZ pick points and not a list of Mitcad edge
names. The first `FilletIR` is deliberately bounded to one
`PlacementIR(BoxIR)`, one positive constant/parameter radius and that semantic
parallel-edge set.

SolidCraft independently derives the accepted four Box edge pick points from
the typed Box corner, length, width and height, then emits the existing
`solid.fillet` command. This keeps stable command compatibility while making
the IR independent of SolidCraft's point-pick transport.

Mitcad cannot consume that semantic selector directly. Its replay stage first
binds the single current body, queries native edges with `geometry=true`, and
examines only native line geometry. Start/end vectors are compared against the
semantic principal axis with a tight relative tolerance; names are retained
only for the exact matching line edges. The first Box/Z slice requires exactly
four unique matches. Missing or extra matches fail closed. Native names and
endpoint geometry live only in replay bindings and never enter
`ParallelEdgeSetIR` or `FilletIR`.

The feature result then composes through the already-existing `BooleanIR`.
The bounded first composition is `FilletIR -> BooleanIR(join ConeIR)`, so
SolidCraft spells Box → `solid.fillet` → `solid.cone(operation="join")`.
Mitcad creates the Box, resolves/binds four Z-parallel native edges, creates one
native Fillet, then reuses the helper-aware Cone command group. A private Cone
support plane may occur between Fillet and Cone but is not a semantic history
node.

The exact runtime proof is the existing `cone-boolean` geometry contract:
50×40×20 BOTTOM Box, R2 on the four vertical edges, joined with an
Ø18→Ø10 × 8 Cone whose BOTTOM is at Z=18. The filleted Box volume is
`39680 + 80π`; only the Cone portion above the Box contributes another
`258π`, giving `39680 + 338π ≈ 40741.85831691335 mm³`. Bounds remain
[-25,-20,0]..[25,20,26]. Model-owner `scpf-mitcad` attachment remains a
separate catalogue checkpoint after the compiler/runtime contract is accepted.

#514 reuses the already-qualified semantic face-boundary selector rather than
adding another Fillet-specific topology vocabulary. The bounded extension is
exactly `FilletIR(..., edges=FaceBoundaryIR(("top",)))` over one
`PlacementIR(BoxIR)`. Public authoring remains the existing
`Edges.from_faces(Faces.TOP)`; FRONT/BACK/LEFT/RIGHT/BOTTOM and multi-face
Fillet selections remain outside the slice.

SolidCraft lowers that selector through the same semantic TOP-face query and
complete-boundary binding used by typed Chamfer, then emits the existing
`solid.fillet` spelling. Mitcad reuses the existing replay
`bind_face_boundary_edges` contract and passes only the resulting private
native edge names to one Fillet feature. Fillet does not need Chamfer's
two-distance `reference_face`; native face/edge ids remain backend transport.

This first face-boundary Fillet remains standalone. The existing
Fillet→Cone `BooleanIR` widening is intentionally restricted to
`ParallelEdgeSetIR("Z")`, so adding TOP-boundary Fillet does not implicitly
qualify a new composition path. Exact Mitcad v0.70.0 qualification uses a
60×40×12 BOTTOM Box with R2 TOP-boundary Fillet, unchanged
[-30,-20,0]..[30,20,12] bounds. The first accepted pinned runtime pass measured
28631.38638124875 mm³; that literal native result is the regression value rather
than a separately derived geometric estimate.

#519 is the first IR-completion batch under the #525 IR-first policy. Explicit
public Hole-family authoring is one CAD feature/history concept rather than a
special Cylinder Boolean. `HoleIR` therefore owns the typed target, entry
point, automatic-inward or fixed drilling direction, through-all/finite depth
intent and the variant-specific simple/counterbore/countersink/thread metadata.

The bounded target is a typed Box, and repeated explicit holes form a semantic
history chain by allowing one `HoleIR` to target the preceding `HoleIR`.
That preserves source feature order without inventing a generic Boolean for an
operation whose authored meaning is “Hole”. Parameter/Expression values in
length-valued fields remain semantic CAD dimensions. Countersink angle and
drilling direction stay fixed numeric intent in this batch rather than silently
changing their stable parameter-unit behavior.

SolidCraft lowers the typed chain back to the existing one-native-feature
`solid.hole` spelling for each authored Hole. This is checked against the
legacy compiler document, including the distinction between omitted through-all
depth, omitted auto-inward direction, counterbore/countersink fields and
thread metadata. No SolidCraft command field is part of `HoleIR`.

Mitcad is intentionally not implemented in #519. It must reject `HoleIR`
explicitly as an unsupported typed node, proving that backend lag does not push
valid semantic intent back into `LegacyShapeIR`. A later Mitcad backend batch
may lower the same Hole semantics using native Hole intent or backend-owned cut
geometry without changing Forge IR.

Topology-relative `Hole.on(...)`, attached Hole construction,
feature-pattern/configuration composition and parameter-driven
direction/countersink-angle widening remain separate IR work.

#532 adds a generic `BodyIR` result/history contract so downstream features do
not need pair-specific target unions merely to say “the current typed body”.
All already-typed body-producing nodes participate in that marker without
changing their existing feature semantics or their current normalization
boundaries.

The first new consumer is `ShellIR`. It owns one typed BodyIR base, one
positive symbolic wall thickness and a `FaceSetIR` containing the cardinal
faces that remain open. `FaceSetIR` means the faces themselves; it is
deliberately distinct from `FaceBoundaryIR`, whose meaning is the boundary
edges of selected faces.

SolidCraft now lowers typed body history through one shared dispatcher. Shell
first lowers its semantic base, then performs cardinal native face queries and
passes only the privately bound face names to the existing `solid.shell`
command. Topology query indexes are derived from the already-emitted typed
history, preserving stable command documents when Shell follows another
topology-consuming feature.

`HoleIR.target` also becomes the generic BodyIR contract. This allows an
explicit Hole to follow any already-typed body history that SolidCraft can
lower, such as a typed Chamfer, without inventing a Chamfer→Hole special IR
pair. The Hole node itself is unchanged. This composition widening does not
claim that legacy targets, attached Hole placement or other feature semantics
have become typed.

Mitcad remains fail-closed for unsupported ShellIR/HoleIR histories. #532 does
not widen vertical Fillet, Chamfer, Revolve or Boolean normalization merely
because their result classes participate in BodyIR.

### Experimental Sketch/Profile + Extrude IR (#282)

Standalone sketch geometry, region membership and the consuming feature are
separate compiler concepts:

```text
SCPF Sketch + Circle2D + extrude
        ↓
SketchIR(
  profiles=(CircleProfileIR(...),)
)
        ↓
RegionIR(outer=0, holes=())
        ↓
ExtrudeIR(sketch=..., regions=..., distance=..., direction=...)
        ├── SolidCraft lowering
        │     sketch.create → sketch.circle.center → sketch.finish
        │     → solid.extrude
        └── Mitcad lowering
              native sketch feature → native extrude feature
```

Profile indexes in `RegionIR` are compiler-local semantic references inside
one `SketchIR`; they are not native curve ids or engine region ids. The IR
therefore has a place to express future nested-loop membership without
embedding either engine's topology vocabulary. A backend may derive an
engine-native region selector from the semantic profiles during lowering; for
the current Mitcad circle slice the native `[0, 0]` pick is derived from the
qualified circle geometry and is not stored as region intent.

#282 initially qualified only the existing single centered Circle2D region
with no holes and positive/negative distance extrusion. #320 extends that same
boundary to the already-public #267 two-concentric-circle exact-region annulus:

```text
SketchIR(
  profiles=(outer_circle, inner_circle)
)
RegionIR(outer=0, holes=(1,))
        ├── SolidCraft: one Sketch + two circles + one exact-region Extrude
        └── Mitcad: one native sketch + two circles + one region-bound Extrude
```

The public fixed profile pick is frontend selection evidence, not IR data.
Normalization proves that the selected point lies between the two concentric
radii, then discards it. A shared semantic helper derives a deterministic
interior point midway between the inner and outer radii only when a backend
needs a coordinate transport selector. SolidCraft emits that point through its
existing `profiles=[{point: ...}], exact_regions=true` contract; Mitcad sends
the point to its MCP, which resolves and stores the engine-owned native region
reference. Forge never predicts or retains a Mitcad region id.

Both symbolic diameters and extrusion distance remain semantic values through
IR. The circle slice is deliberately bounded to one circle or one
two-concentric-circle annulus. Non-concentric/nonnested circle membership and
more than two circle profiles remain LegacyShapeIR. Other profile families
require separately qualified semantic IR; #351 later adds the bounded convex
PolygonProfileIR path without introducing a second backend parser.

SolidCraft lowering remains byte-for-byte compatible with the accepted legacy
command plan for both qualified owners. `circle-negative-extrude` retains the
single-region A/B proof; `multi-profile-extrude` adds the annular proof and
uses the same physical owner/source for SolidCraft and Mitcad.

### Experimental polygon Extrude + feature-composition IR (#351)

#351 extends the Sketch/Profile compiler boundary from circles to one bounded
closed straight-segment profile and, more importantly, proves that one typed
feature result may feed another typed feature without returning to raw Shape
payloads:

```text
Polygon2D
    ↓
SketchIR(
  profiles=(PolygonProfileIR(...),)
)
    ↓
RegionIR(outer=0)
    ↓
ExtrudeIR(direction="symmetric", distance=15)
    ↓
ChamferIR(
  base=<that ExtrudeIR>,
  edges=FaceBoundaryIR(("front", "back"))
)
      ├── SolidCraft
      │     one XZ Sketch + closed sketch.line
      │     → symmetric solid.extrude
      │     → replay-resolved FRONT/BACK boundaries
      │     → one solid.chamfer
      └── Mitcad
            one native XZ Sketch with Point/Line entities
            → native symmetric full-length Extrude
            → runtime body + FRONT/BACK boundary queries
            → one native Chamfer
```

`PolygonProfileIR` stores Sketch-local points and optional authored segment
ids only. It contains no SolidCraft curve ids, Mitcad entity ids or native
region ids. The first Mitcad-qualified slice is intentionally strict: one
fixed, finite, strictly convex polygon. The frontend validates that shape and
derives a deterministic interior selector from its semantic geometry only when
native lowering needs a point-based region bind. Parameterized, concave or
degenerate polygon forms stay behind `LegacyShapeIR` rather than being baked
or approximated.

Symmetric extrusion remains one Forge semantic. The public SCPF distance is the
total full length. SolidCraft keeps its existing
`direction="symmetric", distance=<total>` spelling. Mitcad lowers the same
intent through v0.70.0's native symmetric extent with
`full_length=true`; Forge does not reinterpret the authored 15 mm as 15 mm
per side.

This checkpoint also widens `ChamferIR.base` from only a placed Box to the
qualified typed `ExtrudeIR` result. Lowerings therefore recurse through the
semantic feature chain. SolidCraft reproduces the accepted legacy command
document. Mitcad first creates the Sketch/Extrude body, then resolves topology
against that native result. Neither backend inspects the original
`sketch_base_extrusion` Shape payload after normalization.

The existing Mitcad replay transport keeps its single-face `face={...}`
contract unchanged and adds a backward-compatible multi-face
`faces=[...]` form. Each query resolves one native face boundary; the adapter
combines and deduplicates returned native edge names before executing one
Chamfer feature. The query list and returned edge identities are transport
details and never enter `FaceBoundaryIR`.

The unchanged `topology-face-boundary-xz` physical owner is the qualification
case. It adds `scpf-mitcad` beside SolidCraft and applies one shared mesh
contract to both exports. Bounds prove the 40 × 15 × 30 symmetric extrusion;
surface-distance probes on different FRONT/BACK boundary orientations prove
the 1.5 mm equal-distance chamfer instead of accepting an unchanged prism.

### Experimental Mitcad builder boundary (#218)

The normal Forge build integration is a thin consumer of that accepted backend
boundary:

```text
owner-local SCPF source
        ↓
builder-scpf-mitcad
        ↓ run_script(source, backend="mitcad")
scpf-mitcad command document
        ↓ scpf.backends.mitcad_headless.run_document(...)
model.mitcad + model.stl
        ↓
cad_library_ci.runtime writes normal build.json
```

The builder does not own Mitcad installation, version discovery or downloads.
Its runtime contract is an already-qualified `mitcad-cli` executable on
`PATH`; a runtime may provide an explicit executable through
`CAD_LIBRARY_MITCAD_EXECUTABLE`. The builder validates the command document,
executes it through the existing native headless boundary and fails closed if
either the native document or STL is missing.

#218 deliberately qualified the builder before a root `runtimes.mitcad`
entry. #221 then qualified the runtime independently in
`brainboxemb/docker.cad.solidcraft`: v0.3.7 publishes an isolated
`cad-mitcad` image pinned to Mitcad 0.70.0 and exposes `mitcad-cli` on
`PATH`. Forge `exp` pins that immutable role in root `ci.yml`.

Before the immutable release, temporary evidence PR #230 used the exact
runtime-candidate manifest through normal CAD-CI and proved both
`simple-box--scpf-mitcad:geometry` and
`circle-negative-extrude--scpf-mitcad:geometry` PASS. That PR was closed
unmerged so candidate-only owner declarations did not enter `exp`.
#232 owns the secondary owner attachment.

### Experimental Mitcad owner integration (#232)

The first persistent Mitcad implementations do not create a second model tree.
The existing owners `simple-box`, `circle-negative-extrude` and
`topology-face-boundary-box` each add one secondary `scpf-mitcad`
implementation that points to the same owner-local `scpf/model.py` as the
primary SolidCraft `scpf` implementation.

`simple-box` and `circle-negative-extrude` reuse their existing generic mesh
geometry contracts. `topology-face-boundary-box` adds a generic geometry
contract because its previous evidence was SolidCraft-native only: common box
bounds and watertightness are supplemented by two surface-distance probes at
the original top boundary edges. A correct 2 mm equal-distance chamfer moves
those surfaces by `sqrt(2)` mm, so an unchamfered box cannot satisfy the
contract. The same contract applies to both SolidCraft and Mitcad STL.

SolidCraft remains the primary implementation and owns native/visual checks.
Mitcad remains a secondary experimental implementation and enters the normal
reference-runtime mesh verification path.


### Experimental Mitcad Pages evidence (#243)

The experimental site is an inspection surface for the accepted multi-backend
boundary, not merely a status dashboard. A persistent `scpf-mitcad` build
therefore publishes three distinct durable artifacts:

```text
scpf/model.py
     ↓ Forge Mitcad lowering
mitcad.json          pre-execution Forge → Mitcad command/replay document
     ↓ cad-mitcad:v0.3.7 / mitcad-cli
model.mitcad         native document saved by Mitcad
model.stl            geometry exported by Mitcad
     ↓ reference preview + verification
model.png + verification evidence
```

`builder-scpf-mitcad` writes `mitcad.json` only after the backend document
passes `validate_document`, before native execution. The document is therefore
the exact validated intent supplied to the headless layer, including replay
bindings used for native topology operations. Pages reads the durable file and
projects both initial commands and replay-stage binding/command rows; it does
not regenerate the stream from SCPF source.

The normal deterministic mesh preview renders `model.png` from the actual
Mitcad-exported `model.stl`. The UI labels that image **Mitcad STL result** so
it cannot be confused with a native Mitcad viewport screenshot. The saved
`model.mitcad` document remains directly linked as the engine-native result.

When `scpf` and `scpf-mitcad` point to the same owner-local
`scpf/model.py`, Pages marks the latter as a shared-source alternate backend:
the primary SCPF source is shown once, while Mitcad keeps its own command,
preview, native-model, build and verification evidence.
