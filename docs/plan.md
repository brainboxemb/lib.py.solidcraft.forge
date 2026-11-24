# Forge NEW plan

This file is the source of truth for unfinished work in `lib.py.solidcraft.forge.NEW`.

## Baseline

- template architecture: `template.cad.library@f73c3e76066b16751d4bd1eb7f1c221e0f3fc3fe`;
- old Forge is the known-good A/B source;
- SCPF source baseline: released 0.15.0 package;
- runtimes: `docker.cad.solidcraft v0.3.5` / SolidCraft 0.48.1.

## Now — bootstrap

Issue #1.

- install the complete technical template baseline;
- migrate the real `scpf` source to `cadlib/src/scpf`;
- migrate package-focused unit tests;
- establish AGENTS, requirements, design, manual, plan and handoff;
- qualify the repository on a temporary branch;
- merge bootstrap to `dev`, then promote a full-green `dev` to `main`.

The historical Forge repository remains unchanged.

## Next — first real example

Create a separate issue after bootstrap. Select one small genuine Forge example from the old repository and migrate it end-to-end. Keep the old build authoritative and compare:
- SCPF source semantics;
- generated SolidCraft command JSON;
- native SolidCraft output;
- STL geometry;
- verification result/evidence;
- preview;
- Hugo example page.

Do not migrate five examples until the one-example slice is accepted.

## Then

1. migrate five representative examples;
2. migrate ten examples;
3. classify and migrate the remaining graph;
4. migrate API/guide/reference content into Hugo/Hextra;
5. add release/version behavior after package and CAD parity;
6. retire duplicated old Forge CI/site/scripts only after equivalent NEW behavior is stable;
7. only then plan retirement of the old repository/external verification ownership.

## Explicit non-goals for bootstrap

- no new Forge API;
- no runtime upgrade;
- no release;
- no mass example migration;
- no edits to old Forge;
- no attempt to preserve historical CI directory layout.
