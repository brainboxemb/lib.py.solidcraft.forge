# Change 0005 — HUB75-like multi-parent AnchorFrame regression

Status: design + qualification work in progress  
Tracking issue: #175  
Related issues: #162, #92

## Problem

Forge has small AnchorFrame/attach qualification cases that pass, including the
single-parent `eight-corner-brackets` fixture. They do not reproduce the
regression seen in the larger HUB75 wood-frame assembly.

The missing structural detail is not "a more complicated bracket". It is the
assembly graph:

- two occurrences of one parametrically sized side-board definition;
- each board occurrence has its own symbolic Placement;
- four child brackets are attached to each board;
- the eight children share one neutral reusable L-profile definition;
- child mount frames carry non-zero local A/B offsets and explicit axes;
- front and rear relationships differ along Y;
- width, height and depth must remain associative after editing the saved design.

`AnchorFrame` worked in earlier Forge/CAD work. The current behaviour is a
regression. This change must not describe it as a design that "masks" another
problem.

The production HUB75 CAD model has meanwhile been restored to explicit
symbolic `Placement` and is green. Change 0005 does **not** require that model
to use AnchorFrame again.

## Decision

Reproduce the relationship in Forge with one self-contained diagnostic case,
using simple geometry.

The case has two SCPF variants that share the same component geometry:

1. **Placement baseline**
   - side boards are parametrically placed occurrences;
   - all eight L-profiles use explicit symbolic `Placement`;
   - this is the expected native geometry.

2. **AnchorFrame variant**
   - the same two side boards use the same symbolic Placement;
   - the same neutral L-profile is reused eight times;
   - standard parent FRONT/BACK corner anchors are combined with four explicit
     child AnchorFrames;
   - eight authored `attach()` relationships place the profiles;
   - no explicit child Placement is allowed as a corrective workaround.

The Placement baseline is diagnostic reference geometry. It is not an
alternative lowering of `attach()`.

## Geometry

Keep the fixture close to the HUB75 construction but deliberately small:

- opening between side boards;
- two vertical side boards, each one wall thickness wide;
- SideBoard itself is only `Box(width, depth, height)`; all cabinet position
  belongs to its occurrence `Placement`;
- cabinet depth along +Y;
- boards start one wall thickness above the outside bottom datum;
- one neutral polygonal L-profile in local XZ;
- in this diagnostic the L-profile wall thickness is the same 12 mm as the
  side-board/frame wall, matching the historically working HUB75 mount frames;
- the profile is extruded symmetrically along Y;
- front/rear profiles share the same X/Z corner class and differ only in Y.

The four expected X/Z orientation classes are:

| Corner | Baseline orientation |
| --- | --- |
| top-left | Y 0° |
| top-right | Y 90° |
| bottom-left | Y 270° |
| bottom-right | Y 180° |

This avoids the ambiguity of quarter-turning an asymmetric L-profile.

## Child AnchorFrames

The child frames model the same A/B mounting references used by the earlier
HUB75 experiment.

Let `w` be the L-profile wall thickness. In this fixture `w = 12 mm`,
the same value as the side-board wall thickness, because that equality is part
of the historically working HUB75 mount geometry:

- A = `(0, 0, -w)`
- B = `(w, 0, 0)`

Front and rear frames use opposite Y normals. Their X direction fixes the
remaining clocking. The bracket extrusion is symmetric about local Y.

The parent side-board occurrence remains the real attachment target. The
application-specific A/B references belong to this diagnostic assembly, not to
the generic L-profile component definition.

## Native command contract

### Placement baseline

Expected structure:

- one reusable SideBoard definition and two occurrences;
- one reusable LProfile definition and eight occurrences;
- symbolic `occurrence.move` commands for both side-board placements;
- symbolic `occurrence.move` commands for the eight L-profile placements;
- zero `joint.create` commands.

### AnchorFrame variant

Expected structure:

