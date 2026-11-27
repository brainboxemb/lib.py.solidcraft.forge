# Twenty-owner migration gate — candidate acceptance

This record extends the accepted ten-owner baseline with the ten remaining historical owners from the first two Forge Verification groups.

Technical candidate:
- source: `553033bdd2ccf0e5612e8f12d2a95c51a51ec462`;
- CI run: **45456265226**;
- qualification artifact: **14950656646** (`cad-qualification`);
- artifact SHA-256: `be7de244eff3513ed06dd5b8d9a8493c514bc3cc4a654cc2b2693a0df67f462f`.

Historical authority is `brainboxemb/lib.py.solidcraft.forge`, generated branch `build`, scope `dev-cad/examples/<id>/`. The table pins each OLD generated owner by its immutable Git tree object. All corresponding OLD model verification records report pass.

| New owner | OLD generated tree | Purpose | Historical implementations | Candidate |
| --- | --- | --- | --- | --- |
| round-top-sketch | `accb21098a31854db21e884d23c1ea55d6082818` | verification | SCPF + 4 reference | pass |
| native-revolve | `e58ed2d624cbf2c698ca6455f093e87961f8735c` | verification | SCPF only | pass |
| circle-negative-extrude | `2a4983d7bab5e476158f41bc6244cf7c7a554cc8` | verification | SCPF + 4 reference | pass |
| bracket | `d396a84caf1f486e148d21fdcf1a3c48c3c587d3` | verification | SCPF + 4 reference | pass |
| hole-family | `5084ee475cb212ea4c3e6bd168b1c294aec7eafb` | verification | SCPF + 4 reference | pass |
| top-sketch-after-chamfer | `b0f2220dac64458d4705495711846474f91622da` | verification | SCPF + 4 reference | pass |
| circular-feature-pattern | `d8edb7e61fa879c44ff350ef81d041b93704cab9` | verification | SCPF + 4 reference | pass |
| rounded-rectangle-sketch | `ff7607a9ab240d2a46140939939e4f573664e4de` | verification | SCPF + 4 reference | pass |
| attached-through-all | `41b9d6366019514c5a84848d19f8b592f9ce07f5` | verification | SCPF only | pass |
| cone-boolean | `a5dea83c89ec0d347a4ced2d14e31b231588762f` | verification | SCPF only | pass |

## Ownership and source contracts

Each model remains one physical owner under `models/<id>/`. SCPF is primary.

The seven multi-engine owners retain exactly the four historical reference implementations: CadQuery, build123d, PythonSCAD and pyBOSL2. `native-revolve`, `attached-through-all` and `cone-boolean` deliberately remain SCPF-only; no synthetic reference implementation or geometry stage was added.

Historical owner-local source/compiler tests are retained. OLD per-engine orchestration wrappers and visual-baseline plumbing were not copied into NEW; the standard NEW builders, verification module and preview module are reused.

All owner-local command-contract tests pass before CAD execution.

## Restored SCPF library contract

The migration exposed one library gap rather than a model defect: NEW had lost the historical public `Sketch.revolve(...)` API even though `native-revolve` legitimately depends on it.

The historical behavior was restored in `cadlib/scpf`, not worked around in the model:
- public `Sketch.revolve(axis=..., angle=..., sym=...)`;
- `sketch_base_revolve` lowering to native `solid.revolve`;
- root and Boolean feature-tree dispatch;
- native history identity `Revolve`;
- angle-parameter classification as degrees rather than millimetres;
- historical revolve unit tests, including Boolean use and invalid-axis/sweep validation.

The final candidate passes the restored cadlib tests and the original `native-revolve` owner tests unchanged apart from the repository path migration.

## Native SolidCraft parity

All **20/20 native SCPF stages pass** in the candidate. The ten new baselines match OLD generated measurements.

### Basic geometry

- **round-top-sketch** — one closed body, bounds `[-50,-50,0] .. [50,50,26]`, volume `102868.30984914419 mm³`; 5 faces (2 cylinder + 3 plane); timeline Disc Sketch/Extrude then Hub Sketch/Extrude.
- **native-revolve** — one closed body, bounds `[0,-4,-4] .. [10,4,4]`, volume `502.654824574367 mm³`; timeline RadialProfile Sketch → RevolveFeature; parameters radius=4 mm, length=10 mm and sweep expression 360 deg.
- **circle-negative-extrude** — one closed body, bounds `[-10,-10,-30] .. [10,10,0]`, volume `9424.777960769381 mm³`; timeline Profile Sketch → ExtrudeFeature.
- **bracket** — one closed body, bounds `[0,-12,-40] .. [40,12,0]`, volume `19584 mm³`; 8 planar faces; width=24 mm, arm_length=40 mm, arm_height=12 mm.

