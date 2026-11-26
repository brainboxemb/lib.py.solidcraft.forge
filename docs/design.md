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

The intended Forge path is:

```text
models/<id>/scpf/model.py
        ↓ cadlib/scpf compiler
SolidCraft command JSON
        ↓ generic builder-solidcraft
model.sc + model.stl + native model.png
        ↓ reference verifier
owner-local geometry/semantic evidence
```

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

## Native configuration-table boundary

Configuration is final design intent rather than a Python model variant. The
public authoring boundary is:

```python
Configure(design, active=..., columns=(...), rows={...})
```

The configured `design` may be a single `Shape`, one component occurrence or
an `Assembly`. `Param(...)` points at an existing native model parameter, so
the same column type can drive dimensions, occurrence `Placement`, attachment
offsets and other native associative dependencies. `Suppress(feature)` points
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
| `configuration-installed-state` | one physical flexible-fit component with `Free` manufacturing geometry and `Installed` mounted geometry, switched natively after saving |
| replay row identity | Forge-generated name-stable row references bind to SolidCraft-returned native row ids; activation uses the bound id |
| saved-design switching | rows are switched after reopening the generated `.sc`, proving configurations are native document state rather than Python presets |

The use-case boundary is intentional:

| Use case | #216 public contract |
| --- | --- |
| product sizes / dimensional presets | `Param(...)` |
| front/below/service assembly positions | `Param(...)` driving associative `Placement` |
| optional authored feature | `Suppress(feature)` |
| dimensions plus suppression in one row | supported by the same table |
| flexible-fit free/mounted state | `Free` / `Installed` rows using ordinary native parameters; this is a physical configuration, not a display state |
| material or appearance variants | native SolidCraft supports them, but Forge waits for a typed, separately verified column contract |
| whole component present/absent | not silently mapped to feature suppression |
| alternate attachment/joint graph | not a configuration cell; requires explicit relationship authoring |
| arbitrary Python branches per row | rejected as a configuration-table substitute |

A suppression reference must be an actual Forge feature handle available to the
configured design. #216 does not invent string paths into hidden child-component
implementation details. If cross-component exported feature handles are needed,
that is a reusable component API capability and must be designed explicitly.

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
- `title_block_style="compact"` lowers to native `drawing.sheet.set(title_block="compact")`, using SolidCraft's compact 49 mm block rather than Forge-rendered replacement graphics.

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
        ↓
docs/reference/solidcraft/<version>/
  commands.json
  commands.md
  SOURCE.md
```

`modules/solidcraft-reference` validates registry completeness, captures and
normalizes the exact runtime registry, renders the human catalog/provenance, and
compares the checked snapshot back to the same immutable runtime. Its item watch
includes `docs/reference/solidcraft/**`, so reference changes select their
own verifier. Historical version directories remain immutable evidence.

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
