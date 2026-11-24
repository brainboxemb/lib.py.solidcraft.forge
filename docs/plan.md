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

The current candidate and permanent dev integration already prove:
- OLD and NEW SCPF command JSON are semantically identical;
- SCPF and all four reference implementations pass the historical geometry contract;
- the candidate uses exactly the existing `solidcraft` and `reference` runtime roles.

Generic staged verification from `template.cad.library#25` is now consumed and the historical native baseline plus `length=50` saved-design mutation match the retained OLD machine evidence. PR #7 is merged to `dev`; durable `build/dev/models/simple-box` is published and Pages deployment succeeded. The final #6 acceptance item is #14: expose the retained `native` and `geometry` stages explicitly on the model page, then close #6.

Do not expand to five historical models until #6 is accepted.

## After #6

1. migrate five representative physical models;
2. migrate ten;
3. classify and migrate the remaining graph;
4. migrate API/guides/reference documentation;
5. qualify NEW release/version mechanics;
6. retire duplicated historical orchestration only after parity.