- the same reusable SideBoard and LProfile definitions/counts;
- symbolic `occurrence.move` commands for both side-board placements;
- exactly eight authored `joint.create` relationships;
- no generated hidden placement joints;
- child AnchorFrames are supplied directly to the authored relationships;
- standard parent corner origins carry the already-defined
  `_corner_native_x(anchor)` clocking axis explicitly. SolidCraft 0.42 uses
  current pose/minimum-turn behaviour when this axis is omitted, which can pick
  the alternate rigid orientation on the right-side corners;
- the `CornerBrackets` browser group is not grounded, because its children
  attach to SideBoard occurrences outside that group;
- attached child `occurrence.move` commands may be concrete solver seeds.
  That was already the behaviour in the historically working Forge 79b2be2
  implementation and is not the regression being fixed here.

The exact numeric seed pose remains an implementation detail.
The public distinction remains:

- `Placement` = absolute occurrence pose;
- `attach()` = semantic component relationship.

## First-divergence rule

Do not change lowering until the diagnostic records where the variants first
differ.

Compare, in order:

1. Python-side ModelInstance Placement/Attachment state;
2. generated SolidCraft command JSON;
3. initial native transforms and body bounds;
4. saved-design transforms/bounds after parameter mutation.

The first mismatching layer is part of the qualification evidence.

## Parametric mutation

The saved designs must be edited without rerunning Python.

Change at least:

- opening width;
- opening height;
- cabinet depth.

Both variants must recompute to the same eight L-profile poses after mutation.

The test specifically exercises two independently placed parent occurrences.
A single parent block is insufficient because it does not reproduce the
floating/multi-graph behaviour observed downstream.

## Qualification

Register one public qualification case for the AnchorFrame variant and publish
the Placement baseline as additional diagnostic evidence on the same case.

Required evidence:

- AnchorFrame Forge source;
- Placement baseline Forge source;
- generated command JSON for both;
- initial native measurements for both;
- mutated native measurements for both;
- occurrence-by-occurrence comparison for all eight L-profiles;
- joint inspection for the AnchorFrame variant;
- front/right/isometric renders;
- PythonSCAD, pyBOSL2 and CadQuery references per change 0004.

Q5 passes only when the saved AnchorFrame design follows width/height/depth
mutations and remains equal to the Placement baseline.

## Non-goals

This change does not:

- modify the production HUB75 CAD model;
- require downstream code to migrate back to AnchorFrame;
- copy the detailed printed CornerBracket geometry;
- hide an AnchorFrame failure with manual child Placement;
- redefine Placement as a joint;
- accept a visual-only match without native transform/bounds evidence.

## Expected implementation investigation

Historical CI and retained artifacts now identify the regression boundary:

- CAD commit `7859e3f...`: inside-corner child frames + joint angles, native PASS;
- CAD commit `4d4130...`: A/B child frames as component anchors, native PASS;
- CAD commit `a03c6ae...`: an incomplete migration moved the frames into the
  assembly but left four stale string references (`"front_mount_a"` /
  `"rear_mount_a"`); it failed during Python anchor resolution, so it is not
  evidence of a native AnchorFrame solver failure;
- CAD commit `c8f485...`: all eight relationships use direct A/B
  `AnchorFrame` objects, native PASS, including saved width/height/depth
  mutations, using Forge `79b2be2`;
- Forge commit `56db3d6...` later changed named-group lowering to
  **ground every group**;
- retained HUB75 artifacts show the later regression with essentially the same
  eight bracket seed moves and eight joints, but `CornerBrackets` changed
  from `grounded: false` to `grounded: true`.

The resulting native symptom matches that over-constraint: one side of the
external joint graph can remain on the wrong solution and fails to follow a
saved-design parent mutation.

Change 0005 therefore keeps the historical numeric attached-child seed
lowering and fixes two compatibility regressions exposed by the newer stack:

1. named-group grounding: independent browser groups stay grounded, while a
   group containing children attached to occurrences outside that group remains
   ungrounded;
2. SolidCraft 0.42 corner clocking: standard corner origins now emit their
   existing explicit `x` axis so direct child AnchorFrames do not depend on
   0.42's minimum-turn choice around the mating normal.

The diagnostic evidence, not the earlier seed hypothesis, determines these
fixes.
