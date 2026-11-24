# Forge NEW plan

This file contains unfinished work only.

## Accepted bootstrap

Current stable bootstrap is `main@2594ff03b5dbae0e558e8ee65ce0a558292add6f`.

It already contains:
- the real `scpf` package under `cadlib/src/scpf`;
- package-owner tests separated from unmigrated model fixtures;
- generic CAD library modules/builders/verification/preview/build/Pages;
- normal branch/merge/release/development guidance.

The historical Forge repository remains the known-good A/B source.

## Now — #11 corrected model-owner template sync

Sync Forge NEW from `template.cad.library@1d9cddfe975d508e2aaa03cb140cbf61e2fdff82`.

Acceptance:
- source root is `models/`, not `examples/`;
- one physical owner expands multiple engine implementations;
- `build.yml` selects models;
- durable `build/<scope>/models/<owner>/` publication works;
- five standard qualification implementations pass under one `simple-box` owner;
- no legacy `build/<scope>/examples/` remains;
- Pages links generated CAD artifacts from `build` and does not duplicate them to `gh-pages`.

## Then — #6 historical Forge simple-box

Rework draft PR #7 onto the accepted owner contract.

The historical Parameterized Box becomes one physical owner. Its SCPF/SolidCraft path and historical reference-engine implementations live inside that owner. Recover:
- example/model-owned command-lowering contract;
- saved-design parameter/timeline verification equivalent to historical `verification/verify.py`;
- explicit OLD vs NEW command/geometry evidence;
- durable build and Hugo evidence.

Do not expand to five historical models until #6 is accepted.

## After #6

1. migrate five representative physical models;
2. migrate ten;
3. classify and migrate the remaining graph;
4. migrate API/guides/reference documentation;
5. qualify NEW release/version mechanics;
6. retire duplicated historical orchestration only after parity.
