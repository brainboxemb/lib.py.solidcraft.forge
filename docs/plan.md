# Forge NEW plan

This file is the source of truth for unfinished work in `lib.py.solidcraft.forge.NEW`.

## Accepted baseline

Bootstrap is accepted on stable `main` at:

`a556e0c20420ac59e0efecd3e9455eb6bd43ffbb`

Qualification:
- full main CI run `45422240513`: success;
- Pages run `45422613383`: success;
- SCPF package-owner suite: 145 tests in the promotion baseline;
- five standard template CAD qualification examples: pass;
- runtimes: `docker.cad.solidcraft v0.3.5` / SolidCraft 0.48.1.

The public package/import name is `scpf`. The historical Forge repository remains the known-good A/B source.

## Now — #6 historical simple-box

Migrate one real Forge example end-to-end before expanding the graph.

Current draft PR #7 adds:
- Forge-specific `builder-scpf`;
- historical Parameterized Box SCPF source and metadata;
- exact historical four reference-engine sources;
- SCPF -> generic SolidCraft builder composition;
- reference-runtime STL verification.

Still required before accepting #6:
- example-owned command-lowering test;
- saved-design parameter/timeline verification equivalent to old `verification/verify.py`;
- explicit OLD vs NEW command/geometry comparison;
- durable build and Hugo evidence from the completed candidate.

Do not expand to five examples before #6 is accepted.

## Then

1. migrate five representative Forge examples;
2. migrate ten examples;
3. classify and migrate the remaining graph;
4. migrate API/guides/reference documentation to Hugo/Hextra;
5. qualify release/version mechanics in NEW;
6. retire duplicated historical CI/site/scripts only after equivalent behavior is stable;
7. only then consider retirement of old repository/external verification ownership.

## Deferred historical tests

See `docs/migration-tests.md`. Deferred tests are ownership work, not discarded coverage.
