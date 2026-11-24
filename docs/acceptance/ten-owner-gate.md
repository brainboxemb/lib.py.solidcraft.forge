# Ten-owner migration gate — candidate acceptance

This record extends the accepted five-owner baseline with five additional historical Forge owners. NEW candidate run **45445906212** at source **bcee6f2f9eab9e7429a06f5a219ae3e045fa87ba** is green. Candidate artifact: **14946042553** (`cad-qualification`).

Historical authority: `brainboxemb/lib.py.solidcraft.forge` generated branch `build`, scope `dev-cad/examples/<id>/`. All corresponding OLD items report `status: pass`.

| New owner | Historical bundle SHA-256 | Purpose | Historical implementations | Candidate |
| --- | --- | --- | --- | --- |
| corner-anchor | `a906b716e952daf095cbc644235d27c6062ff5cf9e75fc068ea1325c0f50001b` | example + verification | SCPF + 4 reference | pass |
| rectangular-pattern | `7dc89eb5743931a93c874b47a61673cb0e4f0d3e87793488facd4abc0e542dfc` | verification | SCPF + 4 reference | pass |
| rotated-sketch-cutter | `4843bb42f2cc6d32e55c14afa945a14dc071676d890feac5659c08a575e7555f` | verification | SCPF only | pass |
| slot-family | `c9e9ebb0baef3f63855016823178ee34c18289986862f02caaad72d391679ca1` | verification | SCPF + 4 reference | pass |
| sheet-fold | `9d4aa9e44fc393f52d240122c97bf9988e9c580c28bc5a441087429a79eb3111` | verification | SCPF + 4 reference | pass |

## Ownership and command contracts

The historical SCPF and reference source files were migrated into one physical owner each. No synthetic reference implementations were added.

`rotated-sketch-cutter` deliberately has one SCPF implementation and one native verification stage because that is the historical contract.

All selected owner-local command-contract tests pass before CAD execution. In particular:
- corner-anchor retains the rigid topology-backed corner relationship;
- rectangular-pattern emits one two-direction native `solid.pattern.rectangular` with dimensionless count parameters;
- rotated-sketch-cutter retains two explicit rotated native Sketch frames;
- slot-family retains all five native Slot creators and dimensioned-sketch bindings;
- sheet-fold retains native sheet rule, base flange, Hole and Fold history.

Replay evidence remains consumer-owned by SCPF:
- corner-anchor: 11 authored commands, 2 phases, Base/Marker occurrence bindings;
- rectangular-pattern: 11 commands, 2 phases, top-face binding;
- slot-family: 30 commands, 5 phases, top-face plus three Slot centre-line/middle bindings.

## Native parity

All **10/10 native SCPF stages pass**.

### corner-anchor

NEW baseline matches OLD:
- Base: `[-20,-15,0] .. [20,15,20]`;
- Marker: `[10,-25,10] .. [20,-15,20]`;
- parameters `base_width=40`, `base_height=20`.

Saved design `size_80x40` also matches OLD:
- Base: `[-40,-15,0] .. [40,15,40]`;
- Marker: `[30,-25,30] .. [40,-15,40]`;
- native parameters become 80 mm and 40 mm.

### rectangular-pattern

NEW baseline matches OLD:
- one body `[-60,-40,0] .. [60,40,4]`;
- volume `36281.41598682458 mm³`;
- 30 faces: 12 cylinder + 18 plane;
- parameters columns=3, pitch=24, rows=2, row_pitch=28;
- native timeline ends in `RectangularPatternFeature`.

Saved design `columns_2_pitch_30` matches OLD:
- columns=2, pitch=30 mm;
- volume `36987.61065788305 mm³`;
- 22 faces: 8 cylinder + 14 plane.

### rotated-sketch-cutter

The intentionally SCPF-only owner matches OLD:
- bounds `[-30,-30,-15] .. [30,30,15]`;
- volume exactly `107488 mm³`;
- timeline contains Box, Left wedge Sketch/Extrude, Right wedge Sketch/Extrude.

### slot-family

NEW baseline matches OLD:
- bounds approximately `[-80,-60,0] .. [80,60,5]`;
- volume `89526.65799554957 mm³`;
- 26 faces: 14 cylinder + 12 plane;
- Slot family Sketch has 29 curves and 5 profiles;
- editable native slot parameters retain historical values.

Saved design `parametric_slots` matches OLD:
- slot_width 10 mm;
- straight_y -20 mm;
- c2c_end_x -35 mm;
- overall_end_x 25 mm;
- center_point_end_x 70 mm;
- volume `86615.62341029986 mm³`.

### sheet-fold

NEW baseline matches OLD:
- folded bounds approximately `[-40,-20,0] .. [21.64380551,20,21.64380551]`;
- volume `6343.451332235381 mm³`;
- native sheet-metal body is closed;
- timeline is Sketch → BaseFlangeFeature → HoleFeature → FoldFeature.

The flat-pattern inspection also matches OLD:
- flat size 80 × 40 × 2 mm;
- one Ø6 cutout centered at (-20,0);
- one 90° bend, radius 2 mm;
- bend allowance `4.71238898038469`;
- rule `SheetFold Rule`;
- thickness 2 mm, K-factor 0.5.

## Reference geometry

The ten-owner candidate contains:
- nine owners with SCPF + four historical reference implementations;
- one SCPF-only owner (`rotated-sketch-cutter`).

All **45 applicable geometry stages pass** in `cad-reference:v0.3.5`. No artificial geometry/reference stage is created for the SCPF-only owner.

## Remaining integration acceptance

The candidate is accepted for integration. The ten-owner gate is complete only after:
1. PR #24 is squash-merged to `dev`;
2. permanent `build/dev/models` contains all ten owners;
3. Pages publishes exactly three Examples entries (`simple-box`, `anchored-holes`, `corner-anchor`) and all ten owners under Verification; owners with both purposes appear in both views;
4. post-merge dev CI/Pages are green;
5. the ten-owner baseline survives a full `dev -> main` promotion.

Do not start remaining-graph migration before these checks are complete.
