# 0031 — version-pinned SolidCraft runtime command contracts

Status: **implemented**  
Issue: **#268**  
SolidCraft target: **0.42.0**

## Problem

Forge had a local SolidCraft command catalog, but not a complete, reproducible
snapshot of the command contracts it actually compiles to. A hand-maintained
agent list had already drifted: it still named `joint.origin` while current
Forge no longer emits that command, and it omitted runtime commands that are
still referenced.

Issue #266 exposed the practical consequence. Understanding
`sketch.create` required reopening SolidCraft source even though the runtime
already exposes the command contract through MCP/`engine.describe`.

## Decision

The official pinned SolidCraft runtime registry is now the primary source for
Forge's SolidCraft command API.

`scripts/solidcraft_snapshot.py`:

1. reads `solidcraft-cli commands`;
2. scans the current Forge runtime source for SolidCraft command ids;
3. calls `engine.describe` for every Forge-used command;
4. stores the raw command catalog and command descriptions under the pinned
   SolidCraft version;
5. records typed-contract gaps instead of hiding them;
6. audits the checked-in snapshot against current Forge source without needing
   SolidCraft installed.

A dedicated fast CI workflow regenerates the snapshot from the
checksum-verified official release and compares it byte-for-byte with Git.

## 0.42 result

At the introduction of this change the generated 0.42 snapshot contained 39 Forge-referenced commands. The live count is intentionally derived from Forge source; `runtime/manifest.json` is the current source of truth.

SolidCraft 0.42 supplies typed input/output schemas for 35. Four commands expose
their parameter documentation but no typed schemas:

- `solid.hole`;
- `solid.loft`;
- `solid.pattern.rectangular`;
- `solid.shell`.

These remain explicit gaps in `runtime/manifest.json`.

## Upgrade rule

A future SolidCraft version, for example 0.44, gets a new sibling snapshot
before Forge compatibility work starts. Existing version snapshots are never
overwritten.

This makes command-API changes reviewable independently from Forge compiler
changes.
