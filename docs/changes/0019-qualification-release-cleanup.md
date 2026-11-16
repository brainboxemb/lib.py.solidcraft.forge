# Change 0019 — Qualification and release cleanup

**Status:** implementation  
**SolidCraft target:** 0.42.0

## Problem

Forge currently has two sources for some native qualification expectations:

- `qualification/native_validation.py`;
- skipped `*NativeTests` classes inside `qualification/tests/`.

The skipped unittest classes run only when `SCPF_NATIVE_ROOT` is supplied and
repeat expectations already owned by the central native validator. This makes
it unclear which source is authoritative.

One remaining qualification test also hard-codes the old SolidCraft version
`0.30.1`, while the library source of truth is
`scpf.version.TESTED_SOLIDCRAFT_VERSION`.

The release validator checks package/changelog/SolidCraft metadata, but it has
no simple machine-readable way to refuse a release when a foundational Forge
blocker is still open.

## Rules

### One native validation source

Native Q4/Q5 geometry, saved-design mutation and native history expectations
live only in:

```text
qualification/native_validation.py
```

Files in `qualification/tests/` test Forge command/API contracts. They do not
contain a second, conditionally skipped native test suite.

### One SolidCraft version source

Qualification and release code read:

```python
scpf.version.TESTED_SOLIDCRAFT_VERSION
```

No qualification assertion may copy a literal engine version such as
`"0.30.1"` or `"0.42.0"`.

Workflow runtime metadata may still contain the installed version as evidence;
it is compared with the library source of truth.

### Explicit release blockers

`docs/design/release-blockers.txt` is the machine-readable list of
foundational blockers.

Rules:

- blank lines and lines beginning with `#` are comments;
- every other non-empty line is an active blocker;
- the release validator refuses a release while any active blocker exists;
- when there are no foundational blockers, the file contains comments only.

The file contains short normal engineering descriptions, not design prose.

## Test layers

Forge tests are separated by purpose:

1. `scpf/tests/` — Forge object/API/compiler behaviour;
2. `qualification/tests/` — emitted SolidCraft command contract and
   qualification tooling;
3. `qualification/native_validation.py` — Q4/Q5 native SolidCraft evidence.

The same native expectation must not be copied into layer 2.

## Non-goals

- no modelling API change;
- no SolidCraft command change;
- no CAD geometry change;
- no new Q5 claim merely to increase coverage;
- no downstream CAD pin in this change.

## Qualification

This change must prove:

- normal qualification tests run without skipped duplicate native test classes;
- no old hard-coded SolidCraft version remains in qualification assertions;
- central native validation still covers the cases whose duplicate classes were
  removed;
- release validation passes when the blocker file has comments only;
- release validation fails and prints active blocker text when the file contains
  a blocker.

## Exit condition

> Forge has one native validation source, one SolidCraft version source, clear
> test-layer ownership and a release gate that refuses known foundational
> blockers.
