# Forge NEW design

## Purpose

Forge NEW is a clean consumer of `template.cad.library`, not a second evolution of the historical Forge repository structure.

```text
cadlib/                     public scpf package
examples/                   migrated examples / qualification fixtures
modules/
  ci/                       selection and runtime orchestration
  builder-*                 standard CAD adapters
  verification/             local generic cad_verification
  preview/                  deterministic presentation rendering
  build/                    durable generated-output publication
  pages/                    Hugo projection/publication
site/                       Hugo/Hextra source
docs/                       repository contract and migration record
```

## SCPF boundary

The template role `cadlib` is implemented by the actual `scpf` package. Forge-specific compilation is consumer-owned logic. Generic builders must not learn Forge semantics merely to support SCPF.

For the final SolidCraft path the intended boundary is:

```text
SCPF source/model
      ↓ Forge compiler (cadlib-owned)
SolidCraft command document
      ↓ builder-solidcraft
.sc + STL + native snapshot
      ↓ reference verifier
geometry / evidence
```

Reference implementations use the standard PythonSCAD, pyBOSL2, CadQuery and build123d builders directly.

## Migration comparison

The old repository currently owns package code, a generic CAD-CI integration layer, custom verification scripts and a hand-built site. Forge NEW separates those responsibilities. Before migrating old code, classify it as:

- **SCPF product behavior** → `cadlib/`;
- **model-specific expectation** → the example;
- **generic verification** → `modules/verification/`;
- **generic builder/runtime behavior** → existing standard module;
- **presentation** → Hugo/Pages;
- **obsolete orchestration/duplication** → remove after parity.

## Example rollout

The first migrated example should be a small but genuine Forge/SCPF example with reference implementations and a geometry contract. It must prove:
- SCPF compilation;
- SolidCraft command capture;
- native execution;
- STL verification;
- preview;
- durable build publication;
- Hugo projection.

After that succeeds, expand to five and then ten examples while keeping the same contracts. Do not broaden infrastructure at the same time unless a real migrated example demonstrates the need.