The historical `native-revolve/resize_revolved_solid` saved design also matches OLD exactly: radius=5 mm, sweep expression 180 deg, bounds `[0,0,-5] .. [10,5,5]`, volume `392.69908169872417 mm³`, and the same Sketch → RevolveFeature timeline.

### Parent/child features and faces

- **hole-family** — one closed body, bounds approximately `[-60,-20,0] .. [60,20,12]`, volume `55857.635240586176 mm³`; 67 faces; native timeline Box1 → Hole1 → Hole2 → Hole3 → Hole4.
- **top-sketch-after-chamfer** — one closed body, bounds approximately `[-50,-35,0] .. [50,35,10]`, volume `67589.02664470769 mm³`; timeline Box1 → Chamfer1 → Top hole Sketch → Top hole ExtrudeFeature.
- **circular-feature-pattern** — one closed body, bounds `[-50,-50,0] .. [50,50,6]`, volume `58190.44263153226 mm³`; 12 faces (6 cylinder + 6 plane); pcd=60 mm and bolts=6; timeline ends in CircularPatternFeature.
- **rounded-rectangle-sketch** — one closed body, bounds `[-40,-30,0] .. [40,30,13]`, volume `31828.31853071796 mm³`; 19 faces; Rounded pad and World cut sketches/timeline match OLD.
- **attached-through-all** — one closed body, bounds `[-40,-30,0] .. [40,30,5]`, volume `22399.999999999996 mm³`; 10 planar faces; timeline Box1 → Through cut Sketch → Through cut ExtrudeFeature.
- **cone-boolean** — one closed body, bounds `[-25,-20,0] .. [25,20,26]`, volume `40741.85831691334 mm³`; 12 faces (1 cone + 4 cylinder + 7 plane); timeline Box1 → Fillet1 → Cone1.

The historical `circular-feature-pattern/bolts_4` saved design matches OLD exactly: bolts=4, pcd=60 mm, volume `58793.62842102151 mm³`, 10 faces (4 cylinder + 6 plane), with the same Box → Hole → CircularPattern timeline.

## Replay evidence

Where the historical source requires dynamic topology replay, the candidate retains consumer-owned SCPF replay semantics through `scpf.headless.run_document()`.

New-owner replay evidence includes:
- round-top-sketch: 9 authored commands, 2 phases, attached top-face binding retained;
- top-sketch-after-chamfer: 7 authored commands, 2 phases, post-chamfer face binding retained;
- rounded-rectangle-sketch: 22 authored commands, 2 phases, attached rounded-pad relationship retained;
- attached-through-all: 9 authored commands, 2 phases, attached face binding and native through-all cut retained.

No Forge-specific replay logic was added to central CI or the generic SolidCraft builder.

## Reference geometry

Across the full twenty-owner candidate:
- 16 owners have SCPF + four historical reference implementations;
- 4 owners are intentionally SCPF-only: `rotated-sketch-cutter`, `native-revolve`, `attached-through-all`, `cone-boolean`.

All **80/80 applicable geometry stages pass** in `cad-reference:v0.3.5`. The ten new owners contribute 35 geometry stages: 7 multi-engine owners × 5 implementations. No artificial geometry stage is created for an SCPF-only owner.

## Remaining integration acceptance

The twenty-owner candidate is accepted for integration. Issue #29 is complete only after:

1. PR #30 is made ready and squash-merged to `dev`;
2. post-merge dev CI passes and permanent `build/dev/models` contains all twenty physical owners;
3. Pages publishes exactly three Examples entries and all twenty owners under Verification;
4. the obsolete flattened `/dev/models` Pages route remains absent;
5. a full `dev -> main` promotion passes and is merged with a merge commit;
6. post-merge main CI, build publication, Pages assembly and live deployment all pass.

Do not start the next historical functional group before these checks are complete.
