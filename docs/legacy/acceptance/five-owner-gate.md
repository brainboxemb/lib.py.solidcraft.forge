# Five-owner migration gate — candidate acceptance

This record compares the historical Forge machine evidence with Forge NEW candidate run **45441165279** at source **5939c926957446b73e3669941acff9b9d44ecc63**. Candidate artifact: **14943616461** (`cad-qualification`).

The historical authority is `brainboxemb/lib.py.solidcraft.forge` generated branch `build`, scope `dev-cad/examples/<id>/`. The OLD items all report `status: pass`.

| Owner | Historical bundle SHA-256 | Purpose | Candidate result |
| --- | --- | --- | --- |
| simple-box | `1246de2f28b541ac655c4911d532bc7a49a7ecf7c52728a7a58a47c6a8f655d6` | example + verification | pass |
| primitive-csg | `19477b9e69c1628ba2f5b5d7933e746a59fa7ce4c566938cec76afd8ebdb462d` | verification | pass |
| anchored-holes | `1f70a10d243d0169fb5763e07caa9ef6dfcf1f3b9ab5eeb2fc46a05115685890` | example + verification | pass |
| assembly-decorator | `0c61c55e46257f152b77b7ca705ae5a8366b510eb0446feff7f57f5d1a6a7173` | verification | pass |
| parametric-attach | `93d2a8ebde7781ff20bfff9779bdfb80cf0b244360d9209d2c5ab8dce5ac7386` | verification | pass |

## Command lowering

The NEW SCPF command documents retain the historical command semantics:

- **primitive-csg** — `solid.sphere(new)`, `solid.box(join)`, native X-axis `solid.cylinder(cut)`, then `solid.box(intersect)`.
- **anchored-holes** — the same version-2 SCPF replay document, including TOP-face `model.faces` bindings, one Hole sketch/cut and one native `solid.pattern.rectangular`.
- **assembly-decorator** — the same version-2 replay structure: one grounded Post component, one native Box and one `occurrence.copy`; no `occurrence.move`.
- **parametric-attach** — the same version-2 replay structure: Base/Block occurrences, native `gap = 10 mm`, symbolic seed move and rigid `joint.create(offset="gap")`.
- **simple-box** — command parity was accepted in the 1-owner gate.

Replay execution is consumer-owned by `builder-scpf` using the existing `scpf.headless.run_document()` semantics. Plain SCPF command documents continue through generic `builder-solidcraft`. Central CI and the generic SolidCraft builder remain unaware of Forge replay semantics.

Candidate replay evidence:
- anchored-holes: 14 authored commands, 2 replay phases, face point/index bindings retained;
- assembly-decorator: 4 authored commands, 1 phase, occurrence bindings retained;
- parametric-attach: 10 authored commands, 2 phases, Base/Block occurrence bindings retained.

## Native SolidCraft parity

All five SCPF `native` verification stages pass in `cad-solidcraft:v0.3.5`.

Observed NEW baseline evidence matches retained OLD machine evidence:

- **primitive-csg** — one body; bounds approximately `[-19.5959179423,-20,0] .. [25,20,20]`; timeline `SphereFeature, BoxFeature, CylinderFeature, BoxFeature`.
- **anchored-holes** — one body; bounds `[0,0,0] .. [100,60,10]`; parameters width=100, depth=60, thickness=10, spacing=40; timeline ends in one `RectangularPatternFeature`.
- **assembly-decorator** — two Post bodies at `[-20,-5,0] .. [-10,5,20]` and `[10,-5,0] .. [20,5,20]`.
- **parametric-attach** — Base `[-20,-15,0] .. [20,15,10]`, Block `[30,-10,0] .. [50,10,10]`, `gap=10 mm`.
- **simple-box** — the previously accepted native Box baseline remains green.

The historical saved-design contract for **parametric-attach** also passes: changing `gap` to `30 mm` keeps Base fixed and moves Block to `[50,-10,0] .. [70,10,10]`, with the native parameter reporting `30 mm`.

## Reference geometry

The candidate selects exactly five physical owners. Each owner has SCPF plus CadQuery, build123d, PythonSCAD and pyBOSL2 implementations.

All **25 geometry stages pass** in `cad-reference:v0.3.5`.

Owner-local command-contract tests also pass for all five owners before CAD execution.

## Integration acceptance

The five-owner gate is complete.

- PR #19 squash-merged to `dev` as `606f07588c8a41ee4f2ae18aef55ff25d1ceb2fc`.
- Post-merge dev CI run `45442571279`: pass.
- Permanent `build/dev/models/` contains all five owners with `source_sha=606f07588c8a41ee4f2ae18aef55ff25d1ceb2fc`.
- Replay evidence is retained for anchored-holes, assembly-decorator and parametric-attach.
- Parametric-attach retains durable `gap_30` saved-design evidence.
- Pages run `45442886388`: pass; platform deployment `45442954257`: pass.
- `gh-pages/dev/models/` publishes exactly the two public owners: `simple-box` and `anchored-holes`. The three verification-only owners are not public.

The next migration gate is issue #21.
