# Forge NEW plan

This file contains unfinished work only.

## Stable baseline

Current stable architecture is `main@cf8bd232065279fad69e711ce46787612fa62ad7`.

It contains:
- the real `scpf` package under `cadlib/src/scpf`;
- package-owner tests separated from model fixtures;
- corrected `models/` physical owner structure;
- five standard template implementations under one owner;
- generic CAD modules/builders/verification/preview/build/Pages;
- durable owner-grouped build output.

The historical Forge repository remains the known-good A/B source.

## Now — #6 historical Forge simple-box

Draft PR #7 migrates the historical Parameterized Box into `models/simple-box/`.

Target owner:
- primary SCPF implementation using local `cadlib/src/scpf`;
- CadQuery, build123d, PythonSCAD and pyBOSL2 historical references;
- historical geometry contract and model documentation;
- package-owned direct native Box lowering assertion;
- no engine-specific sibling owners.

The remaining acceptance item is native saved-design/parameter/timeline verification equivalent to historical `verification/verify.py`. That requires generic staged verification across `solidcraft` and `reference`, owned upstream by `template.cad.library#25`. Do not add a Forge-local scheduler workaround.

After upstream staged verification is qualified, add the native stage to this owner, record explicit OLD vs NEW evidence, then qualify durable build and Hugo projection.

Do not expand to five historical models until #6 is accepted.

## After #6

1. migrate five representative physical models;
2. migrate ten;
3. classify and migrate the remaining graph;
4. migrate API/guides/reference documentation;
5. qualify NEW release/version mechanics;
6. retire duplicated historical orchestration only after parity.
